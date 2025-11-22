from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import logging

import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'tick_sightings.db'
MODEL_PATH = "tick_forecast_model.pkl"


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Tick Sightings API is running',
        'endpoints': [
            '/api/sightings',
            '/api/sightings/search',
            '/api/stats/regions',
            '/api/stats/trends',
            '/api/stats/species',
            '/api/risk/assessment',
            '/api/patterns/seasonal',
            '/api/forecast/trends',
            '/api/risk/scoring'
        ]
    })


@app.route('/api/sightings', methods=['GET'])
def get_sightings():
   # Get all sightings with optional pagination
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM sightings')
        total = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT * FROM sightings 
            ORDER BY date DESC, time DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        sightings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': sightings,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching sightings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sightings/search', methods=['GET'])
def search_sightings():
    # Search and filter sightings
    try:
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        location = request.args.get('location', '')
        species = request.args.get('species', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM sightings WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        if location:
            query += ' AND location = ?'
            params.append(location)
        
        if species:
            query += ' AND species = ?'
            params.append(species)
        
        query += ' ORDER BY date DESC, time DESC LIMIT 500'
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"Error searching sightings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats/regions', methods=['GET'])
def get_region_stats():
    # Get total number of tick sightings per location
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT location, COUNT(*) as count, COUNT(DISTINCT species) as species_count
            FROM sightings
            GROUP BY location
            ORDER BY count DESC
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Error fetching region stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats/trends', methods=['GET'])
def get_trends():
    # Get monthly and weekly trends depending on selection
    try:
        period = request.args.get('period', 'monthly')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if period == 'weekly':
            cursor.execute('''
                SELECT strftime('%Y-W%W', date) as period, COUNT(*) as count
                FROM sightings
                WHERE date != ''
                GROUP BY period
                ORDER BY period DESC
                LIMIT 52
            ''')
        else:
            cursor.execute('''
                SELECT strftime('%Y-%m', date) as period, COUNT(*) as count
                FROM sightings
                WHERE date != ''
                GROUP BY period
                ORDER BY period DESC
                LIMIT 24
            ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'period': period
        })
    
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats/species', methods=['GET'])
def get_species_stats():
    # Get statistics by species of Ticks
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT species, COUNT(*) as count, COUNT(DISTINCT location) as locations
            FROM sightings
            GROUP BY species
            ORDER BY count DESC
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Error fetching species stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/risk/assessment', methods=['GET'])
def get_risk_assessment():
    # Calculate the risk scores by each location
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the most recent date in the database (2024-12-30 based on the current data).
        cursor.execute("SELECT MAX(date) as max_date FROM sightings WHERE date != ''")
        max_date_row = cursor.fetchone()
        max_date = max_date_row['max_date'] if max_date_row else None
        
        if not max_date:
            return jsonify({'success': False, 'error': 'No valid dates in database'}), 400
        
        # Calculate 3 months (90 days) before the latest date
        latest_date = datetime.strptime(max_date, '%Y-%m-%dT%H:%M:%S')
        three_months_ago = (latest_date - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%S')
        
        # Fetch total sightings, last sighting, and recent 3-month sightings
        cursor.execute('''
            SELECT location, 
                       COUNT(*) as total_sightings,
                       MAX(date) as last_sighting,
                       COUNT(CASE WHEN date >= ? THEN 1 END) as recent_sightings
            FROM sightings
            WHERE date != ''
            GROUP BY location
        ''', (three_months_ago,))
        
        rows = cursor.fetchall()
        if not rows:
            return jsonify({'success': False, 'error': 'No sightings available'}), 400
        
        # Convert rows into dicts
        results_raw = [dict(row) for row in rows]

        # --- Dynamic ranges for normalization ---
        totals = [r['total_sightings'] for r in results_raw]
        recents = [r['recent_sightings'] for r in results_raw]

        min_total = min(totals)
        max_total = max(totals)
        max_recent = max(recents) if max(recents) > 0 else 1  # avoid division by zero

        # Prepare final results with risk scoring
        results = []
        for r in results_raw:
            total = r['total_sightings']
            recent = r['recent_sightings']

            # --- Normalized values (0–1) ---
            T_norm = (total - min_total) / (max_total - min_total) if max_total > min_total else 0 # total sightings normalization
            R_norm = recent / max_recent if max_recent > 0 else 0 # recent sightings normalization

            # --- Weighted risk score (0–100) ---
            risk_score = (T_norm * 0.6 + R_norm * 0.4) * 100
            risk_score = round(min(100, max(0, risk_score)), 1)

            # Risk classification
            if risk_score >= 70:
                risk_level = 'HIGH'
                color = 'red'
            elif risk_score >= 40:
                risk_level = 'MEDIUM'
                color = 'yellow'
            else:
                risk_level = 'LOW'
                color = 'green'

            results.append({
                'location': r['location'],
                'total_sightings': total,
                'recent_sightings': recent,
                'last_sighting': r['last_sighting'],
                'risk_score': risk_score,
                'risk_level': risk_level,
                'color': color
            })
        
        conn.close()
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': results,
            'reference_date': max_date,
            'three_month_window': f'{three_months_ago} to {max_date}'
        })
    
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/patterns/seasonal', methods=['GET'])
def seasonal_patterns():
    # Analyze seasonal patterns by species to see peak months for each sighting species
    # All the years data is aggregated here
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT species, month, COUNT(*) as count
            FROM sightings
            WHERE month != '' AND species != ''
            GROUP BY species, month
            ORDER BY species, count DESC
        ''')
        
        species_data = {}
        for row in cursor.fetchall():
            r = dict(row)
            if r['species'] not in species_data:
                species_data[r['species']] = []
            species_data[r['species']].append({'month': r['month'], 'count': r['count']})
        
        results = []
        for species, months in species_data.items():
            sorted_months = sorted(months, key=lambda x: x['count'], reverse=True)
            results.append({
                'species': species,
                'peak_month': sorted_months[0]['month'] if sorted_months else 'Unknown',
                'peak_count': sorted_months[0]['count'] if sorted_months else 0,
                'monthly_data': sorted_months[:3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Error in seasonal analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/forecast/trends', methods=['GET'])
def forecast_trends():
    try:
        # Load pretrained model + metadata
        saved = joblib.load(MODEL_PATH)
        model = saved["model"]
        data_len = saved["data_len"]
        last_year = int(saved["last_year"])
        last_month = int(saved["last_month"])

        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']

        predictions = []

        for i in range(1, 4):
            idx = data_len - 1 + i
            pred_count = model.predict(np.array([[idx]]))[0]

            next_month = ((last_month + i - 1) % 12) + 1
            next_year = last_year + ((last_month + i - 1) // 12)

            predictions.append({
                'month': month_names[next_month],
                'year': next_year,
                'predicted_count': round(max(pred_count, 0))
            })

        # Trend (slope near end)
        tail = np.array([[data_len - 2], [data_len - 1]])
        y_tail = model.predict(tail)
        slope = y_tail[1] - y_tail[0]
        trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"

        return jsonify({
            'success': True,
            'predictions': predictions,
            'trend': trend,
            'slope': round(float(slope), 2),
        })

    except Exception as e:
        logger.error(f"Error in forecasting: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/risk/scoring', methods=['GET'])
def get_risk_scoring():
    """Calculate predictive risk scores with color coding"""
    try:
        danger_level = request.args.get('danger_level', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                location,
                COUNT(*) as total_sightings,
                COUNT(CASE WHEN date >= date('now', '-7 days') THEN 1 END) as recent_7d,
                COUNT(CASE WHEN date >= date('now', '-30 days') THEN 1 END) as recent_30d,
                MAX(date) as last_sighting,COUNT(DISTINCT species) as species_count
            FROM sightings
            WHERE date != ''
            GROUP BY location
        ''')
        
        results = []
        for row in cursor.fetchall():
            r = dict(row)
            
            # Calculate recency factor
            last_date = r['last_sighting']
            if last_date:
                days_ago = (datetime.now() - datetime.strptime(last_date, '%Y-%m-%dT')).days
                recency = max(0, 30 - days_ago) / 30
            else:
                recency = 0
            
            # Risk score formula
            population = 10000
            risk_score = (r['total_sightings'] * recency) / population * 1000
            risk_score += r['recent_7d'] * 0.5
            
            # Danger level
            if risk_score >= 5:
                danger = 'HIGH'
                color = 'red'
            elif risk_score >= 2:
                danger = 'MEDIUM'
                color = 'yellow'
            else:
                danger = 'LOW'
                color = 'green'
            
            result = {
                'location': r['location'],
                'total_sightings': r['total_sightings'],
                'recent_7d': r['recent_7d'],
                'recent_30d': r['recent_30d'],
                'species_count': r['species_count'],
                'last_sighting': last_date,
                'risk_score': round(risk_score, 2),
                'danger_level': danger,
                'color': color
            }
            
            if danger_level == '' or danger_level == color:
                results.append(result)
        
        conn.close()
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': results,
            'filter': danger_level if danger_level else 'all'
        })
    
    except Exception as e:
        logger.error(f"Error in risk scoring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8432)
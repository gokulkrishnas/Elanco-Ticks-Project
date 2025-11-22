import sqlite3
import requests
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickDatabase:
    def __init__(self, db_name='tick_sightings.db'):
        self.db_name = db_name
        self.setup_database()
    
    def setup_database(self):
        """Create the database schema"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create sightings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,
                date TEXT,
                time TEXT,
                location TEXT,
                species TEXT,
                year TEXT,
                month TEXT,
                latinName TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON sightings(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_location ON sightings(location)')
        
        conn.commit()
        conn.close()
        logger.info("Database setup complete")
    
    def insert_sighting(self, sighting_data):
        """Insert a single sighting, skip if duplicate"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO sightings 
                (external_id, date, time, location, species, year, month, latinName)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sighting_data.get('id'),
                sighting_data.get('date'),
                sighting_data.get('time'),
                sighting_data.get('location'),
                sighting_data.get('species'),
                sighting_data.get('year'),
                sighting_data.get('month'),
                sighting_data.get('latinName')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate entry, skip
            return False
        finally:
            conn.close()


class DataIngestion:
    def __init__(self, api_url='https://dev-task.elancoapps.com/data/tick-sightings'):
        self.api_url = api_url
        self.db = TickDatabase()
    
    def fetch_data(self):
        """Fetch data from API with error handling"""
        try:
            logger.info(f"Fetching data from {self.api_url}")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched data")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            return None
    
    def clean_data(self, raw_data):
        """Clean and validate data"""
        if not raw_data:
            return []
        
        cleaned = []
        
        # Handle if data is a list or dict with a key
        if isinstance(raw_data, dict):
            # Try common keys
            for key in ['data', 'sightings', 'results']:
                if key in raw_data:
                    raw_data = raw_data[key]
                    break
        
        if not isinstance(raw_data, list):
            raw_data = [raw_data]
        
        for item in raw_data:
            # Skip if missing critical fields
            if not item.get('id'):
                continue
            
            # Extract year and month from date
            date_str = item.get('date', '')
            year = ''
            month = ''
            time = ''
            
            if date_str:
                try:
                    # Try to parse date (assumes YYYY-MM-DD format)
                    date_parts = date_str.split('-')
                    if len(date_parts) >= 2:
                        year = date_parts[0]
                        month_num = date_parts[1]
                        time = date_str.split('T')[1] if 'T' in date_str else ''
                        
                        # Convert month number to month name
                        month_names = {
                            '01': 'January', '02': 'February', '03': 'March',
                            '04': 'April', '05': 'May', '06': 'June',
                            '07': 'July', '08': 'August', '09': 'September',
                            '10': 'October', '11': 'November', '12': 'December'
                        }
                        month = month_names.get(month_num, '')
                except:
                    pass
            
            # Clean and normalize data
            cleaned_item = {
                'id': str(item.get('id', '')),
                'date': date_str,
                'time': time,
                'location': item.get('location', 'Unknown'),
                'species': item.get('species', 'Unknown'),
                'year': year,
                'month': month,
                'latinName': item.get('latinName', '')
            }
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def process_and_store(self):
        """Main processing pipeline"""
        logger.info("Starting data ingestion process")
        
        # Fetch data
        raw_data = self.fetch_data()
        if not raw_data:
            logger.error("Failed to fetch data")
            return
        
        # Clean data
        cleaned_data = self.clean_data(raw_data)
        logger.info(f"Cleaned {len(cleaned_data)} records")
        
        # Store in database
        inserted = 0
        duplicates = 0
        
        for sighting in cleaned_data:
            if self.db.insert_sighting(sighting):
                inserted += 1
            else:
                duplicates += 1
        
        logger.info(f"Inserted: {inserted}, Duplicates skipped: {duplicates}")
        logger.info("Data ingestion complete")


if __name__ == '__main__':
    # Run the ingestion
    ingestion = DataIngestion()
    ingestion.process_and_store()
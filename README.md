# Tick Sightings Analytics – Backend & Dashboard
### -Gokulkrishna S
A backend + frontend MVP for analysing UK tick sightings data. Built for the Elanco Placement Technical Task.

---

## Overview
This project provides a backend service and a simple dashboard interface for visualising and analysing tick sightings across the UK. It includes:

- Data ingestion and cleaning  
- Search & filtering  
- Regional and species-based analytics  
- Weekly/monthly trend analysis  
- Seasonal pattern extraction  
- Risk assessment  
- Machine learning forecasting (Linear Regression) 
- A simple frontend dashboard that interacts with all backend endpoints to display the output

---

## Tech Stack Used

### **Backend**
- Python  
- Flask (REST API)  
- NumPy  
- Scikit-learn (Polynomial Regression model)  
- Joblib (model saving/loading)

### **Frontend**
- HTML  
- CSS  
- JavaScript (Fetch API calls)

---

## Project Structure
```
api-backend.py         # Main Flask API  
data-handling.py       # Data processing, filtering & analytics  
model-training.py      # ML forecasting logic  
requirements.txt       # Python dependencies  
index.html             # Dashboard UI  
style.css              # UI styling  
main.js                # Fetch calls to backend  
```

---

## API Features

### 1. Health Check  
Ensures backend server is up and running.

### 2. Search & Filtering  
Filter sightings by:
- Date range  
- Location  
- Species  

### 3. Data Reporting  
- Sightings by region  
- Species distribution  
- Weekly or monthly trends  
- Seasonal patterns  

### 4. Risk Assessment  
Identifies high-risk areas based on sighting density & frequency and colour codes them.

### 5. Forecasting (ML)  
Predicts the next 3 months of sightings using a simple polynomial regression model.

---

## Running the Project

### 1. Install dependencies
```
pip install -r requirements.txt
```
### 2. Load the data to database
```
python data-handling.py
```
### 3. Create a pipeline for forecast model
```
python model-training.py
```

### 4. Start the backend
```
python api-backend.py
```

Backend defaults to:
```
http://localhost:8432/
```

### 5. Open the frontend
Open **index.html** directly in your browser.

---

## Hosting Note  
The backend can be deployed on an AWS EC2 instance, and the frontend can consume it simply by updating the `API_BASE` URL inside `main.js`.

---

## Additional Documentation
See the separate *Documentation* file for details on:
- Architecture choices
- Data consumption & processing flow
- What could be improved with more time

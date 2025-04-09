from flask import Flask, jsonify
import pandas as pd
from datetime import datetime

from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['ev_data']
metrics_collection = db['vehicle_metrics']
metrics_catalog_collection = db['metrics_catalog']

VEHICLES = {
    "ioniq5": {
        "make": "Hyundai",
        "model": "Ioniq 5",
        "year": "",
        "mf4_file": "mf4_files/hyundai-ioniq5.mf4",
        "dbc_protocol": "hyundai-kia-uds"  # This links to the DBC file
    },
    "renault": {
        "make": "Renault",
        "model": "Zoe",
        "year": "",
        "mf4_file": "mf4_files/renault.mf4",
        "dbc_protocol": "renault-zoe"  
    }
}

@app.route('/api/process/<vehicle_id>', methods=['POST'])
def process_vehicle_data(vehicle_id):
    try:
        vehicle_info = {"make": "Hyundai", "model": "Ioniq 5"}  # Hardcoded for now
        csv_path = "C:/Users/Instruktor.P-02462/Desktop/mf42csv/out/hyundai-ioniq5-decoded-101.csv"        
        print(f"Loading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("DataFrame is empty!")
            return jsonify({"error": "No data found in CSV file"}), 404

        print("DataFrame columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict())
        
        first_row = df.iloc[0]
        timestamp = datetime.now()
        
        all_metrics = {}
        metrics_catalog = {}
        
        for column in df.columns:
            if column.lower() not in ["t", "timestamp"]:  # Keep 't' in df, just don’t metric-ize it
                print(f"Processing column: {column}")
                # Process all rows, not just first_row
                values = df[column].dropna().astype(float).tolist()  # Drop NaNs, convert to float
                if not values:
                    print(f"  Skipping {column}: No valid data")
                    continue
                unit = ""  # Infer from DBC if needed, e.g., "%" for SOC
                categories = []
                if any(kw in column.lower() for kw in ["battery", "soc", "charge", "bms"]):
                    categories.append("battery")
                if not categories:
                    categories.append("other")
                
                all_metrics[column] = {
                    "values": values,  # List of values over time
                    "times": df["t"].iloc[df[column].notna()].tolist(),  # Matching timestamps
                    "unit": unit,
                    "categories": categories
                }
                metrics_catalog[column] = {
                    "unit": unit,
                    "categories": categories,
                    "last_seen": timestamp
                }
        
        print(f"Metrics processed: {len(all_metrics)}")
        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "timestamp": timestamp.isoformat(),
            "metrics": all_metrics  # Full time series data        
        })

    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return jsonify({"error": f"Failed to process: {str(e)}"}), 500
    
    # Add this to run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
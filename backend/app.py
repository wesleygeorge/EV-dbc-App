from asammdf import MDF
import os
from flask import Flask, jsonify, request
from pymongo import MongoClient
import datetime

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['ev_data']
metrics_collection = db['vehicle_metrics']
metrics_catalog_collection = db['metrics_catalog']

# Define your DBC and MF4 file mappings
DBC_FILES = {
    "hyundai-kia": "dbc_files/can1-hyundai-kia-uds-v2.4.dbc",
    # Add more vehicles as needed
}

MF4_FILES = {
    "hyandai": "mf4_files/hyandai-ioniq5.mf4",
    # Add more vehicles as needed
}

@app.route("/api/process/<vehicle>", methods=["POST"])
def process_vehicle_data(vehicle):
    """Process and store all metrics from vehicle MF4 file"""
    if vehicle not in DBC_FILES or vehicle not in MF4_FILES:
        return jsonify({"error": "Invalid vehicle"}), 400

    dbc_path = os.path.join(os.path.dirname(__file__), DBC_FILES[vehicle])
    mf4_path = os.path.join(os.path.dirname(__file__), MF4_FILES[vehicle])

    if not os.path.exists(dbc_path):
        return jsonify({"error": f"DBC file not found: {dbc_path}"}), 404
    if not os.path.exists(mf4_path):
        return jsonify({"error": f"MF4 file not found: {mf4_path}"}), 404

    try:
        print(f"Loading MF4 file: {mf4_path}")
        mdf = MDF(mf4_path)
        
        print(f"Decoding using DBC file: {dbc_path}")
        mdf_decoded = mdf.extract_can_logging(dbc_path)
        
        print("Converting to dataframe")
        df = mdf_decoded.to_dataframe()
        
        if df.empty:
            return jsonify({"error": "No data found in MF4 file"}), 404

        first_row = df.iloc[0]
        timestamp = datetime.datetime.now()
        
        # Process all metrics with categories
        all_metrics = {}
        metrics_catalog = {}
        
        for column in df.columns:
            if column.lower() not in ["time", "timestamp"]:  # Skip time columns
                signal = mdf_decoded.get(column)
                if signal and len(signal.samples) > 0:
                    try:
                        value = float(first_row[column])
                        unit = signal.unit or ""
                        
                        # Categorize the metric based on name
                        categories = []
                        
                        # Battery related
                        if any(kw in column.lower() for kw in ["battery", "soc", "charge", "bms"]):
                            categories.append("battery")
                            
                        # Drivetrain related
                        if any(kw in column.lower() for kw in ["motor", "drive", "power", "torque", "rpm"]):
                            categories.append("drivetrain")
                            
                        # Temperature related
                        if any(kw in column.lower() for kw in ["temp", "temperature", "thermal"]):
                            categories.append("temperature")
                            
                        # Electrical system
                        if any(kw in column.lower() for kw in ["volt", "current", "amp", "electric"]):
                            categories.append("electrical")
                            
                        # Vehicle status
                        if any(kw in column.lower() for kw in ["speed", "velocity", "accel", "brake", "steer"]):
                            categories.append("vehicle_status")
                            
                        # HVAC system
                        if any(kw in column.lower() for kw in ["hvac", "ac", "heat", "cool", "fan"]):
                            categories.append("hvac")
                            
                        # If no category found, use "other"
                        if not categories:
                            categories.append("other")
                            
                        all_metrics[column] = {
                            "value": value,
                            "unit": unit,
                            "categories": categories
                        }
                        
                        # Store in metrics catalog for future reference
                        metrics_catalog[column] = {
                            "unit": unit,
                            "categories": categories,
                            "last_seen": timestamp
                        }
                    except Exception as e:
                        print(f"Error processing column {column}: {str(e)}")
                        # Skip this column and continue
        
        # Store all metrics in MongoDB
        metrics_record = {
            "vehicle": vehicle,
            "metrics": all_metrics,
            "timestamp": timestamp,
            "metrics_count": len(all_metrics)
        }
        
        metrics_collection.insert_one(metrics_record)
        
        # Update metrics catalog with info about available metrics
        for metric_name, metric_info in metrics_catalog.items():
            metrics_catalog_collection.update_one(
                {"vehicle": vehicle, "metric_name": metric_name},
                {"$set": {
                    "vehicle": vehicle,
                    "metric_name": metric_name,
                    "unit": metric_info["unit"],
                    "categories": metric_info["categories"],
                    "last_seen": metric_info["last_seen"]
                }},
                upsert=True
            )
        
        return jsonify({
            "success": True,
            "vehicle": vehicle,
            "timestamp": timestamp.isoformat(),
            "metrics_processed": len(all_metrics)
        })
        
    except Exception as e:
        import traceback
        print(f"Error processing files: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to process: {str(e)}"}), 500

@app.route("/api/metrics/catalog/<vehicle>", methods=["GET"])
def get_metrics_catalog(vehicle):
    """Get the catalog of all available metrics for a vehicle"""
    try:
        catalog = list(metrics_catalog_collection.find(
            {"vehicle": vehicle},
            {"_id": 0}  # Exclude MongoDB _id
        ))
        
        # Group by category for easier frontend consumption
        categories = {}
        for metric in catalog:
            for category in metric["categories"]:
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    "name": metric["metric_name"],
                    "unit": metric["unit"]
                })
        
        return jsonify({
            "vehicle": vehicle,
            "metrics_count": len(catalog),
            "metrics_by_category": categories,
            "all_metrics": catalog
        })
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve metrics catalog: {str(e)}"}), 500

@app.route("/api/metrics/<vehicle>", methods=["GET"])
def get_metrics(vehicle):
    """Get the latest metrics for a vehicle with optional filtering"""
    # Get query parameters for category filtering
    categories = request.args.get("categories", "").split(",") if request.args.get("categories") else []
    metric_names = request.args.get("metrics", "").split(",") if request.args.get("metrics") else []
    
    try:
        # Get the most recent record for this vehicle
        latest_record = metrics_collection.find_one(
            {"vehicle": vehicle},
            sort=[("timestamp", -1)]
        )
        
        if not latest_record:
            return jsonify({"error": "No data found for this vehicle"}), 404
        
        # Filter metrics if requested
        filtered_metrics = {}
        for metric_name, metric_data in latest_record["metrics"].items():
            # Include if explicitly requested by name
            if metric_names and metric_name in metric_names:
                filtered_metrics[metric_name] = metric_data
            # Include if matches requested category
            elif categories and any(cat in metric_data.get("categories", []) for cat in categories):
                filtered_metrics[metric_name] = metric_data
            # Include all if no filters specified
            elif not categories and not metric_names:
                filtered_metrics[metric_name] = metric_data
        
        response = {
            "vehicle": vehicle,
            "timestamp": latest_record["timestamp"].isoformat(),
            "metrics": filtered_metrics,
            "metrics_count": len(filtered_metrics)
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve metrics: {str(e)}"}), 500

@app.route("/api/metrics/<vehicle>/history", methods=["GET"])
def get_metrics_history(vehicle):
    """Get historical data for specific metrics"""
    metric_names = request.args.get("metrics", "").split(",")
    limit = int(request.args.get("limit", 10))  # Default to 10 records
    
    if not metric_names or metric_names[0] == '':
        return jsonify({"error": "Please specify at least one metric"}), 400
    
    try:
        # Get historical records
        history = list(metrics_collection.find(
            {"vehicle": vehicle},
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        # Extract just the requested metrics
        processed_history = []
        for record in history:
            entry = {
                "timestamp": record["timestamp"].isoformat(),
                "metrics": {}
            }
            
            for metric_name in metric_names:
                if metric_name in record["metrics"]:
                    entry["metrics"][metric_name] = record["metrics"][metric_name]
            
            processed_history.append(entry)
        
        return jsonify({
            "vehicle": vehicle,
            "metric_names": metric_names,
            "history": processed_history
        })
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve history: {str(e)}"}), 500

# Add this to run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

# v1
# from asammdf import MDF
# import os
# from flask import Flask, jsonify

# @app.route("/api/metrics/<vehicle>", methods=["GET"])
# def get_metrics(vehicle):
#     if vehicle not in DBC_FILES or vehicle not in MF4_FILES:
#         return jsonify({"error": "Invalid vehicle"}), 400

#     dbc_path = os.path.join(os.path.dirname(__file__), DBC_FILES[vehicle])
#     mf4_path = os.path.join(os.path.dirname(__file__), MF4_FILES[vehicle])

#     if not os.path.exists(dbc_path):
#         return jsonify({"error": "DBC file not found"}), 404
#     if not os.path.exists(mf4_path):
#         return jsonify({"error": "MF4 file not found"}), 404

#     try:
#         mdf = MDF(mf4_path)
#         mdf_decoded = mdf.extract_can_logging(dbc_path)
#         df = mdf_decoded.to_dataframe()
#         if df.empty:
#             return jsonify({"error": "No data found in MF4 file"}), 404

#         first_row = df.iloc[0]
#         metrics = {}
#         for column in df.columns:
#             if column.lower() not in ["time", "timestamp"]:
#                 signal = mdf_decoded.get(column)
#                 if signal and len(signal.samples) > 0:
#                     value = float(first_row[column])
#                     unit = signal.unit or ""
#                     is_ev_specific = any(
#                         keyword in column.lower()
#                         for keyword in [
#                             "battery",
#                             "soc",
#                             "charge",
#                             "motor",
#                             "volt",
#                             "current",
#                             "power",
#                         ]
#                     )
#                     metrics[column] = {
#                         "value": value,
#                         "unit": unit,
#                         "is_ev_specific": is_ev_specific,
#                     }
#         return jsonify({"vehicle": vehicle, "metrics": metrics})
#     except Exception as e:
#         return jsonify({"error": f"Failed to process: {str(e)}"}), 500
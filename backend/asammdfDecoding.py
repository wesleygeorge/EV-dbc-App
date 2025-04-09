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

# Define your DBC files - organized by protocol/manufacturer
DBC_FILES = {
    "hyundai-kia-uds": "dbc_files/can1-hyundai-kia-uds-v2.4.dbc",
    "nissan-leaf-uds": "dbc_files/can1-nissan-leaf-uds-v2.4.dbc",
    "renault-zoe": "dbc_files/can1-renault-zoe.dbc",
    "vw-skoda-audi-uds": "dbc_files/can1-vw-skoda-audi-uds-v2.5.dbc",
    "tesla": "dbc_files/tesla_model_3.dbc",
}

# Define vehicles with their respective MF4 files and which DBC to use
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
    },
    # "ev6": {
    #     "make": "Kia", 
    #     "model": "EV6",
    #     "year": "2022",
    #     "mf4_file": "mf4_files/kia-ev6.mf4",
    #     "dbc_protocol": "hyundai-kia-uds"  # Same DBC file for Kia
    #}
    # Add more vehicles as needed
}

@app.route("/api/vehicles", methods=["GET"])
def list_vehicles():
    """List all available vehicles"""
    result = []
    for vehicle_id, vehicle_info in VEHICLES.items():
        result.append({
            "id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "year": vehicle_info["year"]
        })
    return jsonify({"vehicles": result})

@app.route("/api/process/<vehicle_id>", methods=["POST"])
def process_vehicle_data(vehicle_id):
    if vehicle_id not in VEHICLES:
        return jsonify({"error": f"Invalid vehicle: {vehicle_id}"}), 400
    
    vehicle_info = VEHICLES[vehicle_id]
    dbc_protocol = vehicle_info["dbc_protocol"]
    
    if dbc_protocol not in DBC_FILES:
        return jsonify({"error": f"DBC protocol not found: {dbc_protocol}"}), 400
    
    dbc_path = os.path.join(os.path.dirname(__file__), DBC_FILES[dbc_protocol])
    mf4_path = os.path.join(os.path.dirname(__file__), vehicle_info["mf4_file"])

    if not os.path.exists(dbc_path):
        return jsonify({"error": f"DBC file not found: {dbc_path}"}), 404
    if not os.path.exists(mf4_path):
        return jsonify({"error": f"MF4 file not found: {mf4_path}"}), 404

    try:
        print(f"Loading MF4 file: {mf4_path}")
        mdf = MDF(mf4_path)


        print("Relevant groups with DBC IDs: [21]")  # Hardcoding for now since we know it
        filter_channels = [('Timestamp', 21), ('CAN_DataFrame', 21), ('CAN_DataFrame.BusChannel', 21), ('CAN_DataFrame.ID', 21), ('CAN_DataFrame.IDE', 21), ('CAN_DataFrame.DLC', 21), ('CAN_DataFrame.DataLength', 21), ('CAN_DataFrame.DataBytes', 21), ('CAN_DataFrame.Dir', 21)]
        print(f"Filtering to channels: {filter_channels}")
        mdf_filtered = mdf.filter(filter_channels)
            
        print("Filtered MDF structure:")
        for group_idx, group in enumerate(mdf_filtered.groups):
            print(f"Group {group_idx}:")
            for channel_idx, channel in enumerate(group.channels):
                print(f"  Channel {channel_idx}: {channel.name}")
                if channel.name == "CAN_DataFrame.DataBytes":
                    data_signal = mdf_filtered.get("CAN_DataFrame.DataBytes", group=group_idx)
                    if data_signal and len(data_signal.samples) > 0:
                        print(f"    First few DataBytes: {data_signal.samples[:5]}")
                    else:
                        print("    No DataBytes samples found")
                        
        # # # print("Raw CAN IDs in MF4:") # just for debugging
        # # relevant_groups = []
        # # for group_idx, group in enumerate(mdf.groups):
        # #     try:
        # #         id_channel = mdf.get("CAN_DataFrame.ID", group=group_idx)
        # #         if id_channel and len(id_channel.samples) > 0:
        # #             unique_ids = set(id_channel.samples)
        # #             # print(f"Group {group_idx}: {unique_ids}") # just for debugging
        # #             # Check for DBC IDs: 2028, 1979, 1960
        # #             if any(id in unique_ids for id in [2028, 1979, 1960]):
        # #                 relevant_groups.append(group_idx)
        # #     except Exception as e:
        # #         # print(f"Group {group_idx}: No CAN_DataFrame.ID ({str(e)})") # just for debugging
        # #         continue
        
        # # if not relevant_groups:
        # #     print("No groups found with DBC CAN IDs (2028, 1979, 1960)")
        # #     return jsonify({"error": "No matching CAN data found in MF4 file"}), 404
            
        # print(f"Relevant groups with DBC IDs: {relevant_groups}")
        # # Filter using channel name and group index
        # filter_channels = []
        # for group_idx in relevant_groups:
        #     for channel in mdf.groups[group_idx].channels:
        #         filter_channels.append((channel.name, group_idx))
        # print(f"Filtering to channels: {filter_channels}")
        # mdf_filtered = mdf.filter(filter_channels)

        print(f"Decoding using DBC file: {dbc_path}")
        database_files = {
            "CAN": [(dbc_path, 0)]
        }
        print(f"Database files: {database_files}") # just checking this is right.
        mdf_decoded = mdf_filtered.extract_bus_logging(database_files=database_files)
        
        if mdf_decoded is None:
            print("Decoding failed!")
            return jsonify({"error": "Failed to decode CAN data with the provided DBC file"}), 500
        
        print("Decoded MDF structure:")
        for group_idx, group in enumerate(mdf_decoded.groups):
            print(f"Group {group_idx}:")
            for channel_idx, channel in enumerate(group.channels):
                print(f"  Channel {channel_idx}: {channel.name}")
        
        print("Converting to dataframe")
        df = mdf_decoded.to_dataframe()
        
        if df.empty:
            print("DataFrame is empty!")
            return jsonify({"error": "No data found in MF4 file after decoding"}), 404

        print("DataFrame columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict())
        
        first_row = df.iloc[0]
        timestamp = datetime.datetime.now()
        
        all_metrics = {}
        metrics_catalog = {}
        
        for column in df.columns:
            if column.lower() not in ["time", "timestamp"]:
                base_name = column.split("_")[0]
                if base_name.lower() == "s":
                    print(f"Skipping column: {column}")
                    continue
                print(f"Processing column: {column}")
                signal = mdf_decoded.get(base_name)
                if signal and len(signal.samples) > 0:
                    try:
                        value = float(first_row[column])
                        unit = signal.unit or ""
                        print(f"  Value: {value}, Unit: {unit}")
                        
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
            "vehicle_id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "year": vehicle_info["year"],
            "metrics": all_metrics,
            "timestamp": timestamp,
            "metrics_count": len(all_metrics)
        }
        
        metrics_collection.insert_one(metrics_record)
        
        # Update metrics catalog with info about available metrics
        for metric_name, metric_info in metrics_catalog.items():
            metrics_catalog_collection.update_one(
                {"vehicle_id": vehicle_id, "metric_name": metric_name},
                {"$set": {
                    "vehicle_id": vehicle_id,
                    "make": vehicle_info["make"],
                    "model": vehicle_info["model"],
                    "metric_name": metric_name,
                    "unit": metric_info["unit"],
                    "categories": metric_info["categories"],
                    "last_seen": metric_info["last_seen"]
                }},
                upsert=True
            )
        
        return jsonify({
            "success": True,
            "vehicle_id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "timestamp": timestamp.isoformat(),
            "metrics_processed": len(all_metrics)
        })
        
    except Exception as e:
        import traceback
        print(f"Error processing files: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to process: {str(e)}"}), 500

@app.route("/api/metrics/catalog/<vehicle_id>", methods=["GET"])
def get_metrics_catalog(vehicle_id):
    """Get the catalog of all available metrics for a vehicle"""
    if vehicle_id not in VEHICLES:
        return jsonify({"error": f"Invalid vehicle: {vehicle_id}"}), 400
        
    try:
        catalog = list(metrics_catalog_collection.find(
            {"vehicle_id": vehicle_id},
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
        
        vehicle_info = VEHICLES[vehicle_id]
        return jsonify({
            "vehicle_id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "year": vehicle_info["year"],
            "metrics_count": len(catalog),
            "metrics_by_category": categories,
            "all_metrics": catalog
        })
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve metrics catalog: {str(e)}"}), 500

@app.route("/api/metrics/<vehicle_id>", methods=["GET"])
def get_metrics(vehicle_id):
    """Get the latest metrics for a vehicle with optional filtering"""
    if vehicle_id not in VEHICLES:
        return jsonify({"error": f"Invalid vehicle: {vehicle_id}"}), 400
        
    # Get query parameters for category filtering
    categories = request.args.get("categories", "").split(",") if request.args.get("categories") else []
    metric_names = request.args.get("metrics", "").split(",") if request.args.get("metrics") else []
    
    try:
        # Get the most recent record for this vehicle
        latest_record = metrics_collection.find_one(
            {"vehicle_id": vehicle_id},
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
            "vehicle_id": vehicle_id,
            "make": latest_record["make"],
            "model": latest_record["model"],
            "year": latest_record["year"],
            "timestamp": latest_record["timestamp"].isoformat(),
            "metrics": filtered_metrics,
            "metrics_count": len(filtered_metrics)
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve metrics: {str(e)}"}), 500

@app.route("/api/metrics/<vehicle_id>/history", methods=["GET"])
def get_metrics_history(vehicle_id):
    """Get historical data for specific metrics"""
    if vehicle_id not in VEHICLES:
        return jsonify({"error": f"Invalid vehicle: {vehicle_id}"}), 400
        
    metric_names = request.args.get("metrics", "").split(",")
    limit = int(request.args.get("limit", 10))  # Default to 10 records
    
    if not metric_names or metric_names[0] == '':
        return jsonify({"error": "Please specify at least one metric"}), 400
    
    try:
        # Get historical records
        history = list(metrics_collection.find(
            {"vehicle_id": vehicle_id},
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
        
        vehicle_info = VEHICLES[vehicle_id]
        return jsonify({
            "vehicle_id": vehicle_id,
            "make": vehicle_info["make"],
            "model": vehicle_info["model"],
            "metric_names": metric_names,
            "history": processed_history
        })
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve history: {str(e)}"}), 500

# Add this to run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

# I couldn't get asammdf to install on my Mac. Wheel build failed. Try again on windows.

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
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
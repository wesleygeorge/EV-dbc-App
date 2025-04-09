import os
import subprocess
import pandas as pd
import shutil

def convert_mf4_to_csv(input_folder, dbc_path, output_folder, model_name):
    print(f"Input folder: {input_folder}")
    os.makedirs(output_folder, exist_ok=True)
    temp_folder = os.path.join(output_folder, "temp")  # Temp spot for decoder output
    
    mf4_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".mf4")]
    print(f"Found {len(mf4_files)} MF4 files: {mf4_files}")
    
    if not mf4_files:
        print("No MF4 files found—exiting!")
        return
    
    for idx, mf4_file in enumerate(mf4_files, start=1):
        input_path = os.path.join(input_folder, mf4_file)
        output_csv = os.path.join(output_folder, f"{model_name}-decoded-{idx:03d}.csv")
        os.makedirs(temp_folder, exist_ok=True)
        
        cmd = [
            "mdf2csv_decode.exe",
            "-i", input_path,
            f"--dbc-can1={dbc_path}",
            "-O", temp_folder,
            "--verbosity", "4",
            "--no-append-root"
        ]
        print(f"Converting {mf4_file} to {output_csv}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr or result.returncode != 0:
            print(f"Errors (code {result.returncode}): {result.stderr}")
        
        # Find all CSVs in temp subfolders
        generated_files = []
        for root, _, files in os.walk(temp_folder):
            for f in files:
                if f.endswith(".csv"):
                    signal_group = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(root))))  # e.g., CAN1_Battery_S_M62_R_M101
                    generated_files.append((os.path.join(root, f), signal_group))
        
        if generated_files:
            dfs = []
            for csv_path, signal_group in generated_files:
                df = pd.read_csv(csv_path)
                df["signal_group"] = signal_group.split("CAN1_", 1)[-1] if "CAN1_" in signal_group else signal_group  # Clean up to Battery_S_M62_R_M101
                dfs.append(df)
            
            # Merge all signal groups into one DF
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df.to_csv(output_csv, index=False)
            print(f"Saved combined CSV: {output_csv}")
        
        # Clean up temp folder
        shutil.rmtree(temp_folder, ignore_errors=True)

input_folder = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/input"
dbc_path = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/dbc_files/can1-hyundai-kia-uds-v2.4.dbc"
output_folder = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/output"
model_name = "hyundai-kona"

convert_mf4_to_csv(input_folder, dbc_path, output_folder, model_name)

# import os
# import subprocess

# def convert_mf4_to_csv(input_folder, dbc_path, output_folder, model_name):
#     # Ensure output folder exists
#     os.makedirs(output_folder, exist_ok=True)
    
#     # Find all .mf4 files
#     mf4_files = [f for f in os.listdir(input_folder) if f.endswith(".MF4")]
    
#     for idx, mf4_file in enumerate(mf4_files, start=1):
#         input_path = os.path.join(input_folder, mf4_file)
#         output_csv = os.path.join(output_folder, f"{model_name}-decoded-{idx:03d}.csv")
        
#         # Run mdf2csv_decode
#         cmd = [
#             "mdf2csv_decode.exe",
#             "-i", input_path,
#             f"--dbc-can1={dbc_path}",  # Use = instead of space
#             "-O", output_folder,
#             "--verbosity", "4"
#         ]
#         print(f"Converting {mf4_file} to {output_csv}")
#         result = subprocess.run(cmd, capture_output=True, text=True)
#         print(result.stdout)
#         if result.stderr:
#             print(f"Errors: {result.stderr}")
        
#         # Rename the output file 
#         generated_files = [f for f in os.listdir(output_folder) if f.startswith("hyundai-ioniq5_decoded")]
#         if generated_files:
#             os.rename(
#                 os.path.join(output_folder, generated_files[-1]),
#                 output_csv
#             )

# # Edit paths and model name as needed
# input_folder = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/input"
# dbc_path = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/dbc_files/can1-hyundai-kia-uds-v2.4.dbc"
# output_folder = "C:/Users/Instruktor.P-02462/Coding/evhub/EV-dbc-App/backend/mf42csv/output"
# model_name = "hyundai-kona"

# convert_mf4_to_csv(input_folder, dbc_path, output_folder, model_name)
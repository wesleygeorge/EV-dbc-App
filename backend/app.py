import pandas as pd

# Load the CSV (replace with your file path)
df = pd.read_csv("data/decoded_ev6_data_full.csv")

# Select battery-related columns
battery_columns = [
    "TimeStamp",
    "StateOfChargeBMS",
    "StateOfChargeDisplay",
    "StateOfHealth",
    "BatteryCurrent",
    "BatteryDCVoltage",
    "BatteryAvailableChargePower",
    "BatteryAvailableDischargePower",
    "BatteryMaxTemperature",
    "BatteryMinTemperature",
    "BatteryTemperature1",
    "BatteryTemperature2",
    "BatteryTemperature3",
    "BatteryTemperature4",
    "BatteryTemperature5",
    "BatteryHeaterTemperature1",
    "BatteryVoltageAuxillary",
    "BatteryFanStatus",
    "BatteryFanFeedback",
    "BMSIgnition",
    "BMSMainRelay",
    "CEC_CumulativeEnergyCharged",
    "CED_CumulativeEnergyDischarged",
    "CCC_CumulativeChargeCurrent",
    "CDC_CumulativeDischargeCurrent",
    "Charging",
    "MaxCellVoltage",
    "MaxCellVoltageCellNo",
    "MinCellVoltage",
    "MinCellVoltageCellNo",
    "MinDeterioration",
    "MinDeteriorationCellNo",
    "OperatingTime",
    "OutdoorTemperature",
    "Speed",
    "AccelerationX",
    "AccelerationY",
    "AccelerationZ",
    "Altitude",
]

# Extract a subset (e.g., first 1000 rows, or sample every 10th row for the full dataset)
subset = df[battery_columns].iloc[::40]  # Sample every 10th row to reduce size

# Save to JSON
subset.to_json("battery_data.json", orient="records")

print("Battery data saved to battery_data.json")


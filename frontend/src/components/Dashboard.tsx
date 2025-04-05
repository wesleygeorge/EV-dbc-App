// src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { BatteryData } from '../types/BatteryData';
import LineChart from './LineChart';
import MultiLineChart from './MultiLineChart';

const Dashboard: React.FC = () => {
  const [batteryData, setBatteryData] = useState<BatteryData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching battery data...');
        const response = await fetch('/battery_data.json');
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        setBatteryData(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-6 rounded-lg shadow-md max-w-md">
          <p className="font-semibold">Error: {error}</p>
          <p className="mt-2 text-sm">Please ensure <code>battery_data.json</code> is in the <code>public</code> folder.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10">
      {/* Header */}
      <header className="w-full max-w-6xl mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-gray-800 bg-gradient-to-r from-blue-600 to-teal-500 bg-clip-text text-transparent">
          Electric Vehicle Battery Dashboard
        </h1>
        <p className="mt-2 text-lg text-gray-600">Real insights into your EV's battery performance</p>
      </header>

      {/* Main Content */}
      <main className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-6 px-4">
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="StateOfChargeBMS" 
          title="Battery State of Charge" 
          color="#10B981"
          unit="%"
        />
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="BatteryCurrent" 
          title="Battery Current" 
          color="#3B82F6"
          unit=" A"
        />
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="BatteryDCVoltage" 
          title="Battery Voltage" 
          color="#F59E0B"
          unit=" V"
        />
        <MultiLineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          title="Battery Temperature" 
          series={[
            { key: "BatteryMaxTemperature", name: "Max Temp", color: "#EF4444", unit: "°C" },
            { key: "BatteryMinTemperature", name: "Min Temp", color: "#3B82F6", unit: "°C" }
          ]}
        />
        <MultiLineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          title="Cell Voltage" 
          series={[
            { key: "MaxCellVoltage", name: "Max Cell", color: "#EC4899", unit: " V" },
            { key: "MinCellVoltage", name: "Min Cell", color: "#8B5CF6", unit: " V" }
          ]}
        />
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="StateOfHealth" 
          title="Battery State of Health" 
          color="#14B8A6"
          unit="%"
        />
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="Speed" 
          title="Vehicle Speed" 
          color="#8D5524"
          unit=" km/h"
        />
        <MultiLineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          title="Acceleration" 
          series={[
            { key: "AccelerationX", name: "X-Axis", color: "#EF4444", unit: " m/s²" },
            { key: "AccelerationY", name: "Y-Axis", color: "#10B981", unit: " m/s²" },
            { key: "AccelerationZ", name: "Z-Axis", color: "#3B82F6", unit: " m/s²" }
          ]}
        />
        <LineChart 
          data={batteryData} 
          xKey="TimeStamp" 
          yKey="Altitude" 
          title="Altitude" 
          color="#7C3AED"
          unit=" m"
        />
      </main>

      {/* Footer */}
      <footer className="mt-10 text-gray-500 text-sm">
        <p>Data sampled every 40th row | Powered by xAI</p>
      </footer>
    </div>
  );
};

export default Dashboard;
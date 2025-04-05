// src/components/LineChart.tsx
import React from 'react';
import { 
  ResponsiveContainer, LineChart as RechartsLineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend 
} from 'recharts';

interface LineChartProps {
  data: any[];
  xKey: string;
  yKey: string;
  title: string;
  color?: string;
  unit?: string;
}

const LineChart: React.FC<LineChartProps> = ({ 
  data, xKey, yKey, title, color = "#8884d8", unit = "" 
}) => {
  const formattedData = data.map(item => ({
    ...item,
    formattedTime: new Date(item[xKey]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }));

  return (
    <div className="bg-white p-5 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsLineChart
          data={formattedData}
          margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis 
            dataKey="formattedTime" 
            tick={{ fill: '#6B7280', fontSize: 12 }} 
            stroke="#D1D5DB"
          />
          <YAxis 
            unit={unit} 
            tick={{ fill: '#6B7280', fontSize: 12 }} 
            stroke="#D1D5DB"
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E5E7EB' }}
            formatter={(value: number) => [`${value.toFixed(2)}${unit}`, title]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '14px', color: '#4B5563' }} />
          <Line 
            type="monotone" 
            dataKey={yKey} 
            stroke={color} 
            strokeWidth={2}
            activeDot={{ r: 6, fill: color, stroke: '#fff', strokeWidth: 2 }} 
            name={title}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LineChart;
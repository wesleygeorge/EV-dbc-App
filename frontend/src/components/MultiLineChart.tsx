// src/components/MultiLineChart.tsx
import React from 'react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend 
} from 'recharts';

interface DataSeries {
  key: string;
  name: string;
  color: string;
  unit?: string;
}

interface MultiLineChartProps {
  data: any[];
  xKey: string;
  series: DataSeries[];
  title: string;
}

const MultiLineChart: React.FC<MultiLineChartProps> = ({ data, xKey, series, title }) => {
  const formattedData = data.map(item => ({
    ...item,
    formattedTime: new Date(item[xKey]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }));

  return (
    <div className="bg-white p-5 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
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
            tick={{ fill: '#6B7280', fontSize: 12 }} 
            stroke="#D1D5DB"
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #E5E7EB' }}
            formatter={(value: number, key: string) => {
              const seriesItem = series.find(s => s.key === key);
              return [`${value.toFixed(2)}${seriesItem?.unit || ''}`, seriesItem?.name || key];
            }}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '14px', color: '#4B5563' }} />
          {series.map((s) => (
            <Line 
              key={s.key}
              type="monotone" 
              dataKey={s.key} 
              stroke={s.color}
              strokeWidth={2}
              activeDot={{ r: 6, fill: s.color, stroke: '#fff', strokeWidth: 2 }}
              name={s.name}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MultiLineChart;
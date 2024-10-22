import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function FinancialOverview({ data }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="date" />
      <YAxis />
      <CartesianGrid strokeDasharray="3 3" />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="balance" stroke="#8884d8" />
      <Line type="monotone" dataKey="income" stroke="#82ca9d" />
      <Line type="monotone" dataKey="spending" stroke="#ffc658" />
    </LineChart>
  );
}

export default FinancialOverview;
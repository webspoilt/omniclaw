import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

function CostChart({ costs }) {
    // Transform costs for chart (cumulative sum per day)
    const data = costs.reverse().map((c, idx, arr) => {
        const cumulative = arr.slice(0, idx + 1).reduce((sum, curr) => sum + curr.cost_usd, 0);
        return {
            time: format(new Date(c.timestamp), 'HH:mm'),
            cost: cumulative,
        };
    });

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="cost" stroke="#8884d8" activeDot={{ r: 8 }} />
            </LineChart>
        </ResponsiveContainer>
    );
}

export default CostChart;

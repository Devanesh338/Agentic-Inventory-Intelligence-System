import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

export const OptimizationAnalytics: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Optimization Analytics</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const cost = optimizationResult.cost_summary || {};
  const costData = [
    { name: 'Procurement Cost', value: cost.total_procurement_cost || 0 },
    { name: 'Holding Cost', value: cost.total_holding_cost || 0 },
    { name: 'Stockout Cost', value: cost.total_stockout_cost || 0 },
    { name: 'Transport Cost', value: cost.total_transport_cost || 0 }
  ].filter(d => d.value > 0);

  const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444'];

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Optimization Analytics</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Cost Breakdown</h3>
          <div style={{ height: 300, width: '100%' }}>
            {costData.length > 0 ? (
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={costData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                    {costData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value: any) => `₹${Number(value).toLocaleString()}`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray" style={{ textAlign: 'center', marginTop: '5rem' }}>No cost data available</p>
            )}
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Cost Metrics</h3>
          <ul style={{ listStyle: 'none' }}>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Total Cost</span>
              <span style={{ fontWeight: 'bold' }}>₹{cost.total_cost?.toLocaleString()}</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Budget Used</span>
              <span style={{ fontWeight: 'bold' }}>{cost.budget_utilization_percent?.toFixed(1)}%</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Procurement Cost</span>
              <span style={{ fontWeight: 'bold' }}>₹{cost.total_procurement_cost?.toLocaleString()}</span>
            </li>
            <li style={{ padding: '0.75rem 0', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Holding Cost</span>
              <span style={{ fontWeight: 'bold' }}>₹{cost.total_holding_cost?.toLocaleString()}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

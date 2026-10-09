import React from 'react';
import { useStore } from '../../store/useStore';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

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

  const summary = optimizationResult.summary || {};
  const breakdown = optimizationResult.optimization_analytics?.cost_breakdown || {};
  const cost = optimizationResult.cost_summary || {};

  const procurementCost = breakdown['Procurement'] ?? summary.procurement_cost ?? cost.total_procurement_cost ?? 0;
  const holdingCost = breakdown['Holding'] ?? summary.holding_cost ?? cost.total_holding_cost ?? 0;
  const stockoutCost = breakdown['Stockout'] ?? summary.stockout_cost ?? cost.total_stockout_cost ?? 0;
  const transportCost = breakdown['Transport'] ?? summary.transport_cost ?? cost.total_transport_cost ?? 0;
  const totalCost = summary.total_cost ?? cost.total_cost ?? 0;
  const budgetUtilization = summary.budget_utilization ?? cost.budget_utilization_percent ?? 0;

  const costData = [
    { name: 'Procurement Cost', value: procurementCost },
    { name: 'Holding Cost', value: holdingCost },
    { name: 'Stockout Cost', value: stockoutCost },
    { name: 'Transport Cost', value: transportCost }
  ].filter(d => d.value > 0);

  const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444'];

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Optimization Analytics</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Cost Breakdown</h3>
          <div style={{ height: 320, width: '100%' }}>
            {costData.length > 0 ? (
              <ResponsiveContainer>
                <PieChart>
                  <Pie 
                    data={costData} 
                    dataKey="value" 
                    nameKey="name" 
                    cx="50%" 
                    cy="50%" 
                    outerRadius={90} 
                    label={({ percent }) => (percent && percent > 0.03 ? `${(percent * 100).toFixed(0)}%` : '')}
                  >
                    {costData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value: any) => formatCurrency(Number(value))} />
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
              <span style={{ fontWeight: 'bold' }}>{formatCurrency(totalCost)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Budget Used</span>
              <span style={{ fontWeight: 'bold', color: budgetUtilization > 100 ? 'var(--danger)' : '#16a34a' }}>
                {budgetUtilization.toFixed(1)}%
              </span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Procurement Cost</span>
              <span style={{ fontWeight: 'bold' }}>{formatCurrency(procurementCost)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Holding Cost</span>
              <span style={{ fontWeight: 'bold' }}>{formatCurrency(holdingCost)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Transport Cost</span>
              <span style={{ fontWeight: 'bold' }}>{formatCurrency(transportCost)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-gray">Stockout Cost</span>
              <span style={{ fontWeight: 'bold' }}>{formatCurrency(stockoutCost)}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

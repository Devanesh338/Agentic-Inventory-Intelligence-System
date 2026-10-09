import React from 'react';
import { useStore } from '../../store/useStore';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const DemandInventory: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Demand & Inventory</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const inventorySummary = optimizationResult.inventory_summary || [];

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Demand & Inventory Analytics</h2>
      
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Inventory Status</h3>
        <div style={{ height: 400, width: '100%' }}>
          <ResponsiveContainer>
            <BarChart data={inventorySummary} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="product_id" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="forecast_demand" name="Forecast Demand" fill="var(--brand-primary)" />
              <Bar dataKey="current_stock" name="Current Stock" fill="var(--success)" />
              <Bar dataKey="replenishment_requirement" name="Requirement" fill="var(--warning)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Inventory Details</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Store</th>
                <th>Current Stock</th>
                <th>Forecast Demand</th>
                <th>Projected Stock</th>
                <th>Safety Stock</th>
                <th>Requirement</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {inventorySummary.map((item: any, idx: number) => (
                <tr key={idx}>
                  <td>{item.product_id}</td>
                  <td>{item.store_id}</td>
                  <td>{item.current_stock}</td>
                  <td>{item.forecast_demand}</td>
                  <td style={{ color: item.projected_stock < 0 ? 'var(--danger)' : 'inherit' }}>{item.projected_stock}</td>
                  <td>{item.safety_stock}</td>
                  <td style={{ fontWeight: 'bold' }}>{item.replenishment_requirement}</td>
                  <td>
                    <span className={`badge ${item.risk_level === 'HIGH' ? 'badge-danger' : 'badge-success'}`}>
                      {item.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

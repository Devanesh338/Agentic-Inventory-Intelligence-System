import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

export const SupplierAnalysis: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Supplier Analysis</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  // The backend might not serialize all supplier options, but we can plot the selected ones from procurement_plan
  const plan = optimizationResult.procurement_plan || [];
  
  const scatterData = plan.map((p: any) => ({
    supplier_id: p.supplier_id,
    unit_cost: p.unit_cost,
    reliability: p.supplier_reliability * 100,
    lead_time: p.lead_time_days
  }));

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Supplier Analysis</h2>
      
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Cost vs Reliability (Selected Suppliers)</h3>
        <div style={{ height: 400, width: '100%' }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="unit_cost" type="number" name="Unit Cost" unit="₹" domain={['auto', 'auto']} />
              <YAxis dataKey="reliability" type="number" name="Reliability" unit="%" domain={[0, 100]} />
              <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Suppliers" data={scatterData} fill="var(--brand-primary)" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Supplier Utilization</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Supplier ID</th>
                <th>Product Allocated</th>
                <th>Total Ordered Qty</th>
                <th>Unit Cost</th>
                <th>Lead Time (Days)</th>
                <th>Reliability</th>
              </tr>
            </thead>
            <tbody>
              {plan.map((item: any, idx: number) => (
                <tr key={idx}>
                  <td>{item.supplier_id}</td>
                  <td>{item.product_id}</td>
                  <td style={{ fontWeight: 'bold' }}>{item.quantity}</td>
                  <td>₹{item.unit_cost}</td>
                  <td>{item.lead_time_days}</td>
                  <td>{formatReliability(item.reliability)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

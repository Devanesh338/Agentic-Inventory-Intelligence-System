import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { submitApproval } from '../../api';

export const ProcurementPlan: React.FC = () => {
  const { optimizationResult, requestId, approvalStatus, setApprovalStatus } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Procurement Plan</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const handleDecision = async (decision: 'APPROVE' | 'REJECT') => {
    if (!requestId) return;
    try {
      const data = await submitApproval(requestId, decision, `User ${decision.toLowerCase()}d the plan.`);
      setApprovalStatus(data.status); // Should be APPROVED or REJECTED
    } catch (err) {
      console.error(err);
      alert('Failed to submit decision.');
    }
  };

  const plan = optimizationResult.procurement_plan || [];

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Optimized Procurement Plan</h2>
      
      {/* Approval Banner */}
      <div className="card" style={{ borderLeft: `4px solid ${approvalStatus === 'APPROVED' ? 'var(--success)' : approvalStatus === 'REJECTED' ? 'var(--danger)' : 'var(--warning)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ marginBottom: '0.5rem' }}>Decision Approval</h3>
            <p className="text-gray" style={{ marginBottom: '0.5rem' }}>
              Status: <span style={{ fontWeight: 'bold' }}>{approvalStatus}</span>
            </p>
            <p className="text-gray text-sm">
              Total Cost: {formatCurrency(optimizationResult.summary?.total_cost)} | Budget Utilized: {formatPercentage(optimizationResult.summary?.budget_utilization)}
            </p>
          </div>
          
          {approvalStatus === 'PENDING_APPROVAL' && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => handleDecision('REJECT')} style={{ color: 'var(--danger)', borderColor: 'var(--danger-border)' }}>
                Reject Plan
              </button>
              <button className="btn btn-primary" onClick={() => handleDecision('APPROVE')}>
                Approve Plan
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Plan Table */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Recommended Items ({plan.length})</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Store</th>
                <th>Supplier</th>
                <th>Qty</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Lead Time (Days)</th>
                <th>Reliability</th>
              </tr>
            </thead>
            <tbody>
              {plan.map((item: any, idx: number) => (
                <tr key={idx}>
                  <td>{item.product_id}</td>
                  <td>{item.store_id}</td>
                  <td>{item.supplier_id}</td>
                  <td style={{ fontWeight: 'bold' }}>{item.quantity}</td>
                  <td>{formatCurrency(item.unit_cost)}</td>
                  <td>{formatCurrency(item.total_cost)}</td>
                  <td>{item.lead_time_days}</td>
                  <td>{formatReliability(item.reliability)}</td>
                </tr>
              ))}
              {plan.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2rem' }}>No items recommended.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

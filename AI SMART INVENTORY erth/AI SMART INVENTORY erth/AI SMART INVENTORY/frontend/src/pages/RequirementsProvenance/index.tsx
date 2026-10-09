import React from 'react';
import { useStore } from '../../store/useStore';
import { Settings, Shield } from 'lucide-react';

export const RequirementsProvenance: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Requirements & Provenance</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const reqs = optimizationResult.user_parameters || {};
  const weights = optimizationResult.objective_weights || {};

  const query = optimizationResult.original_user_query || reqs.original_user_request || "No query provided";
  const budget = reqs.budget_limit || reqs.budget || optimizationResult.summary?.budget_limit || 200000;
  const leadTime = reqs.max_lead_time || reqs.max_lead_time_days || 5;
  const serviceLevel = reqs.target_service_level || reqs.min_service_level || 0.95;

  const costWeight = weights.procurement_cost || weights.purchase_cost || weights.cost_weight || 0.35;
  const leadTimeWeight = weights.lead_time || weights.lead_time_weight || 0.15;
  const reliabilityWeight = weights.supplier_reliability || weights.reliability_weight || 0.25;

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Requirements & Provenance</h2>
      
      <div className="card">
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={18} />
          Original Natural Language Request
        </h3>
        <p style={{ fontStyle: 'italic', padding: '1rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
          "{query}"
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings size={18} />
            Parsed Operational Parameters
          </h3>
          <ul style={{ listStyle: 'none' }}>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Budget Limit</span>
              <span style={{ fontWeight: 'bold' }}>₹{Number(budget).toLocaleString()} <span className="badge badge-info" style={{ marginLeft: '0.5rem' }}>User</span></span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Max Lead Time</span>
              <span style={{ fontWeight: 'bold' }}>{leadTime} days <span className="badge badge-info" style={{ marginLeft: '0.5rem' }}>User</span></span>
            </li>
            <li style={{ padding: '0.75rem 0', display: 'flex', justifyContent: 'space-between' }}>
              <span>Target Service Level</span>
              <span style={{ fontWeight: 'bold' }}>{(serviceLevel * 100).toFixed(0)}% <span className="badge badge-info" style={{ marginLeft: '0.5rem' }}>User</span></span>
            </li>
          </ul>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings size={18} />
            Objective Weights (Preferences)
          </h3>
          <ul style={{ listStyle: 'none' }}>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Cost Weight</span>
              <span style={{ fontWeight: 'bold' }}>{costWeight.toFixed(2)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Lead Time Weight</span>
              <span style={{ fontWeight: 'bold' }}>{leadTimeWeight.toFixed(2)}</span>
            </li>
            <li style={{ padding: '0.75rem 0', display: 'flex', justifyContent: 'space-between' }}>
              <span>Reliability Weight</span>
              <span style={{ fontWeight: 'bold' }}>{reliabilityWeight.toFixed(2)}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );

};

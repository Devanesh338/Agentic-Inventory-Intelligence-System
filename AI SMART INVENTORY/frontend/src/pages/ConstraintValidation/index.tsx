import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { CheckCircle, XCircle } from 'lucide-react';

export const ConstraintValidation: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Constraint Validation</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const constraints = optimizationResult.constraint_summary || {};
  const constraintList = [
    { name: 'Budget Constraint', passed: constraints.budget_passed, limit: optimizationResult.user_requirements?.budget, used: optimizationResult.cost_summary?.total_cost },
    { name: 'Lead Time Constraint', passed: constraints.lead_time_passed },
    { name: 'Service Level Constraint', passed: constraints.service_level_passed },
    { name: 'Supplier Capacity Constraint', passed: constraints.capacity_passed },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Constraint Validation</h2>
      
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Global Constraints</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Constraint Type</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {constraintList.map((c, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 500 }}>{c.name}</td>
                  <td>
                    {c.passed === true ? (
                      <span className="badge badge-success" style={{ display: 'inline-flex', gap: '0.25rem' }}><CheckCircle size={14} /> PASS</span>
                    ) : c.passed === false ? (
                      <span className="badge badge-danger" style={{ display: 'inline-flex', gap: '0.25rem' }}><XCircle size={14} /> FAIL</span>
                    ) : (
                      <span className="badge badge-warning">N/A</span>
                    )}
                  </td>
                  <td className="text-gray text-sm">
                    {c.name === 'Budget Constraint' && c.limit ? `Used ₹${c.used?.toLocaleString()} of ₹${c.limit?.toLocaleString()}` : 'Validated internally by MILP Engine.'}
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

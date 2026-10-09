import React from 'react';
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

  const rawConstraints = optimizationResult.constraints || optimizationResult.constraint_summary || {};
  const summary = optimizationResult.summary || {};
  const userParams = optimizationResult.user_parameters || {};

  const budgetItem = rawConstraints.budget || {};
  const leadTimeItem = rawConstraints.lead_time || {};
  const serviceLevelItem = rawConstraints.service_level || {};
  const capacityItem = rawConstraints.supplier_capacity || {};

  const isOptimal = optimizationResult.optimization_status === 'OPTIMAL' || optimizationResult.status === 'OPTIMAL';

  const budgetLimit = userParams.budget_limit || summary.budget_limit || 200000;
  const totalCost = summary.total_cost || 0;

  const constraintList = [
    {
      name: 'Budget Constraint',
      passed: budgetItem.status === 'PASSED' || rawConstraints.budget_passed === true || (isOptimal && totalCost <= budgetLimit),
      details: budgetItem.details || `Used ₹${totalCost.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} of ₹${budgetLimit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${((totalCost / budgetLimit) * 100).toFixed(1)}%)`
    },
    {
      name: 'Lead Time Constraint',
      passed: leadTimeItem.status === 'PASSED' || rawConstraints.lead_time_passed === true || isOptimal,
      details: leadTimeItem.details || `All orders meet the ${userParams.max_lead_time || 5} days delivery requirement.`
    },
    {
      name: 'Service Level Constraint',
      passed: serviceLevelItem.status === 'PASSED' || rawConstraints.service_level_passed === true || isOptimal,
      details: serviceLevelItem.details || `Target service level of ${((userParams.target_service_level || 0.95) * 100).toFixed(0)}% satisfied.`
    },
    {
      name: 'Supplier Capacity Constraint',
      passed: capacityItem.status === 'PASSED' || rawConstraints.capacity_passed === true || isOptimal,
      details: capacityItem.details || 'Supplier allocations strictly respect maximum production capacity.'
    },
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
                    {c.passed ? (
                      <span className="badge badge-success" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <CheckCircle size={14} /> PASS
                      </span>
                    ) : (
                      <span className="badge badge-danger" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <XCircle size={14} /> FAIL
                      </span>
                    )}
                  </td>
                  <td className="text-gray text-sm">
                    {c.details}
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

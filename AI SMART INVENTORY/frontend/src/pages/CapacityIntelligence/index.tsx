import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';

export const CapacityIntelligence: React.FC = () => {
  const { optimizationResult } = useStore();

  if (!optimizationResult) {
    return (
      <div className="card">
        <h2>Capacity Intelligence</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  const capacitySummary = optimizationResult.capacity || {};
  const supplierAllocations = capacitySummary.supplier_allocations || {};

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Capacity Intelligence</h2>
      
      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">System Feasibility</span>
          <span className="kpi-value" style={{ color: capacitySummary.feasibility === 'CAPACITY_SUFFICIENT' ? 'var(--success)' : 'var(--danger)' }}>
            {capacitySummary.feasibility === 'CAPACITY_SUFFICIENT' ? 'FEASIBLE' : capacitySummary.feasibility}
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Global Required Capacity</span>
          <span className="kpi-value">{capacitySummary.global_required_capacity || 0}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Global Available Capacity</span>
          <span className="kpi-value">{capacitySummary.global_available_capacity || 0}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Capacity Utilization</span>
          <span className="kpi-value">
            {capacitySummary.global_available_capacity > 0 
              ? `${((capacitySummary.global_required_capacity / capacitySummary.global_available_capacity) * 100).toFixed(1)}%`
              : '0%'}
          </span>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Supplier Allocation Breakdown</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Supplier ID</th>
                <th>Available Capacity</th>
                <th>Allocated Quantity</th>
                <th>Utilization</th>
                <th>Feasible?</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(supplierAllocations).map(([supplier, details]: [string, any], idx: number) => {
                const util = details.capacity > 0 ? (details.allocated / details.capacity) : 0;
                const isFeasible = details.allocated <= details.capacity;
                return (
                  <tr key={idx}>
                    <td>{supplier}</td>
                    <td>{details.capacity}</td>
                    <td style={{ fontWeight: 'bold' }}>{details.allocated}</td>
                    <td>{formatPercentage(util)}</td>
                    <td>
                      <span className={`badge ${isFeasible ? 'badge-success' : 'badge-danger'}`}>
                        {isFeasible ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

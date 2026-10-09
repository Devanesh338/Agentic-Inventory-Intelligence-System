import React from 'react';
import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { OptimizationPanel } from '../../components/OptimizationPanel';
import { Activity, BarChart, FileText, CheckCircle } from 'lucide-react';

export const ExecutiveOverview: React.FC = () => {
  const { optimizationResult, optimizationStatus } = useStore();

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Executive Overview</h2>
      
      {!optimizationResult ? (
        <OptimizationPanel />
      ) : (
        <div>
          <div className="kpi-grid">
            <div className="kpi-card">
              <span className="kpi-label">Optimization Status</span>
              <span className="kpi-value" style={{ color: 'var(--success)' }}>
                {optimizationResult.status}
              </span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Total Procurement Cost</span>
              <span className="kpi-value">
                {formatCurrency(optimizationResult.summary?.total_cost)}
              </span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Budget Utilization</span>
              <span className="kpi-value">
                {formatPercentage(optimizationResult.summary?.budget_utilization)}
              </span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Service Level Achieved</span>
              <span className="kpi-value">
                {formatPercentage(optimizationResult.summary?.achieved_service_level)}
              </span>
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={18} />
              Summary
            </h3>
            <p>{optimizationResult.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
};

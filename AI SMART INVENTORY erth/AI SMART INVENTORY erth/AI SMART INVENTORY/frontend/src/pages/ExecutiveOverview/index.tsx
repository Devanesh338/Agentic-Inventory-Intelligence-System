import React from 'react';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { useStore } from '../../store/useStore';
import { OptimizationPanel } from '../../components/OptimizationPanel';
import { FileText } from 'lucide-react';

export const ExecutiveOverview: React.FC = () => {
  const { optimizationResult, setOptimizationResult } = useStore();

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Executive Overview</h2>
        {optimizationResult && (
          <button 
            className="btn btn-secondary" 
            onClick={() => setOptimizationResult(null)}
          >
            ← Modify / Run New Optimization
          </button>
        )}
      </div>
      
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
            <p>{typeof optimizationResult.summary === 'string' ? optimizationResult.summary : (optimizationResult.explanation?.summary || 'Optimization completed successfully.')}</p>
          </div>
        </div>
      )}
    </div>
  );
};

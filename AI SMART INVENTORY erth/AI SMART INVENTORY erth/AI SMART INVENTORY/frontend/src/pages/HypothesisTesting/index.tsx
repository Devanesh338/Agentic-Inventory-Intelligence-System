import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { fetchAnalytics } from '../../api';

export const HypothesisTesting: React.FC = () => {
  const { requestId, optimizationResult } = useStore();
  const cachedHypothesis = optimizationResult?.hypothesis_testing?.is_valid != null ? optimizationResult.hypothesis_testing : null;
  const [fetchedData, setFetchedData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const displayData = cachedHypothesis || fetchedData;

  const loadData = React.useCallback(() => {
    if (!requestId) return;
    setLoading(true);
    setError(null);
    fetchAnalytics('hypothesis', requestId)
      .then(res => {
        setFetchedData(res);
        setLoading(false);
      })
      .catch(err => {
        const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
        setError(detail || 'Failed to load hypothesis test');
        setLoading(false);
      });
  }, [requestId]);

  useEffect(() => {
    let ignore = false;
    if (!cachedHypothesis && requestId) {
      Promise.resolve().then(() => {
        if (!ignore) loadData();
      });
    }
    return () => {
      ignore = true;
    };
  }, [requestId, cachedHypothesis, loadData]);

  if (!requestId && !optimizationResult) {
    return (
      <div className="card">
        <h2>Hypothesis Testing</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  if (loading) return <div className="card">Loading hypothesis test...</div>;
  if (error) {
    return (
      <div className="card badge-danger" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{error}</span>
        <button className="btn btn-secondary" style={{ marginLeft: '1rem' }} onClick={loadData}>Retry</button>
      </div>
    );
  }
  if (!displayData) return null;

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Statistical Hypothesis Testing</h2>
      
      {!displayData.is_valid ? (
        <div className="card badge-warning" style={{ padding: '1rem' }}>
          {displayData.message || 'Statistical comparison unavailable.'}
        </div>
      ) : (
        <>
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Hypotheses</h3>
            <div style={{ padding: '1rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
              <p><strong>H0:</strong> {displayData.hypothesis_0}</p>
              <p style={{ marginTop: '0.5rem' }}><strong>H1:</strong> {displayData.hypothesis_1}</p>
            </div>
            
            <div className="kpi-grid" style={{ marginTop: '1.5rem' }}>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Test Used</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{displayData.test_used}</span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Sample Size</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>n={displayData.sample_size}</span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Statistic</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                  {displayData.t_statistic != null ? displayData.t_statistic.toFixed(4) : 'N/A'}
                </span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">P-Value</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                  {displayData.p_value != null ? displayData.p_value.toExponential(4) : 'N/A'}
                </span>
              </div>
            </div>
            
            <div style={{ marginTop: '1.5rem', padding: '1rem', borderLeft: `4px solid ${displayData.decision?.includes('Reject') ? (displayData.decision?.includes('Warning') ? 'var(--warning)' : 'var(--success)') : 'var(--brand-primary)'}` }}>
              <p><strong>Significance Level (Alpha):</strong> {displayData.significance_level}</p>
              <p style={{ marginTop: '0.5rem' }}><strong>Conclusion:</strong> {displayData.decision}. {displayData.interpretation}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

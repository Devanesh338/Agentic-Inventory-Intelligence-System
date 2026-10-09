import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { fetchAnalytics } from '../../api';

export const HypothesisTesting: React.FC = () => {
  const { requestId } = useStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (requestId) {
      setLoading(true);
      fetchAnalytics('hypothesis', requestId)
        .then(res => {
          setData(res);
          setError(null);
        })
        .catch(err => {
          setError(err.message || 'Failed to load hypothesis test');
        })
        .finally(() => setLoading(false));
    }
  }, [requestId]);

  if (!requestId) {
    return (
      <div className="card">
        <h2>Hypothesis Testing</h2>
        <p className="text-gray">No optimization result available. Run an optimization first.</p>
      </div>
    );
  }

  if (loading) return <div className="card">Loading hypothesis test...</div>;
  if (error) return <div className="card badge-danger" style={{ padding: '1rem' }}>{error}</div>;
  if (!data) return null;

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Statistical Hypothesis Testing</h2>
      
      {!data.is_valid ? (
        <div className="card badge-warning" style={{ padding: '1rem' }}>
          {data.message || 'Statistical comparison unavailable.'}
        </div>
      ) : (
        <>
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Hypotheses</h3>
            <div style={{ padding: '1rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
              <p><strong>H0:</strong> {data.hypothesis_0}</p>
              <p style={{ marginTop: '0.5rem' }}><strong>H1:</strong> {data.hypothesis_1}</p>
            </div>
            
            <div className="kpi-grid" style={{ marginTop: '1.5rem' }}>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Test Used</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{data.test_used}</span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Sample Size</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>n={data.sample_size}</span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">Statistic</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                  {data.t_statistic != null ? data.t_statistic.toFixed(4) : 'N/A'}
                </span>
              </div>
              <div className="kpi-card" style={{ padding: '1rem' }}>
                <span className="text-gray text-sm">P-Value</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                  {data.p_value != null ? data.p_value.toExponential(4) : 'N/A'}
                </span>
              </div>
            </div>
            
            <div style={{ marginTop: '1.5rem', padding: '1rem', borderLeft: `4px solid ${data.decision.includes('Reject') ? (data.decision.includes('Warning') ? 'var(--warning)' : 'var(--success)') : 'var(--brand-primary)'}` }}>
              <p><strong>Significance Level (Alpha):</strong> {data.significance_level}</p>
              <p style={{ marginTop: '0.5rem' }}><strong>Conclusion:</strong> {data.decision}. {data.interpretation}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

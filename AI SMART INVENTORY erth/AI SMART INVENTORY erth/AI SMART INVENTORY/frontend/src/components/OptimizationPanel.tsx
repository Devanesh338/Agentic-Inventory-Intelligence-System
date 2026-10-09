import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { uploadDatasets, fetchRegions, runOptimization } from '../api';
import { UploadCloud, Play, MapPin, Search, CheckCircle, Database } from 'lucide-react';

export const OptimizationPanel: React.FC = () => {
  const { 
    ingestionStatus, setIngestionStatus, setIngestionData,
    selectedRegion, setSelectedRegion,
    userQuery, setUserQuery,
    optimizationStatus, setOptimizationStatus, setOptimizationResult,
    setRequestId, setApprovalStatus
  } = useStore();

  const [files, setFiles] = useState<{ sales?: File; inventory?: File; suppliers?: File }>({});
  const [regions, setRegions] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchRegions().then((regionData) => {
      if (regionData && regionData.length > 0) {
        setRegions(regionData);
        useStore.setState((state) => ({
          selectedRegion: state.selectedRegion || regionData[0]
        }));
      }
    }).catch((err) => {
      console.error('Failed to load regions', err);
    });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'sales' | 'inventory' | 'suppliers') => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFiles((prev) => ({ ...prev, [type]: selectedFile }));
    }
  };

  const handleUpload = async () => {
    if (!files.sales && !files.inventory && !files.suppliers) {
      setErrorMsg('Please select at least one CSV file to upload, or proceed directly to Section 2 to use the pre-seeded PostgreSQL database.');
      return;
    }
    setIngestionStatus('loading');
    setErrorMsg(null);
    try {
      const data = await uploadDatasets(files.sales, files.inventory, files.suppliers);
      if (data.status === 'success') {
        setIngestionStatus('success');
        setIngestionData(data.tables);
        const regionData = await fetchRegions();
        if (regionData && regionData.length > 0) {
          setRegions(regionData);
        }
      } else {
        setIngestionStatus('error');
        const errs = data.validation?.errors;
        setErrorMsg(Array.isArray(errs) && errs.length > 0 ? errs.join(', ') : 'Upload validation failed');
      }
    } catch (err: any) {
      setIngestionStatus('error');
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setErrorMsg(detail || 'Server error during dataset upload');
    }
  };

  const handleOptimize = async () => {
    if (!selectedRegion || !userQuery) return;
    setOptimizationStatus('loading');
    setErrorMsg(null);
    try {
      const data = await runOptimization(userQuery, selectedRegion);
      if (data.status === 'ERROR') {
        setOptimizationStatus('error');
        const detail = data.explanation?.rationale || data.explanation?.summary || 'Optimization failed: Infeasible constraints or no data found.';
        setErrorMsg(detail);
      } else {
        setOptimizationStatus('success');
        setOptimizationResult(data);
        setRequestId(data.request_id || data.plan_id);
        setApprovalStatus('PENDING_APPROVAL');
      }
    } catch (err: any) {
      setOptimizationStatus('error');
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setErrorMsg(detail || 'Server error during optimization');
    }
  };

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Play size={20} color="var(--brand-primary)" />
        Run Optimization Pipeline
      </h2>

      {/* Database Status Banner */}
      <div style={{
        margin: '1rem 0',
        padding: '0.75rem 1rem',
        backgroundColor: 'var(--bg-secondary, #f8fafc)',
        border: '1px solid var(--border-light, #e2e8f0)',
        borderRadius: 'var(--radius-md, 6px)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        fontSize: '0.875rem'
      }}>
        <Database size={18} color="var(--brand-primary, #2563eb)" />
        <div>
          <strong>Pre-seeded PostgreSQL Database Ready:</strong> Regional sales, inventory, and supplier records are loaded and available. You can run optimization directly or upload custom CSV datasets below.
        </div>
      </div>

      {/* Upload Section */}
      <div style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
        <h3 className="text-sm">1. Data Ingestion (Optional)</h3>
        <p className="text-xs text-gray" style={{ margin: '0.25rem 0 0.75rem 0' }}>
          Upload new CSV datasets (sales_history.csv, inventory.csv, suppliers.csv) to test custom scenarios. If skipped, the system uses the pre-seeded database.
        </p>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
          <div>
            <label className="label">Sales History (.csv)</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'sales')} className="input" />
            {files.sales && <span style={{ fontSize: '0.75rem', color: '#16a34a', display: 'block', marginTop: '0.25rem' }}>✓ {files.sales.name}</span>}
          </div>
          <div>
            <label className="label">Inventory (.csv)</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'inventory')} className="input" />
            {files.inventory && <span style={{ fontSize: '0.75rem', color: '#16a34a', display: 'block', marginTop: '0.25rem' }}>✓ {files.inventory.name}</span>}
          </div>
          <div>
            <label className="label">Suppliers (.csv)</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'suppliers')} className="input" />
            {files.suppliers && <span style={{ fontSize: '0.75rem', color: '#16a34a', display: 'block', marginTop: '0.25rem' }}>✓ {files.suppliers.name}</span>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
          <button 
            className="btn btn-primary" 
            onClick={handleUpload}
            disabled={ingestionStatus === 'loading'}
          >
            <UploadCloud size={16} style={{ marginRight: '0.5rem' }} />
            {ingestionStatus === 'loading' ? 'Uploading & Ingesting...' : 'Upload & Validate'}
          </button>
          {ingestionStatus === 'success' && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#16a34a', fontSize: '0.875rem' }}>
              <CheckCircle size={16} /> Data successfully ingested into database!
            </span>
          )}
        </div>
      </div>

      {/* Region & Requirements Section */}
      <div style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
        <h3 className="text-sm">2. Configuration</h3>
        
        <div style={{ marginTop: '0.5rem' }}>
          <label className="label">Region</label>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <MapPin size={16} className="text-gray" />
            <select 
              className="input" 
              value={selectedRegion || ''} 
              onChange={(e) => setSelectedRegion(e.target.value)}
            >
              <option value="">-- Select Region --</option>
              {regions.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <label className="label">Natural Language Requirement</label>
          <textarea 
            className="input" 
            rows={3} 
            placeholder="e.g. Optimize replenishment for Chennai-Central with a budget of ₹200000 within 5 days. Maintain at least 95 percent service level. Cost is very important and supplier reliability is also important."
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
          />
        </div>

        <button 
          className="btn btn-primary" 
          style={{ marginTop: '1rem', width: '100%', padding: '0.75rem' }} 
          onClick={handleOptimize}
          disabled={optimizationStatus === 'loading' || !selectedRegion || !userQuery}
        >
          <Search size={16} style={{ marginRight: '0.5rem' }} />
          {optimizationStatus === 'loading' ? 'Running Multi-Agent Optimization...' : 'Run Optimization'}
        </button>
      </div>

      {errorMsg && (
        <div className="badge badge-danger" style={{ display: 'block', padding: '1rem', whiteSpace: 'pre-wrap', marginTop: '1rem' }}>
          {errorMsg}
        </div>
      )}
    </div>
  );
};


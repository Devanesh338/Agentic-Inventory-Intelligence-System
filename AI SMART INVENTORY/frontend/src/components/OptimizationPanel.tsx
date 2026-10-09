import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { uploadDatasets, fetchRegions, runOptimization } from '../api';
import { UploadCloud, Play, MapPin, Search } from 'lucide-react';

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'sales' | 'inventory' | 'suppliers') => {
    if (e.target.files && e.target.files[0]) {
      setFiles({ ...files, [type]: e.target.files[0] });
    }
  };

  const handleUpload = async () => {
    setIngestionStatus('loading');
    setErrorMsg(null);
    try {
      const data = await uploadDatasets(files.sales, files.inventory, files.suppliers);
      if (data.status === 'success') {
        setIngestionStatus('success');
        setIngestionData(data.tables);
        // Load regions
        const regionData = await fetchRegions();
        setRegions(regionData);
      } else {
        setIngestionStatus('error');
        setErrorMsg(data.validation?.errors?.join(', ') || 'Upload failed');
      }
    } catch (err: any) {
      setIngestionStatus('error');
      setErrorMsg(err.message || 'Server error');
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
        setErrorMsg(data.explanation || 'Optimization failed');
      } else {
        setOptimizationStatus('success');
        setOptimizationResult(data);
        setRequestId(data.request_id);
        setApprovalStatus('PENDING_APPROVAL');
      }
    } catch (err: any) {
      setOptimizationStatus('error');
      setErrorMsg(err.message || 'Server error during optimization');
    }
  };

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Play size={20} color="var(--brand-primary)" />
        Run Optimization Pipeline
      </h2>

      {/* Upload Section */}
      <div style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
        <h3 className="text-sm">1. Data Ingestion</h3>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
          <div>
            <label className="label">Sales History</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'sales')} className="input" />
          </div>
          <div>
            <label className="label">Inventory</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'inventory')} className="input" />
          </div>
          <div>
            <label className="label">Suppliers</label>
            <input type="file" accept=".csv" onChange={(e) => handleFileChange(e, 'suppliers')} className="input" />
          </div>
        </div>
        <button 
          className="btn btn-primary" 
          style={{ marginTop: '1rem' }} 
          onClick={handleUpload}
          disabled={ingestionStatus === 'loading'}
        >
          <UploadCloud size={16} style={{ marginRight: '0.5rem' }} />
          {ingestionStatus === 'loading' ? 'Uploading...' : 'Upload & Validate'}
        </button>
      </div>

      {/* Region & Requirements Section */}
      {ingestionStatus === 'success' && (
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
              placeholder="e.g. Optimize replenishment for Chennai-Central with a budget of ₹100000..."
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
      )}

      {errorMsg && (
        <div className="badge badge-danger" style={{ display: 'block', padding: '1rem', whiteSpace: 'pre-wrap' }}>
          {errorMsg}
        </div>
      )}
    </div>
  );
};

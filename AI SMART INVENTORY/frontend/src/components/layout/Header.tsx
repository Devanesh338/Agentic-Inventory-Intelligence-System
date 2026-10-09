import React from 'react';
import { useStore } from '../../store/useStore';

export const Header: React.FC = () => {
  const { selectedRegion } = useStore();

  return (
    <header className="header">
      <div>
        {selectedRegion ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="text-gray">Region:</span>
            <span className="badge badge-info" style={{ fontSize: '0.875rem' }}>{selectedRegion}</span>
          </div>
        ) : (
          <span className="text-gray">No region selected</span>
        )}
      </div>
      <div>
        <span className="badge badge-warning" style={{ marginRight: '1rem' }}>Admin Role</span>
        <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--brand-primary)', color: 'white', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
          OP
        </div>
      </div>
    </header>
  );
};

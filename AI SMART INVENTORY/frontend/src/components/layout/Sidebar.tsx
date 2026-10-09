import React from 'react';
import { NavLink } from 'react-router-dom';
import { useStore } from '../../store/useStore';
import { 
  BarChart3, ShoppingCart, TrendingUp, Users, 
  Settings, CheckSquare, Activity, MessageSquare, 
  HelpCircle, CheckCircle2 
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/executive-overview', label: 'Executive Overview', icon: BarChart3 },
  { path: '/procurement-plan', label: 'Procurement Plan', icon: ShoppingCart },
  { path: '/demand-inventory', label: 'Demand & Inventory', icon: TrendingUp },
  { path: '/supplier-analysis', label: 'Supplier Analysis', icon: Users },
  { path: '/capacity-intelligence', label: 'Capacity Intelligence', icon: Activity },
  { path: '/requirements-provenance', label: 'Requirements & Provenance', icon: Settings },
  { path: '/constraint-validation', label: 'Constraint Validation', icon: CheckSquare },
  { path: '/optimization-analytics', label: 'Optimization Analytics', icon: Activity },
  { path: '/hypothesis-testing', label: 'Hypothesis Testing', icon: HelpCircle },
  { path: '/grounded-explanation', label: 'Grounded Explanation', icon: MessageSquare },
  { path: '/decision-approval', label: 'Decision Approval', icon: CheckCircle2 },
];

export const Sidebar: React.FC = () => {
  const { ingestionStatus, optimizationStatus, approvalStatus } = useStore();

  return (
    <aside className="sidebar">
      <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--border-light)' }}>
        <h1 style={{ fontSize: '1.25rem', color: 'var(--brand-primary)', margin: 0 }}>AEMIIF</h1>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Decision Intelligence</p>
      </div>

      <nav style={{ padding: '1rem', flex: 1, overflowY: 'auto' }}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              padding: '0.75rem 1rem',
              marginBottom: '0.25rem',
              borderRadius: 'var(--radius-md)',
              color: isActive ? 'var(--brand-primary)' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--brand-light)' : 'transparent',
              textDecoration: 'none',
              fontWeight: isActive ? 600 : 500,
              fontSize: '0.875rem'
            })}
          >
            <item.icon size={18} style={{ marginRight: '0.75rem' }} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-light)' }}>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: '0.75rem' }}>System Status</h4>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span className="text-sm">Data</span>
          <span className={`badge ${ingestionStatus === 'success' ? 'badge-success' : 'badge-warning'}`}>
            {ingestionStatus === 'success' ? 'Ready' : 'Pending'}
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span className="text-sm">Optimization</span>
          <span className={`badge ${optimizationStatus === 'success' ? 'badge-success' : 'badge-warning'}`}>
            {optimizationStatus === 'success' ? 'Optimal' : 'Pending'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span className="text-sm">Approval</span>
          <span className={`badge ${
            approvalStatus === 'APPROVED' ? 'badge-success' : 
            approvalStatus === 'REJECTED' ? 'badge-danger' : 
            approvalStatus === 'PENDING_APPROVAL' ? 'badge-warning' : 'badge-info'
          }`}>
            {approvalStatus === 'APPROVED' ? 'Approved' : 
             approvalStatus === 'REJECTED' ? 'Rejected' : 
             approvalStatus === 'PENDING_APPROVAL' ? 'Pending' : 'N/A'}
          </span>
        </div>
      </div>
    </aside>
  );
};

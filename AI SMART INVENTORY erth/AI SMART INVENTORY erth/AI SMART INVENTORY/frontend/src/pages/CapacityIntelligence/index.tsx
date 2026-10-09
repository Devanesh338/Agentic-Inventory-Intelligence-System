import React from 'react';
import { formatPercentage } from '../../utils/formatters';
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
  const supplierAllocations = capacitySummary.supplier_allocations || [];

  // Secondary lookup from supplier_analysis in case capacity wasn't directly in supplier_allocations
  const supplierAnalysis = optimizationResult.supplier_analysis || [];
  const capacityLookup = new Map<string, number>();
  if (Array.isArray(supplierAnalysis)) {
    supplierAnalysis.forEach((s: any) => {
      if (s?.supplier_id && s?.capacity) {
        capacityLookup.set(s.supplier_id, Math.max(capacityLookup.get(s.supplier_id) || 0, Number(s.capacity)));
      }
    });
  }

  // Normalize supplierAllocations whether it's an Array or an Object
  let allocationsList: Array<{
    supplierId: string;
    capacity: number;
    allocated: number;
    utilization: number;
    isFeasible: boolean;
  }> = [];

  if (Array.isArray(supplierAllocations)) {
    allocationsList = supplierAllocations.map((item: any, idx: number) => {
      const sid = item?.supplier_id || item?.supplier || item?.id || `SUP${String(idx + 1).padStart(3, '0')}`;
      let cap = Number(item?.capacity ?? item?.available_capacity ?? 0);
      if (cap === 0 && capacityLookup.has(sid)) {
        cap = capacityLookup.get(sid)!;
      }
      const alloc = Number(item?.allocated ?? item?.quantity ?? item?.allocated_quantity ?? 0);
      if (cap === 0 && alloc > 0) {
        cap = alloc;
      }
      
      let util = 0;
      if (item?.utilization !== undefined && item?.utilization !== null) {
        util = item.utilization > 1 ? item.utilization / 100 : item.utilization;
      } else if (cap > 0) {
        util = alloc / cap;
      }

      const isFeasible = item?.is_feasible !== undefined
        ? Boolean(item.is_feasible)
        : (cap > 0 ? alloc <= cap : true);

      return {
        supplierId: sid,
        capacity: cap,
        allocated: alloc,
        utilization: util,
        isFeasible
      };
    });
  } else if (typeof supplierAllocations === 'object' && supplierAllocations !== null) {
    allocationsList = Object.entries(supplierAllocations).map(([key, details]: [string, any], idx: number) => {
      const sid = details?.supplier_id || details?.supplier || key || `SUP${String(idx + 1).padStart(3, '0')}`;
      let cap = Number(details?.capacity ?? details?.available_capacity ?? 0);
      if (cap === 0 && capacityLookup.has(sid)) {
        cap = capacityLookup.get(sid)!;
      }
      const alloc = Number(details?.allocated ?? details?.quantity ?? details?.allocated_quantity ?? 0);
      if (cap === 0 && alloc > 0) {
        cap = alloc;
      }

      let util = 0;
      if (details?.utilization !== undefined && details?.utilization !== null) {
        util = details.utilization > 1 ? details.utilization / 100 : details.utilization;
      } else if (cap > 0) {
        util = alloc / cap;
      }

      const isFeasible = details?.is_feasible !== undefined
        ? Boolean(details.is_feasible)
        : (cap > 0 ? alloc <= cap : true);

      return {
        supplierId: sid,
        capacity: cap,
        allocated: alloc,
        utilization: util,
        isFeasible
      };
    });
  }

  // Fallback: If allocationsList is empty but supplierAnalysis exists, populate from supplierAnalysis
  if (allocationsList.length === 0 && Array.isArray(supplierAnalysis) && supplierAnalysis.length > 0) {
    const grouped = new Map<string, { capacity: number; allocated: number }>();
    supplierAnalysis.forEach((s: any) => {
      const sid = s.supplier_id;
      if (!sid) return;
      const prev = grouped.get(sid) || { capacity: 0, allocated: 0 };
      grouped.set(sid, {
        capacity: Math.max(prev.capacity, Number(s.capacity || 0)),
        allocated: prev.allocated + Number(s.quantity || 0)
      });
    });

    allocationsList = Array.from(grouped.entries()).map(([sid, data]) => {
      const cap = data.capacity > 0 ? data.capacity : data.allocated;
      const util = cap > 0 ? data.allocated / cap : 0;
      return {
        supplierId: sid,
        capacity: cap,
        allocated: data.allocated,
        utilization: util,
        isFeasible: data.allocated <= cap
      };
    });
  }

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
              {allocationsList.map((item, idx) => (
                <tr key={item.supplierId || idx}>
                  <td style={{ fontWeight: 500 }}>{item.supplierId}</td>
                  <td>{item.capacity}</td>
                  <td style={{ fontWeight: 'bold' }}>{item.allocated}</td>
                  <td>{formatPercentage(item.utilization)}</td>
                  <td>
                    <span className={`badge ${item.isFeasible ? 'badge-success' : 'badge-danger'}`}>
                      {item.isFeasible ? 'PASS' : 'FAIL'}
                    </span>
                  </td>
                </tr>
              ))}
              {allocationsList.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }} className="text-gray">
                    No supplier allocations recorded for this plan.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

import os

pages = [
    "ExecutiveOverview", "ProcurementPlan", "DemandInventory", 
    "SupplierAnalysis", "CapacityIntelligence", "RequirementsProvenance", 
    "ConstraintValidation", "OptimizationAnalytics", "HypothesisTesting", 
    "GroundedExplanation", "DecisionApproval"
]

for p in pages:
    os.makedirs(f"src/pages/{p}", exist_ok=True)
    title = "".join([" " + c if c.isupper() else c for c in p]).strip()
    content = f"""import React from 'react';

export const {p}: React.FC = () => {{
  return (
    <div className="card">
      <h2 style={{{{ marginBottom: '1rem' }}}}>{title}</h2>
      <p className="text-gray">This module is part of the AEMIIF decision dashboard.</p>
    </div>
  );
}};
"""
    with open(f"src/pages/{p}/index.tsx", "w") as f:
        f.write(content)

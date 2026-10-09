import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';

// Pages
import { ExecutiveOverview } from './pages/ExecutiveOverview';
import { ProcurementPlan } from './pages/ProcurementPlan';
import { DemandInventory } from './pages/DemandInventory';
import { SupplierAnalysis } from './pages/SupplierAnalysis';
import { CapacityIntelligence } from './pages/CapacityIntelligence';
import { RequirementsProvenance } from './pages/RequirementsProvenance';
import { ConstraintValidation } from './pages/ConstraintValidation';
import { OptimizationAnalytics } from './pages/OptimizationAnalytics';
import { HypothesisTesting } from './pages/HypothesisTesting';
import { GroundedExplanation } from './pages/GroundedExplanation';
import { DecisionApproval } from './pages/DecisionApproval';

export const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/executive-overview" replace />} />
          <Route path="executive-overview" element={<ExecutiveOverview />} />
          <Route path="procurement-plan" element={<ProcurementPlan />} />
          <Route path="demand-inventory" element={<DemandInventory />} />
          <Route path="supplier-analysis" element={<SupplierAnalysis />} />
          <Route path="capacity-intelligence" element={<CapacityIntelligence />} />
          <Route path="requirements-provenance" element={<RequirementsProvenance />} />
          <Route path="constraint-validation" element={<ConstraintValidation />} />
          <Route path="optimization-analytics" element={<OptimizationAnalytics />} />
          <Route path="hypothesis-testing" element={<HypothesisTesting />} />
          <Route path="grounded-explanation" element={<GroundedExplanation />} />
          <Route path="decision-approval" element={<DecisionApproval />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;

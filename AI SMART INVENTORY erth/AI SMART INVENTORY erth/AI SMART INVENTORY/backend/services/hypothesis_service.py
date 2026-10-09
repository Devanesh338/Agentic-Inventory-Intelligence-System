from typing import Dict, Any, List
from scipy import stats
import numpy as np

def evaluate_hypothesis(plan_items: List[Dict[str, Any]], sups: List[Any], optimization_status: str) -> Dict[str, Any]:
    """
    Evaluates whether the optimization significantly reduces cost compared to average available supplier baselines.
    Returns a dictionary suitable for API Hypotheis testing response.
    """
    if optimization_status not in ["OPTIMAL", "FEASIBLE"] or not plan_items or not sups:
        return {
            "is_valid": False,
            "message": "Statistical comparison unavailable. Requires optimal plan and supplier candidates."
        }

    baseline_costs = []
    optimized_costs = []
    
    for item in plan_items:
        pid = item.get("product_id")
        qty = item.get("quantity", item.get("order_quantity", 0))
        opt_unit_cost = item.get("unit_cost", 0)
        
        # Find eligible suppliers for this product
        eligible_sups = [s for s in sups if (getattr(s, "product_id", None) or (s.get("product_id") if isinstance(s, dict) else None)) == pid]
        
        if eligible_sups and qty > 0:
            avg_unit_cost = sum((getattr(s, "unit_cost", 0) or (s.get("unit_cost") if isinstance(s, dict) else 0)) for s in eligible_sups) / len(eligible_sups)
            
            # Observation: Total cost for this line if we bought it at avg market rate vs optimized rate
            baseline_costs.append(avg_unit_cost * qty)
            optimized_costs.append(opt_unit_cost * qty)
    
    n = len(baseline_costs)
    if n < 2:
        return {
            "is_valid": False,
            "message": "Insufficient observations for hypothesis testing (n < 2)."
        }
        
    t_stat, p_val = stats.ttest_rel(baseline_costs, optimized_costs)
    
    alpha = 0.05
    
    if np.isnan(t_stat) or np.isnan(p_val):
        decision = "Not statistically meaningful"
        interpretation = "Zero variance in cost differences. The optimized cost exactly equals the baseline average."
    else:
        if p_val < alpha:
            if t_stat > 0: # Baseline > Optimized
                decision = "Reject H0"
                interpretation = "The optimization significantly reduces procurement cost (p < 0.05)."
            else:
                decision = "Reject H0 (Warning)"
                interpretation = "The optimized cost is actually significantly HIGHER than baseline."
        else:
            decision = "Fail to reject H0"
            interpretation = "No significant cost difference detected."

    return {
        "is_valid": True,
        "hypothesis_0": "Optimization does not significantly reduce procurement cost.",
        "hypothesis_1": "Optimization significantly reduces procurement cost.",
        "test_used": "Paired T-Test",
        "sample_size": n,
        "t_statistic": None if np.isnan(t_stat) else float(t_stat),
        "p_value": None if np.isnan(p_val) else float(p_val),
        "significance_level": alpha,
        "decision": decision,
        "interpretation": interpretation
    }

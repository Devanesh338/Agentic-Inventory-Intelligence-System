import os
import re

PAGES_DIR = r"c:\Users\daksh\Downloads\AI SMART INVENTORY erth\Ai Smart Inventory\frontend\src\pages"

def patch_file(filepath, replacements, add_imports=None):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, does not exist")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
        
    if add_imports and add_imports not in content:
        # Add imports right after the first import
        content = re.sub(r"^(import .*;\n)", r"\1" + add_imports + "\n", content, count=1)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Patched {filepath}")

formatters_import = "import { formatCurrency, formatPercentage, formatReliability, formatNumber, formatStatus } from '../../utils/formatters';"

# ExecutiveOverview
patch_file(
    os.path.join(PAGES_DIR, "ExecutiveOverview", "index.tsx"),
    [
        (r"optimizationResult\.cost_summary\?\.total_cost", r"optimizationResult.summary?.total_cost"),
        (r"optimizationResult\.cost_summary\?\.budget_utilization_percent", r"optimizationResult.summary?.budget_utilization"),
        (r"optimizationResult\.achieved_service_level", r"optimizationResult.summary?.achieved_service_level"),
        (r"optimizationResult\.cost_summary\?\.procurement_cost", r"optimizationResult.summary?.procurement_cost"),
        (r"₹\{?([A-Za-z0-9_\.\?]+(\.toLocaleString\(\))?)\}?", r"{formatCurrency(\1)}"),
        (r"\{?([A-Za-z0-9_\.\?]+)(\.toFixed\([0-9]+\))?\}?%", r"{formatPercentage(\1)}")
    ],
    formatters_import
)

# ProcurementPlan
patch_file(
    os.path.join(PAGES_DIR, "ProcurementPlan", "index.tsx"),
    [
        (r"item\.procurement_cost", r"item.total_cost"),
        (r"item\.supplier_reliability", r"item.reliability"),
        (r"optimizationResult\.cost_summary\?\.total_cost", r"optimizationResult.summary?.total_cost"),
        (r"optimizationResult\.cost_summary\?\.budget_utilization_percent", r"optimizationResult.summary?.budget_utilization"),
        (r"₹\{?([A-Za-z0-9_\.\?]+)(\.toLocaleString\(\))?\}?", r"{formatCurrency(\1)}"),
        (r"\{?\(([A-Za-z0-9_\.\?]+)\s*\*\s*100\)\.toFixed\([0-9]+\)\}?%", r"{formatReliability(\1)}"),
        (r"\{?([A-Za-z0-9_\.\?]+)(\.toFixed\([0-9]+\))?\}?%", r"{formatPercentage(\1)}")
    ],
    formatters_import
)

# CapacityIntelligence
patch_file(
    os.path.join(PAGES_DIR, "CapacityIntelligence", "index.tsx"),
    [
        (r"optimizationResult\.capacity_summary", r"optimizationResult.capacity"),
        (r"capacityData\.total_required", r"capacityData.global_required_capacity"),
        (r"capacityData\.total_available", r"capacityData.global_available_capacity"),
        (r"capacityData\.utilization_percent", r"capacityData.capacity_utilization"),
        (r"\{?([A-Za-z0-9_\.\?]+)(\.toFixed\([0-9]+\))?\}?%", r"{formatPercentage(\1)}")
    ],
    formatters_import
)

# SupplierAnalysis
patch_file(
    os.path.join(PAGES_DIR, "SupplierAnalysis", "index.tsx"),
    [
        (r"item\.supplier_reliability", r"item.reliability"),
        (r"\{?\(([A-Za-z0-9_\.\?]+)\s*\*\s*100\)\.toFixed\([0-9]+\)\}?%", r"{formatReliability(\1)}")
    ],
    formatters_import
)

# RequirementsProvenance
patch_file(
    os.path.join(PAGES_DIR, "RequirementsProvenance", "index.tsx"),
    [
        (r"optimizationResult\.user_requirements\?\.original_user_request", r"optimizationResult.original_user_query"),
        (r"optimizationResult\.user_requirements", r"optimizationResult.user_parameters"),
        (r"optimizationResult\.user_parameters\?\.budget", r"optimizationResult.user_parameters?.budget_limit"),
        (r"optimizationResult\.user_parameters\?\.max_lead_time_days", r"optimizationResult.user_parameters?.max_lead_time"),
        (r"optimizationResult\.user_parameters\?\.min_service_level", r"optimizationResult.user_parameters?.target_service_level"),
        (r"optimizationResult\.objective_weights\?\.purchase_cost", r"optimizationResult.objective_weights?.procurement_cost"),
    ],
    formatters_import
)

# ConstraintValidation
patch_file(
    os.path.join(PAGES_DIR, "ConstraintValidation", "index.tsx"),
    [
        (r"optimizationResult\.constraint_summary\?\.([a-zA-Z_]+)\?", r"optimizationResult.constraints?.\1?")
    ],
    formatters_import
)

# OptimizationAnalytics
patch_file(
    os.path.join(PAGES_DIR, "OptimizationAnalytics", "index.tsx"),
    [
        (r"optimizationResult\.cost_summary\?\.total_purchase_cost", r"optimizationResult.summary?.procurement_cost"),
        (r"optimizationResult\.cost_summary\?\.total_transport_cost", r"optimizationResult.summary?.transport_cost"),
        (r"optimizationResult\.cost_summary\?\.total_holding_cost", r"optimizationResult.summary?.holding_cost"),
        (r"optimizationResult\.cost_summary\?\.total_stockout_cost", r"optimizationResult.summary?.stockout_cost"),
        (r"optimizationResult\.cost_summary\?\.total_cost", r"optimizationResult.summary?.total_cost"),
        (r"optimizationResult\.cost_summary\?\.budget_utilization_percent", r"optimizationResult.summary?.budget_utilization"),
    ],
    formatters_import
)

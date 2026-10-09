from typing import List, Optional
from datetime import datetime
from collections import defaultdict
from .schemas import ForecastOutput, InventoryOutput, SupplierOption, UserDecisionConfig
from .mcp_tools import get_sales_history, get_inventory, get_supplier_options

class ForecastAgent:
    def run(self, region: str, product_id: Optional[str] = None, store_id: Optional[str] = None) -> List[ForecastOutput]:
        """Calculate 7-day moving average forecast for all products/stores in region."""
        sales = get_sales_history(region, product_id, store_id)
        
        grouped = defaultdict(list)
        for s in sales:
            grouped[(s['product_id'], s['store_id'])].append(s)
            
        forecasts = []
        for (pid, sid), p_sales in grouped.items():
            days_available = len(p_sales)
            if days_available > 7:
                p_sales = p_sales[:7]
                days_available = 7
                
            total_sales = sum(s['quantity_sold'] for s in p_sales)
            avg_daily = total_sales / days_available if days_available > 0 else 0
            forecast_7_days = int(avg_daily * 7)
            
            forecasts.append(ForecastOutput(
                region=region,
                product_id=pid,
                store_id=sid,
                historical_period_days=days_available,
                forecast_horizon=7,
                forecast_demand=forecast_7_days,
                average_daily_demand=round(avg_daily, 2),
                model_name="7-Day Moving Average",
                confidence=0.8 if days_available == 7 else 0.4
            ))
            
        return forecasts

class InventoryAgent:
    def run(self, region: str, forecasts: List[ForecastOutput], product_id: Optional[str] = None, store_id: Optional[str] = None) -> List[InventoryOutput]:
        """Calculate deterministic inventory indicators for all products/stores in region."""
        inventory_records = get_inventory(region, product_id, store_id)
        
        forecast_map = {(f.product_id, f.store_id): f for f in forecasts}
        
        results = []
        for r in inventory_records:
            pid = r['product_id']
            sid = r['store_id']
            f = forecast_map.get((pid, sid))
            forecast_demand = f.forecast_demand if f else 0
            
            current_stock = r['current_stock']
            safety_stock = r['safety_stock']
            incoming_quantity = r['incoming_quantity']
            
            inventory_position = current_stock + incoming_quantity
            projected_stock = inventory_position - forecast_demand
            
            replenishment_requirement = max(0, forecast_demand + safety_stock - inventory_position)
            
            if projected_stock < 0:
                risk_level = "HIGH"
            elif projected_stock < safety_stock:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
                
            results.append(InventoryOutput(
                region=region,
                product_id=pid,
                store_id=sid,
                current_stock=current_stock,
                incoming_quantity=incoming_quantity,
                forecast_demand=forecast_demand,
                projected_stock=projected_stock,
                safety_stock=safety_stock,
                inventory_position=inventory_position,
                replenishment_requirement=replenishment_requirement,
                risk_level=risk_level,
                storage_capacity=r.get('storage_capacity', None)
            ))
            
        return results

class SupplierAgent:
    def run(self, region: str, config: UserDecisionConfig, product_id: Optional[str] = None) -> List[SupplierOption]:
        """Produce a list of feasible supplier options based on hard constraints."""
        raw_options = get_supplier_options(region, product_id)
        
        options = []
        
        for opt in raw_options:
            supplier_id = opt['supplier_id']
            pid = opt['product_id']
            
            # Dummy distance for prototyping without coordinates
            distance = 50.0 
            transport_cost = float(opt['transport_cost_per_km']) * float(distance) if opt['transport_cost_per_km'] is not None else 0.0
            
            feasibility = "feasible"
            reasons = []
            
            if config.parameters.max_lead_time_days is not None:
                if opt['lead_time_days'] > config.parameters.max_lead_time_days:
                    feasibility = "infeasible"
                    reasons.append(f"Lead time {opt['lead_time_days']} > limit {config.parameters.max_lead_time_days}")
                    
            if config.parameters.max_distance_km is not None:
                if distance > config.parameters.max_distance_km:
                    feasibility = "infeasible"
                    reasons.append(f"Distance {distance} > limit {config.parameters.max_distance_km}")
            
            if config.parameters.min_supplier_reliability is not None:
                if opt['reliability_score'] < config.parameters.min_supplier_reliability:
                    feasibility = "infeasible"
                    reasons.append(f"Supplier reliability {opt['reliability_score']} < limit {config.parameters.min_supplier_reliability}")
            
            options.append(SupplierOption(
                supplier_id=supplier_id,
                region=region,
                product_id=pid,
                unit_cost=float(opt['unit_cost']),
                moq=opt['moq'],
                lead_time_days=opt['lead_time_days'],
                reliability=float(opt['reliability_score']),
                capacity=opt['capacity'],
                distance_km=distance,
                transport_cost=transport_cost,
                feasibility_status=feasibility,
                infeasibility_reason="; ".join(reasons) if reasons else None
            ))
            
        return options


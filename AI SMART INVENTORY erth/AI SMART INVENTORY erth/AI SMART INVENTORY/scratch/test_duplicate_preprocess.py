import pandas as pd
from app import preprocess_dataframe
from io import StringIO

csv_data = """supplier_id,supplier_name,region,product_id,unit_cost,moq,capacity,lead_time_days,reliability_score,latitude,longitude,transport_cost_per_km,transport_cost_per_km
SUP001,ABC Supplies,Chennai-North,P001,80.25,110,430,3,0.955,13.086,80.2253,2.46,3.46
SUP002,XYZ Supplies,Chennai-North,P001,80.96,110,360,5,0.919,13.0757,80.2512,2.43,3.43
"""

def main():
    df = pd.read_csv(StringIO(csv_data))
    print("Original columns:", df.columns.tolist())
    
    cleaned = preprocess_dataframe(df, "Suppliers")
    print("Cleaned columns:", cleaned.columns.tolist())

if __name__ == "__main__":
    main()

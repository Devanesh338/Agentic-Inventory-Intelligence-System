from app import preprocess_dataframe
from aemiif.validation_ingestion import validate_suppliers
import pandas as pd

def test_wrong_file():
    df_sales = pd.read_csv('data/sales_history.csv')
    df_sales_clean = preprocess_dataframe(df_sales, "Sales")
    
    ok, errs = validate_suppliers(df_sales_clean)
    print("If you upload sales_history.csv as suppliers.csv:")
    print("Validation OK?", ok)
    print("Errors:", errs)
    print()

    df_inv = pd.read_csv('data/inventory.csv')
    df_inv_clean = preprocess_dataframe(df_inv, "Inventory")
    
    ok, errs = validate_suppliers(df_inv_clean)
    print("If you upload inventory.csv as suppliers.csv:")
    print("Validation OK?", ok)
    print("Errors:", errs)

if __name__ == "__main__":
    test_wrong_file()

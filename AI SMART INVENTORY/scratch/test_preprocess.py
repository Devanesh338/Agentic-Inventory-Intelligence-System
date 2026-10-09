import pandas as pd
from app import preprocess_dataframe

def main():
    df = pd.read_csv('data/suppliers.csv')
    print("Original columns:", df.columns.tolist())
    
    cleaned = preprocess_dataframe(df, "Suppliers")
    print("Cleaned columns:", cleaned.columns.tolist())

if __name__ == "__main__":
    main()

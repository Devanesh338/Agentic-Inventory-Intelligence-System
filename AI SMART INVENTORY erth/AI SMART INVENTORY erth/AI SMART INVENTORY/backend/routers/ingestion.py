from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, Dict, Any
import pandas as pd
import io
from backend.services.ingestion_service import preprocess_dataframe, clean_duplicate_columns
from aemiif.validation_ingestion import validate_sales, validate_inventory, validate_suppliers, validate_cross_dataset
from backend.schemas.api_responses import APIUploadValidationResult

router = APIRouter(tags=["Ingestion"])

@router.post("/upload", response_model=APIUploadValidationResult)
async def upload_datasets(
    sales_file: Optional[UploadFile] = File(None),
    inventory_file: Optional[UploadFile] = File(None),
    suppliers_file: Optional[UploadFile] = File(None)
):
    results = {"tables": {}, "validation": {"errors": [], "warnings": []}}
    
    dfs = {}
    
    async def process_file(file: UploadFile, name: str, validate_func):
        content = await file.read()
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            results["validation"]["errors"].append(f"Failed to read {name} CSV: {str(e)}")
            return None
        
        success, warns, errs = clean_duplicate_columns(df)
        if not success:
            results["validation"]["errors"].extend(errs)
            return None
        
        results["validation"]["warnings"].extend(warns)
        
        cleaned_df, preprocess_success, preprocess_warns = preprocess_dataframe(df, dataset_name=name)
        results["validation"]["warnings"].extend(preprocess_warns)
        
        is_valid, validation_errors = validate_func(cleaned_df)
        if not is_valid:
            results["validation"]["errors"].extend(validation_errors)
            return None
            
        results["tables"][name] = {"rows": len(cleaned_df)}
        return cleaned_df
        
    if not sales_file and not inventory_file and not suppliers_file:
        results["status"] = "error"
        results["validation"]["errors"].append("No CSV files were selected. Please select at least one file to upload, or use the pre-seeded database.")
        return APIUploadValidationResult(**results)
        
    if sales_file:
        dfs["sales"] = await process_file(sales_file, "sales_history", validate_sales)
    if inventory_file:
        dfs["inventory"] = await process_file(inventory_file, "inventory", validate_inventory)
    if suppliers_file:
        dfs["suppliers"] = await process_file(suppliers_file, "suppliers", validate_suppliers)
        
    if len(dfs) == 3 and all(v is not None for v in dfs.values()):
        is_valid, cross_errors = validate_cross_dataset(dfs["sales"], dfs["inventory"], dfs["suppliers"])
        if not is_valid:
            results["validation"]["errors"].extend(cross_errors)
            
    # Push validated datasets to the database without wiping schema
    valid_dfs = {k: v for k, v in dfs.items() if v is not None}
    if not results["validation"]["errors"] and len(valid_dfs) > 0:
        try:
            from scripts.seed_database import ingest_dataframe
            if "sales" in valid_dfs:
                ingest_dataframe("sales_history", valid_dfs["sales"], replace=True)
            if "inventory" in valid_dfs:
                ingest_dataframe("inventory", valid_dfs["inventory"], replace=True)
            if "suppliers" in valid_dfs:
                ingest_dataframe("suppliers", valid_dfs["suppliers"], replace=True)
            results["status"] = "success"
        except Exception as e:
            results["validation"]["errors"].append(f"Database insertion failed: {str(e)}")
            results["status"] = "error"
    else:
        results["status"] = "error" if results["validation"]["errors"] else "partial_success"
        
    return APIUploadValidationResult(**results)

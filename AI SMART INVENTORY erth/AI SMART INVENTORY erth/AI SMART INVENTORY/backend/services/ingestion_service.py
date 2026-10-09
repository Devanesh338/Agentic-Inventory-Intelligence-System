import pandas as pd
import re
from typing import Tuple, List, Dict, Any

def clean_duplicate_columns(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Removes duplicate columns created by pandas (e.g., .1) if they are identical to the base column.
    Returns (success_status, warnings, errors).
    """
    warnings_list = []
    errors_list = []
    
    dup_cols = [c for c in df.columns if '.' in c and c.split('.')[-1].isdigit()]
    for dup in dup_cols:
        base_col = dup.rsplit('.', 1)[0]
        if base_col in df.columns:
            if df[base_col].equals(df[dup]):
                df.drop(columns=[dup], inplace=True)
                warnings_list.append(f"Removed identical duplicate column: {dup}")
            else:
                errors_list.append(f"Conflicting data found in duplicate column: {dup}")
                return False, warnings_list, errors_list
    return True, warnings_list, errors_list

def preprocess_dataframe(df: pd.DataFrame, dataset_name: str = "Dataset") -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    AEMIIF preprocessing layer.
    Returns (cleaned_dataframe, success_messages, warning_messages).
    """
    df = df.copy()
    success_messages = []
    warning_messages = []

    # 1. Normalize column names
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\ufeff", "", regex=False)  # BOM
        .str.strip()
    )

    # 2. Remove unnamed CSV index columns
    unnamed_cols = [
        col for col in df.columns
        if str(col).lower().startswith("unnamed:")
    ]

    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # 3. Normalize duplicate column naming
    def canonical_name(col):
        col = str(col).strip()
        col = re.sub(r"\.\d+$", "", col)
        return col

    original_columns = list(df.columns)
    column_groups = {}

    for col in original_columns:
        base = canonical_name(col)
        if base not in column_groups:
            column_groups[base] = []
        column_groups[base].append(col)

    # 4. Merge duplicate logical columns
    cleaned = pd.DataFrame(index=df.index)

    for base_name, cols in column_groups.items():
        if len(cols) == 1:
            cleaned[base_name] = df[cols[0]]
            continue

        warning_messages.append(
            f"⚠️ {dataset_name}: duplicate field detected: "
            f"{base_name} ({len(cols)} columns). "
            f"Preprocessing is merging them."
        )

        merged = df[cols[0]].copy()
        conflict_count = 0

        for duplicate_col in cols[1:]:
            current = df[duplicate_col]
            both_present = merged.notna() & current.notna()
            try:
                conflicts = (
                    both_present &
                    (merged.astype(str).str.strip() != current.astype(str).str.strip())
                )
                conflict_count += int(conflicts.sum())
            except Exception:
                pass

            merged = merged.where(merged.notna(), current)

        if conflict_count > 0:
            warning_messages.append(
                f"⚠️ {dataset_name}: {base_name} had "
                f"{conflict_count} conflicting duplicate values. "
                f"The first non-null value was retained deterministically."
            )

        cleaned[base_name] = merged

    # 5. Remove completely empty rows
    cleaned = cleaned.dropna(how="all")

    # 6. Strip whitespace from string columns
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        if pd.api.types.is_object_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

    # 7. Convert common numeric fields
    numeric_keywords = [
        "cost", "price", "value", "quantity", "stock", "capacity",
        "reliability", "lead_time", "distance", "demand", "sales",
        "amount", "budget", "moq"
    ]

    for column in cleaned.columns:
        column_lower = column.lower()
        if any(keyword in column_lower for keyword in numeric_keywords):
            if column_lower.endswith("_id") or column_lower == "id":
                continue
            try:
                converted = pd.to_numeric(cleaned[column], errors="coerce")
                if converted.notna().sum() > 0:
                    cleaned[column] = converted
            except Exception:
                pass

    # 8. Final duplicate safety check
    if cleaned.columns.duplicated().any():
        duplicated = cleaned.columns[cleaned.columns.duplicated()].tolist()
        warning_messages.append(f"⚠️ Final duplicate columns removed: {duplicated}")
        cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]

    # 9. Show preprocessing result
    success_messages.append(
        f"✅ {dataset_name} preprocessing complete: "
        f"{len(df)} ➔ {len(cleaned)} rows, "
        f"{len(original_columns)} ➔ {len(cleaned.columns)} columns"
    )

    return cleaned, success_messages, warning_messages

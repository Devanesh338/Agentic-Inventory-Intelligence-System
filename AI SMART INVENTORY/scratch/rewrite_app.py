import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace clean_duplicate_columns
pattern1 = re.compile(r"def clean_duplicate_columns.*?return True\n", re.DOTALL)
replacement1 = """from backend.services.ingestion_service import clean_duplicate_columns as backend_clean
from backend.services.ingestion_service import preprocess_dataframe as backend_preprocess

def clean_duplicate_columns(df: pd.DataFrame) -> bool:
    success, warnings, errors = backend_clean(df)
    import streamlit as st
    for w in warnings:
        st.warning(w)
    for e in errors:
        st.error(e)
    return success
"""
content = pattern1.sub(replacement1, content)

# Replace preprocess_dataframe
pattern2 = re.compile(r"def preprocess_dataframe.*?return cleaned\n", re.DOTALL)
replacement2 = """def preprocess_dataframe(df: pd.DataFrame, dataset_name: str = "Dataset") -> pd.DataFrame:
    cleaned, successes, warnings = backend_preprocess(df, dataset_name)
    import streamlit as st
    for w in warnings:
        st.warning(w)
    for s in successes:
        st.success(s)
    return cleaned
"""
content = pattern2.sub(replacement2, content)

# Now hypothesis testing
pattern3 = re.compile(r"baseline_costs = \[\]\s*optimized_costs = \[\](.*?)else:\n\s*st\.write\(\"Statistical comparison unavailable\. Requires optimal plan and supplier candidates\.\"\)", re.DOTALL)
replacement3 = """from backend.services.hypothesis_service import evaluate_hypothesis
                res = evaluate_hypothesis(plan_items, sups, resp.status)
                if not res["is_valid"]:
                    st.warning(res.get("message", "Statistical comparison unavailable."))
                else:
                    st.write(f"**H0**: {res['hypothesis_0']}")
                    st.write(f"**H1**: {res['hypothesis_1']}")
                    
                    if res["t_statistic"] is None or res["p_val"] is None:
                        st.warning(res["interpretation"])
                    else:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Test Used", res["test_used"])
                        col2.metric("Sample Size", f"n={res['sample_size']}")
                        col3.metric("Statistic", f"{res['t_statistic']:.4f}")
                        col4.metric("P-Value", f"{res['p_value']:.4e}")
                        
                        st.write(f"**Significance Level (Alpha)**: {res['significance_level']}")
                        
                        if "Reject" in res["decision"]:
                            if "Warning" in res["decision"]:
                                st.warning(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
                            else:
                                st.success(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
                        else:
                            st.info(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
            else:
                st.write("Statistical comparison unavailable. Requires optimal plan and supplier candidates.")"""

# Replace the block
content = pattern3.sub(replacement3, content)

with open("app_new.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Rewritten successfully")

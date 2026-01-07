"""
verify_app.py - Verify app.py correctness
"""
import re

def verify():
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    errors = []
    
    # Check RANKING_COLUMNS
    if '"final_score"' not in content:
        errors.append("RANKING_COLUMNS missing 'final_score'")
    if '"risk_flag"' not in content:
        errors.append("RANKING_COLUMNS missing 'risk_flag'")
        
    # Check Mapping
    if 'COLUMN_MAPPING =' not in content:
        errors.append("COLUMN_MAPPING missing")
    if '"risk_flag": "risk_flags"' not in content:
        errors.append("Mapping for risk_flag missing")
        
    # Check POST_COLUMNS
    if '"post_url"' not in content:
        errors.append("POST_COLUMNS missing 'post_url'")
        
    # Check LinkColumn
    if 'st.column_config.LinkColumn("링크"' not in content and 'st.column_config.LinkColumn("Link"' not in content:
         # It might be in Korean
         if 'LinkColumn("링크"' not in content:
             errors.append("LinkColumn config missing")

    # Check display_cols logic
    if 'display_cols.append("post_url")' not in content:
        errors.append("display_cols logic missing post_url")

    if errors:
        print("ERRORS FOUND in app.py:")
        for e in errors:
            print(f"- {e}")
    else:
        print("app.py verified successfully!")

if __name__ == "__main__":
    verify()

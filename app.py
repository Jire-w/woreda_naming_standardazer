# app.py
import streamlit as st
import pandas as pd
from standardizer import match_and_merge_two_datasets
import os
from rapidfuzz import process, fuzz

def run_app():
    """Main function to run the Streamlit app for merging two datasets."""

    st.set_page_config(
        page_title="Data Matcher & Merger",
        page_icon="🔗",
        layout="wide"
    )

    # --- Header and Instructions ---
    st.markdown("""
    <h1 style='text-align: center; color: #2C3E50; font-family: "Segoe UI", sans-serif;'>
    Health Facility Data Matcher
    </h1>
    <h3 style='text-align: center; color: #5D6D7E;'>
    Merge and Standardize Two Datasets
    </h3>
    """, unsafe_allow_html=True)

    st.info("""
    This tool matches records from two datasets based on fuzzy matching of **Region**, **Zone**, **Woreda**, and **Health Facilities** names. It then combines the remaining data from both files into a single output.
    
    Make sure both of your files are in CSV or Excel (XLSX) format and contain columns for these key fields. The tool will automatically find the best-matching columns.
    """)

    # --- File Uploads ---
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader(
            "📤 Upload Dataset 1 (e.g., Longitude/Latitude)",
            type=["csv", "xlsx"]
        )
    with col2:
        uploaded_file2 = st.file_uploader(
            "📤 Upload Dataset 2 (e.g., Penta 1/Penta 2)",
            type=["csv", "xlsx"]
        )

    # --- Threshold Sliders ---
    matching_threshold = st.slider(
        "🎯 Matching Threshold",
        min_value=50, max_value=100, value=80,
        help="Controls how strictly records are matched. Lower values allow for more typos but may lead to incorrect matches."
    )
    
    # --- Processing ---
    if uploaded_file1 and uploaded_file2:
        try:
            # Function to read the correct file format
            def read_file(file):
                if file.name.endswith('.csv'):
                    return pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    return pd.read_excel(file)
                else:
                    return None

            df1 = read_file(uploaded_file1)
            df2 = read_file(uploaded_file2)
            
            # These are the required column names for our internal logic
            required_key_columns = ['region', 'zone', 'woreda', 'health_facilities']

            # Function to create a mapping from internal keys to user's column names
            def map_columns(df, required_cols):
                normalized_cols = [col.strip().lower() for col in df.columns]
                col_mapping = {}
                missing_cols = []
                for req_col in required_cols:
                    best_match = process.extractOne(req_col, normalized_cols, scorer=fuzz.ratio)
                    if best_match and best_match[1] >= 85: # Use a high threshold for column names
                        matched_col = df.columns[normalized_cols.index(best_match[0])]
                        col_mapping[req_col] = matched_col
                    else:
                        missing_cols.append(req_col)
                return col_mapping, missing_cols

            # Get column mappings for both dataframes
            col_mapping1, missing1 = map_columns(df1, required_key_columns)
            col_mapping2, missing2 = map_columns(df2, required_key_columns)
            
            if missing1 or missing2:
                if missing1:
                    st.error(f"Dataset 1 is missing the following required columns or a good match could not be found: **{', '.join(missing1)}**")
                if missing2:
                    st.error(f"Dataset 2 is missing the following required columns or a good match could not be found: **{', '.join(missing2)}**")
            else:
                st.info("🔄 Processing and merging your data...")

                # Call the core matching function with the column mappings
                merged_df, unmatched_df1, unmatched_df2 = match_and_merge_two_datasets(
                    df1, df2, col_mapping1, col_mapping2, matching_threshold
                )

                st.success("✅ Datasets merged successfully!")

                # --- Display and Download Results ---
                st.subheader("✅ Merged Data")
                st.dataframe(merged_df)
                st.download_button(
                    "⬇️ Download Merged Data (.csv)",
                    merged_df.to_csv(index=False).encode('utf-8'),
                    "merged_data.csv",
                    "text/csv"
                )
                
                if not unmatched_df1.empty:
                    st.warning(f"⚠️ {len(unmatched_df1)} rows from Dataset 1 could not be matched.")
                    st.subheader("❌ Unmatched Rows (Dataset 1)")
                    st.dataframe(unmatched_df1)
                    st.download_button(
                        "⬇️ Download Unmatched Rows from Dataset 1",
                        unmatched_df1.to_csv(index=False).encode('utf-8'),
                        "unmatched_dataset1.csv",
                        "text/csv"
                    )

                if not unmatched_df2.empty:
                    st.warning(f"⚠️ {len(unmatched_df2)} rows from Dataset 2 could not be matched.")
                    st.subheader("❌ Unmatched Rows (Dataset 2)")
                    st.dataframe(unmatched_df2)
                    st.download_button(
                        "⬇️ Download Unmatched Rows from Dataset 2",
                        unmatched_df2.to_csv(index=False).encode('utf-8'),
                        "unmatched_dataset2.csv",
                        "text/csv"
                    )


        except Exception as e:
            st.error("An error occurred while processing your files.")
            st.exception(e)

if __name__ == '__main__':
    run_app()

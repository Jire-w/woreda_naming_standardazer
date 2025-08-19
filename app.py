# app.py
import streamlit as st
import pandas as pd
from standardizer import match_and_merge_two_datasets
import os

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
    
    Make sure both of your files are in CSV format and contain the key columns.
    """)

    # --- File Uploads ---
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader(
            "📤 Upload Dataset 1 (e.g., Longitude/Latitude)",
            type="csv"
        )
    with col2:
        uploaded_file2 = st.file_uploader(
            "📤 Upload Dataset 2 (e.g., Penta 1/Penta 2)",
            type="csv"
        )

    # --- Threshold Sliders ---
    woreda_hf_threshold = st.slider(
        "🎯 Matching Threshold",
        min_value=50, max_value=100, value=80,
        help="Controls how strictly records are matched. Lower values allow for more typos but may lead to incorrect matches."
    )

    # --- Processing ---
    if uploaded_file1 and uploaded_file2:
        try:
            df1 = pd.read_csv(uploaded_file1)
            df2 = pd.read_csv(uploaded_file2)

            # Define the key columns for matching
            key_columns = ['region', 'zone', 'woreda', 'health_facilities']

            # Check for required columns in both dataframes
            required_in_df1 = [col for col in key_columns if col not in df1.columns.str.lower()]
            required_in_df2 = [col for col in key_columns if col not in df2.columns.str.lower()]

            if required_in_df1:
                st.error(f"Dataset 1 is missing the following required columns: **{', '.join(required_in_df1)}**")
            if required_in_df2:
                st.error(f"Dataset 2 is missing the following required columns: **{', '.join(required_in_df2)}**")
            
            if not required_in_df1 and not required_in_df2:
                st.info("🔄 Processing and merging your data...")

                # Call the new core matching function
                merged_df, unmatched_df1, unmatched_df2 = match_and_merge_two_datasets(
                    df1,
                    df2,
                    key_columns,
                    woreda_hf_threshold
                )

                st.success("✅ Datasets merged successfully!")

                # Display and provide download buttons for the results
                st.subheader("✅ Merged Data")
                st.dataframe(merged_df)
                st.download_button(
                    "⬇️ Download Merged Data",
                    merged_df.to_csv(index=False).encode('utf-8'),
                    "merged_data.csv",
                    "text/csv"
                )

                # Show unmatched records from both datasets
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

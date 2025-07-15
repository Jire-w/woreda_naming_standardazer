import streamlit as st
import pandas as pd
import os
import sys

# Set up import path for standardizer.py
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

from standardizer import load_reference_data, match_and_correct

# --- Page Setup ---
st.set_page_config(layout="wide")
st.title("📍 Woreda Name Standardizer")

# --- Info Header ---
st.info("""
This application standardizes Woreda names in your dataset using a national reference list.
Upload a CSV file that includes the columns: **'Region', 'Zone', and 'Woreda'**.
""")

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload your dataset (CSV)", type=["csv"])

# --- Matching Threshold Controls ---
woreda_threshold = st.slider(
    "🎯 Woreda Match Threshold",
    min_value=50,
    max_value=100,
    value=80,
    help="Lower threshold allows for looser matches; higher is stricter."
)

region_zone_threshold = st.slider(
    "🌍 Region-Zone Match Threshold",
    min_value=50,
    max_value=100,
    value=90,
    help="Controls matching strictness of Region and Zone before matching Woreda."
)

# --- Process Uploaded File ---
if uploaded_file:
    try:
        user_df = pd.read_csv(uploaded_file)
        user_df.columns = user_df.columns.str.strip().str.lower()

        required_columns = ['region', 'zone', 'woreda']
        if not all(col in user_df.columns for col in required_columns):
            st.error("❌ Your CSV must contain: Region, Zone, Woreda columns.")
            st.info(f"Detected columns: {', '.join(user_df.columns)}")
            st.stop()

        reference_path = os.path.join(current_dir, "data", "reference.csv")
        if not os.path.exists(reference_path):
            st.error(f"❌ Reference file not found at: {reference_path}")
            st.stop()

        reference_df = load_reference_data(reference_path)

        with st.spinner("🔄 Standardizing Woreda names..."):
            corrected_df, unmatched_df = match_and_correct(
                user_df.copy(),
                reference_df,
                threshold=woreda_threshold,
                region_zone_threshold=region_zone_threshold
            )

        st.success("✅ Woreda standardization completed.")

        # --- Display Corrected Data ---
        st.subheader("✅ Corrected Data")
        st.dataframe(corrected_df)

        st.download_button(
            label="⬇️ Download Corrected CSV",
            data=corrected_df.to_csv(index=False),
            file_name="standardized_woredas.csv",
            mime="text/csv"
        )

        # --- Display Unmatched Data ---
        if not unmatched_df.empty:
            st.warning(f"⚠️ {len(unmatched_df)} unmatched rows found.")
            st.subheader("❌ Unmatched Rows")
            st.dataframe(unmatched_df)

            st.download_button(
                label="⬇️ Download Unmatched CSV",
                data=unmatched_df.to_csv(index=False),
                file_name="unmatched_woredas.csv",
                mime="text/csv"
            )
        else:
            st.success("🎉 All rows matched successfully!")

    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded CSV file is empty.")
    except pd.errors.ParserError:
        st.error("❌ Failed to parse the CSV file. Please check the format.")
    except Exception as e:
        st.error("❌ An unexpected error occurred:")
        st.exception(e)

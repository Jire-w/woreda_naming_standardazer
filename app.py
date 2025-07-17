import streamlit as st
import pandas as pd
import os
from PIL import Image
from standardizer import load_reference_data, match_and_correct

# --- Setup page ---
st.set_page_config(
    page_title="Woreda Standardizer Tool",
    page_icon="🧭",
    layout="wide"
)

# --- Load Logo ---
current_dir = os.path.dirname(__file__)
logo_path = os.path.join(current_dir, "logo", "your_logo.png")  # Change this if your logo file is named differently

if os.path.exists(logo_path):
    st.image(Image.open(logo_path), width=140)

# --- Title ---
st.markdown("""
<h1 style='text-align: center; color: #2C3E50; font-family: "Segoe UI", sans-serif;'>
Woreda Name Standardizer
</h1>
""", unsafe_allow_html=True)

# --- Instructions ---
st.info("""
This tool helps you clean and standardize Woreda names in your dataset by comparing them with a national reference list.
Make sure your file includes **Region**, **Zone**, and **Woreda** columns (CSV format).
""")

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload your Woreda dataset (.csv)", type="csv")

# --- Threshold Sliders ---
woreda_threshold = st.slider(
    "🎯 Woreda Matching Threshold", min_value=50, max_value=100, value=80,
    help="Controls how strictly Woreda names are matched."
)
region_zone_threshold = st.slider(
    "🌍 Region & Zone Matching Threshold", min_value=50, max_value=100, value=90,
    help="Controls how strictly Region & Zone names are matched."
)

# --- Processing ---
if uploaded_file:
    try:
        user_df = pd.read_csv(uploaded_file)
        user_df.columns = user_df.columns.str.strip().str.lower()
        required_columns = ['region', 'zone', 'woreda']

        if not all(col in user_df.columns for col in required_columns):
            st.error(f"Your file must include these columns: {', '.join(required_columns)}")
            st.info(f"Detected columns: {', '.join(user_df.columns)}")
        else:
            reference_path = os.path.join(current_dir, "data", "reference.csv")
            if not os.path.exists(reference_path):
                st.error(f"Reference file not found at: {reference_path}")
            else:
                reference_df = load_reference_data(reference_path)

                st.info("🔄 Processing your data...")
                corrected_df, unmatched_df = match_and_correct(
                    user_df.copy(),
                    reference_df,
                    threshold=woreda_threshold,
                    region_zone_threshold=region_zone_threshold
                )

                st.success("✅ Woreda names standardized successfully!")

                # Show and download corrected data
                st.subheader("✅ Standardized Data")
                st.dataframe(corrected_df)
                st.download_button("⬇️ Download Corrected File", corrected_df.to_csv(index=False), "standardized_woredas.csv", "text/csv")

                # Unmatched records
                if not unmatched_df.empty:
                    st.warning(f"⚠️ {len(unmatched_df)} rows could not be matched.")
                    st.subheader("❌ Unmatched Rows")
                    st.dataframe(unmatched_df)
                    st.download_button("⬇️ Download Unmatched Rows", unmatched_df.to_csv(index=False), "unmatched_woredas.csv", "text/csv")
                else:
                    st.info("🎉 All rows matched successfully!")

    except Exception as e:
        st.error("An error occurred while processing your file.")
        st.exception(e)

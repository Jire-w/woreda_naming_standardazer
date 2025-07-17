import streamlit as st
import pandas as pd

st.set_page_config(page_title="Woreda Naming Standardizer", layout="centered")

st.title("🧹 Woreda Naming Standardizer Tool")
st.markdown("Upload a CSV file with Woreda names and get a cleaned version.")

# File upload
uploaded_file = st.file_uploader("📁 Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully.")
        st.write("Preview of uploaded data:", df.head())

        # Select column to standardize
        column_name = st.selectbox("📌 Select the column that contains Woreda names", df.columns)

        # Standardization function
        def clean_woreda_name(name):
            if pd.isna(name):
                return ""
            name = str(name).strip().lower()
            replacements = {
                "woreda": "",
                "sub city": "",
                "subcity": "",
                "zone": "",
                "-": " ",
                "_": " "
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            return " ".join(name.title().split())

        # Apply cleaning
        df["Standardized_Woreda"] = df[column_name].apply(clean_woreda_name)
        st.success("✅ Woreda names standardized.")

        # Display result
        st.subheader("🧾 Cleaned Data Preview")
        st.write(df[[column_name, "Standardized_Woreda"]].head())

        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv,
            file_name="standardized_woreda.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("📎 Please upload a CSV file to begin.")

import streamlit as st
import pandas as pd
import os
import sys
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as st_auth

# --- Path Setup ---
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

from standardizer import load_reference_data, match_and_correct

# --- Streamlit Page Setup ---
st.set_page_config(layout="wide")
st.title("📍 Woreda Name Standardizer")
from PIL import Image

# Load and display logo
logo_path = os.path.join(current_dir, "logo", "logo.png")  # Make sure this matches your file/folder name
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.image(logo, width=180)  # You can adjust the size


# --- Load config.yaml ---
config_path = os.path.join(current_dir, 'config.yaml')

if not os.path.exists(config_path):
    st.error(f"❌ config.yaml not found at {config_path}")
    st.stop()

try:
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
except Exception as e:
    st.error(f"❌ Failed to load config.yaml: {e}")
    st.stop()

# --- Validate config content ---
if 'credentials' not in config or 'usernames' not in config['credentials']:
    st.error("❌ config.yaml must include 'credentials > usernames'")
    st.stop()

if 'cookie' not in config or not all(k in config['cookie'] for k in ['name', 'key', 'expiry_days']):
    st.error("❌ config.yaml must include 'cookie' with keys: name, key, expiry_days")
    st.stop()

# --- Authenticator Setup ---
authenticator = st_auth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    expiry_days=config['cookie']['expiry_days']
)

# --- Login ---
name, authentication_status, username = authenticator.login('Login')

if authentication_status is False:
    st.error("❌ Username or password is incorrect.")
    st.stop()
elif authentication_status is None:
    st.warning("🔐 Please enter your username and password.")
    st.stop()

# --- Authenticated User View ---
authenticator.logout("Logout", "sidebar")
st.sidebar.success(f"👋 Welcome {name}!")

st.info("""
This application standardizes Woreda names in your dataset using a national reference list.
Upload a CSV with **'Region', 'Zone', 'Woreda'** columns to begin.
""")

uploaded_file = st.file_uploader("📤 Upload your dataset (CSV)", type=["csv"])

# --- Matching Threshold Sliders ---
woreda_threshold = st.slider("🎯 Woreda Match Threshold", 50, 100, 80)
region_zone_threshold = st.slider("🌍 Region-Zone Match Threshold", 50, 100, 90)

# --- Processing Uploaded File ---
if uploaded_file:
    try:
        user_df = pd.read_csv(uploaded_file)
        user_df.columns = user_df.columns.str.strip().str.lower()

        required_columns = ['region', 'zone', 'woreda']
        if not all(col in user_df.columns for col in required_columns):
            st.error("❌ CSV must contain columns: Region, Zone, Woreda")
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

        # --- Corrected Data Preview ---
        st.subheader("✅ Corrected Data")
        st.dataframe(corrected_df)

        st.download_button(
            "⬇️ Download Corrected CSV",
            corrected_df.to_csv(index=False),
            "standardized_woredas.csv"
        )

        # --- Unmatched Data ---
        if not unmatched_df.empty:
            st.warning(f"⚠️ {len(unmatched_df)} unmatched rows found.")
            st.subheader("❌ Unmatched Data")
            st.dataframe(unmatched_df)

            st.download_button(
                "⬇️ Download Unmatched CSV",
                unmatched_df.to_csv(index=False),
                "unmatched_woredas.csv"
            )
        else:
            st.success("🎉 All rows matched successfully!")

    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded CSV file is empty.")
    except pd.errors.ParserError:
        st.error("❌ Failed to parse CSV. Please check the formatting.")
    except Exception as e:
        st.error("❌ An unexpected error occurred:")
        st.exception(e)

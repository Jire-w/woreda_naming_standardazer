import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load config.yaml
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("config.yaml file not found. Please make sure it's in the root directory.")
    st.stop()

# Create authenticator
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    expiry_days=config['cookie']['expiry_days'],
    preauthorized=config.get('preauthorized', {})
)

# Render login form
name, authentication_status, username = authenticator.login("Login", location="main")

# Handle login status
if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")
    st.title("Woreda Naming Standardizer App")
    st.write("✅ You are now logged in. You can add your main app features below.")
    
    # Example content
    st.subheader("Welcome to the Standardizer!")
    st.write("This is where your app’s main functionality will appear.")
    
elif authentication_status is False:
    st.error("❌ Incorrect username or password")

elif authentication_status is None:
    st.warning("🔐 Please enter your username and password")

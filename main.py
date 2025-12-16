import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import pandas as pd # Needed for Map Visualization and Update/Delete

# --- 0. Configuration and Initialization ---

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def initialize_firebase():
    """Initializes the Firebase Admin SDK using Streamlit secrets."""
    if not firebase_admin._apps:
        try:
            # Load credentials from Streamlit secrets (must match the secrets.toml structure)
            creds_dict = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'), # Fix line breaks
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            }
            
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(
                cred,
                {'databaseURL': st.secrets["firebase"]["database_url"]}
            )
            st.session_state['db_ref'] = db.reference('/cities')
        
        except Exception as e:
            st.error(f"FATAL ERROR: Firebase Initialization Failed. Check your secrets.toml.")
            st.code(e, language='text')
            st.stop()
            
initialize_firebase() # Run initialization at startup

# --- 1. Authentication and State Handlers ---

def check_login(email, password):
    """Simple admin login check."""
    ADMIN_EMAIL = "kaaysha.rao@gmail.com"
    ADMIN_PASSWORD = "123456"

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.success("Login Successful! Redirecting...")
        st.experimental_rerun()
    else:
        st.error("Invalid Email or Password.")

def logout():
    """Resets the login status and reruns."""
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = None
    st.success("Logged out successfully.")
    st.experimental_rerun()

# --- 2. Database CRUD Operations ---

@st.cache_data(ttl=5)
def get_city_data():
    """Retrieves all city data, cached for 5 seconds to reduce reads."""
    try:
        data = st.session_state['db_ref'].get()
        # Convert Firebase dict to a list of dicts with the key included
        if data:
            city_list = []
            for key, value in data.items():
                value['id'] = key # Include Firebase unique ID
                city_list.append(value)
            return city_list
        return []
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def add_city_data(city, country, continent, lat, lon):
    """Creates a new record."""
    st.session_state['db_ref'].push({
        'city': city,
        'country': country,
        'continent': continent,
        'lat': float(lat),
        'lon': float(lon),
        'timestamp': int(time.time())
    })
    st.cache_data.clear() # Clear cache to show new data immediately
    st.success(f"Successfully added **{city}**!")

def update_city_data(city_id, city, country, continent, lat, lon):
    """Updates an existing record."""
    st.session_state['db_ref'].child(city_id).update({
        'city': city,
        'country': country,
        'continent': continent,
        'lat': float(lat),
        'lon': float(lon)
    })
    st.cache_data.clear()
    st.success(f"Successfully updated **{city}**!")

def delete_city_data(city_id):
    """Deletes a record."""
    st.session_state['db_ref'].child(city_id).delete()
    st.cache_data.clear()
    st.warning("City record deleted.")

# --- 3. UI Pages ---

def login_page():
    """Displays the login form."""
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 City Locator Admin Login")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login")
        
        if submit:
            check_login(email, password)

def admin_panel():
    """Displays the main admin interface with CRUD operations."""
    st.set_page_config(page_title="Admin Panel", layout="wide")
    st.title("🌍 City Locator Admin Panel")
    
    col_info, col_logout = st.columns([4, 1])
    with col_info:
        st.info(f"Welcome, **{st.session_state['user_email']}**. Manage City Data below.")
    with col_logout:
        st.button("Logout", on_click=logout, type="primary")

    st.header("1. Create New City")
    with st.expander("➕ Add City Form", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: city = st.text_input("City Name*", key="add_city")
            with col2: country = st.text_input("Country*", key="add_country")
            with col3: continent = st.text_input("Continent*", key="add_continent")
            with col4: lat = st.number_input("Latitude*", format="%.4f", key="add_lat", value=0.0)
            with col5: lon = st.number_input("Longitude*", format="%.4f", key="add_lon", value=0.0)
            
            if st.form_submit_button("Add New City"):
                if city and country and continent and lat is not None and lon is not None:
                    add_city_data(city, country, continent, lat, lon)
                else:
                    st.error("Please fill in all fields (including valid coordinates).")

    st.header("2. View and Visualize Data")
    
    cities = get_city_data()
    
    if cities:
        # Convert list of dicts to a DataFrame for easy handling/visualization
        df = pd.DataFrame(cities)
        
        # Display Data Table
        st.subheader("Data Table")
        st.dataframe(df.drop(columns=['timestamp']), use_container_width=True)
        
        # Display Map Visualization
        st.subheader("Global City Map")
        # Rename columns to 'lat' and 'lon' for st.map to work
        st.map(df[['lat', 'lon']], zoom=1)
        
    else:
        st.info("No cities found in the database. Add one above!")

    st.header("3. Update / Delete City")
    if cities:
        # Create a dictionary for selection {City Name: Firebase ID}
        city_options = {f"{c['city']} ({c['country']})": c['id'] for c in cities}
        
        selected_city_label = st.selectbox("Select City to Edit/Delete:", list(city_options.keys()))
        selected_city_id = city_options[selected_city_label]
        
        # Find the full data for the selected city
        selected_city_data = next((c for c in cities if c['id'] == selected_city_id), {})
        
        with st.form("edit_delete_form"):
            st.subheader(f"Editing: {selected_city_data.get('city')}")
            
            col_edit1, col_edit2, col_edit3, col_edit4, col_edit5 = st.columns(5)
            with col_edit1: edit_city = st.text_input("City Name", value=selected_city_data.get('city'), key="edit_city")
            with col_edit2: edit_country = st.text_input("Country", value=selected_city_data.get('country'), key="edit_country")
            with col_edit3: edit_continent = st.text_input("Continent", value=selected_city_data.get('continent'), key="edit_continent")
            with col_edit4: edit_lat = st.number_input("Latitude", format="%.4f", value=selected_city_data.get('lat', 0.0), key="edit_lat")
            with col_edit5: edit_lon = st.number_input("Longitude", format="%.4f", value=selected_city_data.get('lon', 0.0), key="edit_lon")
            
            col_buttons = st.columns(2)
            with col_buttons[0]:
                if st.form_submit_button("Update Record", type="primary"):
                    update_city_data(selected_city_id, edit_city, edit_country, edit_continent, edit_lat, edit_lon)
            with col_buttons[1]:
                if st.form_submit_button("Delete Record", type="secondary"):
                    delete_city_data(selected_city_id)
                    # Use st.experimental_rerun() after deletion to update the selectbox immediately
                    st.experimental_rerun()

    else:
        st.info("No data available to edit or delete.")

# --- Main Application Execution ---

def main():
    """Main application loop controlling page display."""
    
    if st.session_state['logged_in']:
        admin_panel()
    else:
        login_page()

if __name__ == '__main__':
    main()

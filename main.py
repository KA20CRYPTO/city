import streamlit as st
import requests
import json
import time
import pandas as pd

# --- 0. Hardcoded Configuration ---

# Replace these values with your actual Firebase Realtime Database details
FIREBASE_DATABASE_URL = "https://city-9baf7-default-rtdb.firebaseio.com/cities.json"
# WARNING: This secret is the master key to your database. Keep it secure!
# Find this secret under Project Settings -> Service Accounts -> Database secrets.
FIREBASE_DATABASE_SECRET = "RXhuy413mcmzU17J4ba1RAZ9ZGzFb58r5X7NZF25" 

# Admin Credentials (Hardcoded)
ADMIN_EMAIL = "kaaysha.rao@gmail.com"
ADMIN_PASSWORD = "123456" 
AUTH_TOKEN = FIREBASE_DATABASE_SECRET # Using the secret as the auth token for REST calls

# --- 1. REST API Helper Functions ---

# All API calls will append ?auth=<TOKEN> to the URL for authentication
BASE_URL = f"{FIREBASE_DATABASE_URL}?auth={AUTH_TOKEN}"

@st.cache_data(ttl=5)
def get_city_data():
    """Retrieves all city data via GET request, cached for 5 seconds."""
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        if data:
            # Convert Firebase dict to a DataFrame, including the Firebase unique key (the ID)
            city_list = []
            for key, value in data.items():
                value['id'] = key
                # Ensure lat/lon exist and are float for st.map
                value['lat'] = float(value.get('lat', 0.0))
                value['lon'] = float(value.get('lon', 0.0))
                city_list.append(value)
            return city_list
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching data: {e}")
        return []

def add_city_data(city, country, continent, lat, lon):
    """Creates a new record using POST request."""
    data = {
        'city': city,
        'country': country,
        'continent': continent,
        'lat': float(lat),
        'lon': float(lon),
        'timestamp': int(time.time())
    }
    try:
        # POST request with null path creates a unique key
        response = requests.post(BASE_URL, json=data)
        response.raise_for_status()
        st.cache_data.clear() # Clear cache to show new data immediately
        st.success(f"Successfully added **{city}**!")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error adding data: {e}")

def update_city_data(city_id, city, country, continent, lat, lon):
    """Updates an existing record using PATCH request."""
    update_url = f"{FIREBASE_DATABASE_URL.replace('.json', '')}/{city_id}.json?auth={AUTH_TOKEN}"
    data = {
        'city': city,
        'country': country,
        'continent': continent,
        'lat': float(lat),
        'lon': float(lon)
    }
    try:
        response = requests.patch(update_url, json=data)
        response.raise_for_status()
        st.cache_data.clear()
        st.success(f"Successfully updated **{city}**!")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error updating data: {e}")

def delete_city_data(city_id):
    """Deletes a record using DELETE request."""
    delete_url = f"{FIREBASE_DATABASE_URL.replace('.json', '')}/{city_id}.json?auth={AUTH_TOKEN}"
    try:
        response = requests.delete(delete_url)
        response.raise_for_status()
        st.cache_data.clear()
        st.warning("City record deleted.")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error deleting data: {e}")

# --- 2. Authentication and State Handlers ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def check_login(email, password):
    """Simple admin login check against hardcoded credentials."""
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.success("Login Successful! Redirecting...")
        time.sleep(1) # Give time for the message to show
        st.rerun()
    else:
        st.error("Invalid Email or Password.")
        st.session_state['logged_in'] = False

def logout():
    """Resets the login status and reruns."""
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = None
    st.success("Logged out successfully.")
    st.rerun()

# --- 3. Streamlit UI Pages ---

def login_page():
    """Displays the login form."""
    st.set_page_config(page_title="Login", layout="centered")
    st.title("🔐 City Locator Admin Login (REST API)")
    
    with st.form("login_form"):
        email = st.text_input("Email", value=ADMIN_EMAIL)
        password = st.text_input("Password", type="password", value=ADMIN_PASSWORD)
        submit = st.form_submit_button("Login")
        
        if submit:
            check_login(email, password)

def admin_panel():
    """Displays the main admin interface with CRUD operations."""
    st.set_page_config(page_title="Admin Panel", layout="wide")
    st.title("🌍 City Locator Admin Panel (REST API)")
    
    col_info, col_logout = st.columns([4, 1])
    with col_info:
        st.info(f"Welcome, **{st.session_state['user_email']}**.")
    with col_logout:
        st.button("Logout", on_click=logout, type="primary")

    st.header("1. Create New City")
    with st.expander("➕ Add City Form", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: city = st.text_input("City Name*", key="add_city")
            with col2: country = st.text_input("Country*", key="add_country")
            with col3: continent = st.text_input("Continent*", key="add_continent")
            # Use sensible defaults for lat/lon as Streamlit needs them for map
            with col4: lat = st.number_input("Latitude*", format="%.4f", key="add_lat", value=0.0, step=0.0001)
            with col5: lon = st.number_input("Longitude*", format="%.4f", key="add_lon", value=0.0, step=0.0001)
            
            if st.form_submit_button("Add New City"):
                if city and country and continent and lat is not None and lon is not None:
                    add_city_data(city, country, continent, lat, lon)
                else:
                    st.error("Please fill in all fields (including valid coordinates).")

    st.header("2. View and Visualize Data")
    
    cities = get_city_data()
    
    if cities:
        df = pd.DataFrame(cities)
        
        # Display Data Table
        st.subheader("Data Table")
        st.dataframe(df.drop(columns=['timestamp']), use_container_width=True)
        
        # Display Map Visualization
        st.subheader("Global City Map")
        # st.map requires 'lat' and 'lon' columns
        st.map(df[['lat', 'lon']], zoom=1)
        
    else:
        st.info("No cities found in the database. Add one above!")

    st.header("3. Update / Delete City")
    if cities:
        # Create a dictionary for selection {City Name (Country): Firebase ID}
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
            with col_edit4: edit_lat = st.number_input("Latitude", format="%.4f", value=selected_city_data.get('lat', 0.0), key="edit_lat", step=0.0001)
            with col_edit5: edit_lon = st.number_input("Longitude", format="%.4f", value=selected_city_data.get('lon', 0.0), key="edit_lon", step=0.0001)
            
            col_buttons = st.columns(2)
            with col_buttons[0]:
                if st.form_submit_button("Update Record", type="primary"):
                    update_city_data(selected_city_id, edit_city, edit_country, edit_continent, edit_lat, edit_lon)
            with col_buttons[1]:
                if st.form_submit_button("Delete Record", type="secondary"):
                    delete_city_data(selected_city_id)
                    st.rerun() # Rerun to update the selectbox after deletion

    else:
        st.info("No data available to edit or delete.")

# --- Main Application Execution ---

if __name__ == '__main__':
    if st.session_state['logged_in']:
        admin_panel()
    else:
        login_page()

import streamlit as st
import pandas as pd

# --- 1. Data Setup (Internal Dataset) ---
# Using a Pandas DataFrame for better structure, searching, and potential expansion.
# This structure is highly suitable for deployment on Streamlit Cloud.
# All city names are converted to lowercase in the DataFrame for easy, case-insensitive searching.

DATA = {
    'City': ['London', 'Paris', 'Tokyo', 'New York', 'Sydney', 'Rio de Janeiro', 'Cairo', 'Mumbai', 'Berlin', 'Toronto', 'Cape Town', 'Beijing', 'Moscow', 'Dubai'],
    'Country': ['United Kingdom', 'France', 'Japan', 'United States', 'Australia', 'Brazil', 'Egypt', 'India', 'Germany', 'Canada', 'South Africa', 'China', 'Russia', 'UAE'],
    'Continent': ['Europe', 'Europe', 'Asia', 'North America', 'Australia', 'South America', 'Africa', 'Asia', 'Europe', 'North America', 'Africa', 'Asia', 'Europe/Asia', 'Asia']
}
city_df = pd.DataFrame(DATA)

# Pre-process the 'City' column to be lowercase for case-insensitive matching
city_df['City_Lower'] = city_df['City'].str.lower()

# --- 2. Streamlit UI Configuration and Layout ---

def main():
    """Defines the main structure and logic of the Streamlit application."""

    # Set the page configuration for a professional look
    st.set_page_config(
        page_title="Global City Locator",
        page_icon="🌍",
        layout="centered"
    )

    # Professional Page Title and simple styling
    st.title("🌍 Global City Locator App")
    st.info("Enter a major city name below to find its country and continent.")

    # --- 3. User Input ---
    city_input = st.text_input(
        "Enter City Name:",
        placeholder="e.g., London, tokyo, New York"
    )

    # Create a clean version of the input for searching
    if city_input:
        search_city = city_input.lower().strip()

        # --- 4. Logic and Search (Handling Case-Insensitivity) ---
        # Search the pre-processed lowercase column
        result = city_df[city_df['City_Lower'] == search_city]

        # --- 5. Display Results ---
        if not result.empty:
            # City Found: Display results clearly using a success message
            
            # Extract the first matching row (should only be one)
            city_data = result.iloc[0]
            
            # Use the original capitalization of the city for display
            original_city_name = city_data['City']
            country = city_data['Country']
            continent = city_data['Continent']

            st.success(f"**City Found!**")
            
            # Use a container for a clean, professional result box
            with st.container(border=True):
                st.header(f"📍 {original_city_name}")
                st.metric(label="Country", value=country)
                st.metric(label="Continent", value=continent)

        else:
            # City Not Found: Show a clear error message
            st.error(f"❌ City **'{city_input}'** not found in the database. Please try another city.")
            st.caption("Note: The current database is limited to a small list of major cities.")

    # --- 6. Future Improvements Suggestion ---
    st.sidebar.header("💡 Future Enhancements")
    st.sidebar.markdown(
        """
        1.  **API Integration:** Replace the internal data with a call to a Geo-location API (like Geonames or Google Maps API) for a comprehensive, up-to-date database.
        2.  **Map Visualization:** Use `st.map()` (requires Latitude/Longitude data) to show the city's location on a global map.
        3.  **Caching:** Use `@st.cache_data` on the DataFrame loading/pre-processing step to optimize performance in a deployed environment.
        """
    )


# Run the main function
if __name__ == "__main__":
    main()
  

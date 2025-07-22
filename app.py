import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import re  

st.set_page_config(layout="wide")
st.title("🚦 Traffic Accident Hotspots in Los Angeles")

@st.cache_data
def load_data():
    df = pd.read_csv("Traffic_Collision_Data.csv")
    df = df.dropna(subset=["Location"])

    # Function to extract latitude and longitude using regular expressions
    def extract_coordinates(location_str):
        match = re.search(r'\((\d+\.\d+),\s*(-?\d+\.\d+)\)', location_str)
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            return longitude, latitude  # Note the order: longitude first
        return None, None

    # Apply the function to create separate latitude and longitude columns
    df['Longitude'], df['Latitude'] = zip(*df['Location'].apply(extract_coordinates))
    df = df.dropna(subset=["Latitude", "Longitude"]) # Drop rows where coordinates couldn't be extracted

    df["geometry"] = gpd.points_from_xy(df["Longitude"], df["Latitude"])
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    return gdf

gdf = load_data()

# Sidebar filters
st.sidebar.header("Filter options")
year_options = gdf["Date Occurred"].str[:4].dropna().unique()
selected_year = st.sidebar.selectbox("Select Year", sorted(year_options, reverse=True))

# Filter data
gdf_filtered = gdf[gdf["Date Occurred"].str.startswith(selected_year)]

st.markdown(f"### Showing {len(gdf_filtered)} accidents from {selected_year}")

# Create map
m = folium.Map(location=[34.0522, -118.2437], zoom_start=11)
heat_data = [[row.geometry.y, row.geometry.x] for idx, row in gdf_filtered.iterrows()]
HeatMap(heat_data, radius=8).add_to(m)

folium_static(m, width=1000, height=600)

# Optional: show data table
if st.checkbox("Show raw data"):
    st.dataframe(gdf_filtered[["Date Occurred", "Time Occurred", "Location", "Hit and Run"]])
    
st.sidebar.header("Time-based analysis")
time_option = st.sidebar.selectbox("Select Time Analysis", ["None", "Year", "Month", "Day of Week", "Hour of Day"])

if time_option == "Year":
    accidents_by_year = gdf_filtered["Date Occurred"].str[:4].value_counts().sort_index()
    st.subheader("Number of Accidents by Year")
    st.bar_chart(accidents_by_year)

elif time_option == "Month":
    gdf_filtered["Month"] = pd.to_datetime(gdf_filtered["Date Occurred"]).dt.month_name()
    accidents_by_month = gdf_filtered["Month"].value_counts().reindex(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
    st.subheader("Number of Accidents by Month")
    st.bar_chart(accidents_by_month)

elif time_option == "Day of Week":
    gdf_filtered["Day of Week"] = pd.to_datetime(gdf_filtered["Date Occurred"]).dt.day_name()
    accidents_by_day = gdf_filtered["Day of Week"].value_counts().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    st.subheader("Number of Accidents by Day of Week")
    st.bar_chart(accidents_by_day)

elif time_option == "Hour of Day":
    # Convert 'Time Occurred' to string and pad with leading zero if necessary
    time_series = gdf_filtered["Time Occurred"].astype(str).str.zfill(4)
    # Attempt to convert to datetime, setting errors='coerce' to handle invalid formats
    gdf_filtered["Hour"] = pd.to_datetime(time_series, format='%H%M', errors='coerce').dt.hour.fillna(-1).astype(int)
    accidents_by_hour = gdf_filtered[gdf_filtered["Hour"] != -1]["Hour"].value_counts().sort_index()
    st.subheader("Number of Accidents by Hour of Day")
    st.bar_chart(accidents_by_hour)
    

st.subheader("Number of Accidents by Area")
accidents_by_area = gdf_filtered["Area Name"].value_counts().sort_values(ascending=False)
st.bar_chart(accidents_by_area)

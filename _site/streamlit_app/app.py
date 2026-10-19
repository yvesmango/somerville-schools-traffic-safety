# streamlit_app/app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import requests
import json
import os
from io import BytesIO


# Page configuration
st.set_page_config(
    page_title="Streamlit - SSTS",
    page_icon="🚸",
    layout="wide"
)

# Title and description
st.title("🏫 Somerville Schools Traffic Safety Map 🚸")
st.markdown("""
This interactive map shows school safety priority zones in Somerville, MA. 
**Hover over any colored buffer** to see detailed statistics for that school.
""")

# Load data with caching
@st.cache_data
def load_data():
    """Load all necessary GeoDataFrames."""

    # Base URL for your release
    base_url = "https://github.com/yvesmango/somerville-schools-traffic-safety/releases/download/v1.0-data-connx"
    
    
        # Helper function to load GeoJSON from URL
    def load_geojson_from_url(filename):
        url = f"{base_url}/{filename}"
        response = requests.get(url)
        response.raise_for_status()  # Check for errors
        return gpd.read_file(BytesIO(response.content))
    
    # Helper function to load CSV from URL
    def load_csv_from_url(filename):
        url = f"{base_url}/{filename}"
        return pd.read_csv(url)
    
    # Load all files
    buffers = load_geojson_from_url('school_buffers_complete_ranks.geojson')
    crashes = load_geojson_from_url('crashes_somerville_wgs84.geojson')
    boundary = load_geojson_from_url('somerville_boundary.geojson')
    schools = load_geojson_from_url('somerville_schools_ranks_wgs84.geojson')
    priority_df = load_csv_from_url('schools_traffic_priority_final.csv')
    
    return buffers, crashes, boundary, schools, priority_df

# Load data with progress indicator
with st.spinner("Loading spatial data..."):
    buffers, crashes, boundary, schools, priority_df = load_data()
st.success("✅ Data loaded successfully!")

# Create sidebar for controls and info
with st.sidebar:
    st.header("About")
    st.markdown("""
    This map displays school safety priority scores based on:
    - Crash data (2023-2025)
    - Traffic volume (AADT)
    
    **Color scale**: Green (🟢 = low priority, 🌕 = medium, 🔴 = high priority)
    """)
    
    st.header("Priority Rankings")
    st.dataframe(priority_df[['school_name', 'crashes_025mi', 'injury_pct', 'total_aadt', 'priority_score', 'rank',]])
    
    st.header("Instructions")
    st.markdown("""
    - **Hover** over colored buffers to see school details
    - Use layer control (top-right) to toggle layers
    - Zoom in/out to explore specific areas
    """)

# Create map
st.header("Interactive Priority Map")

# Calculate min/max for color scaling
min_score = buffers['priority_score'].min()
max_score = buffers['priority_score'].max()
mid_score = (min_score + max_score) / 2

# Function to get color based on priority score (Green → Yellow → Red)
def get_buffer_color(score):
    norm = (score - min_score) / (max_score - min_score)
    
    # Three-stop interpolation: Green (0,255,0) → Yellow (255,255,0) → Red (255,0,0)
    if norm <= 0.5:
        # Green to Yellow segment
        local_norm = norm * 2
        r = int(255 * local_norm)
        g = 255
        b = 0
    else:
        # Yellow to Red segment
        local_norm = (norm - 0.5) * 2
        r = 255
        g = int(255 * (1 - local_norm))
        b = 0
    
    return f'#{r:02x}{g:02x}{b:02x}'

# Add color column to buffers
buffers['fill_color'] = buffers['priority_score'].apply(get_buffer_color)


# Create base map
m = folium.Map(location=[42.3875, -71.0995], zoom_start=13, tiles='CartoDB Positron')

# Add boundary
folium.GeoJson(
    boundary,
    name="Somerville Boundary",
    style_function=lambda x: {
        'color': '#E39414',
        'weight': 3,
        'opacity': 0.5,
        'fill': False
    }
).add_to(m)

# Add crash points
folium.GeoJson(
    crashes,
    name="Crash Points",
    marker=folium.Circle(radius=7, fill_color="blue", fill_opacity=0.4, weight=1, color=None)
).add_to(m)


# Add schools
for idx, row in schools.iterrows():
    folium.RegularPolygonMarker(
        location=[row.geometry.y, row.geometry.x],
        number_of_sides=4,
        radius=6,
        rotation=45,
        color='black',
        fillColor='black',
        fillOpacity=1,
        weight=2).add_to(m)


folium.GeoJson(
    buffers,
    name="School Priority Buffers",
    style_function=lambda x: {
        'color': None,
        'weight': 1,
        'fillColor': get_buffer_color(x['properties']['priority_score']),
        'fillOpacity': 0.2
    },
    highlight_function=lambda x: {
        'color': 'white',
        'weight': 2,
        'fillOpacity': 0.4
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['school_name', 'rank', 'priority_score', 'crashes_025mi', 'total_aadt', 'avg_aadt', 'injury_pct'],
        aliases=['School:', 'Rank:', 'Priority Score:', 'Crashes:', 'Total AADT:', 'Avg. AADT:', 'Injury Rate Pct:'],
        localize=True,
        sticky=False
    )
).add_to(m)


st_folium(m, width=None, height=700)

# After the map, add a colorbar
st.markdown(f"""
<div style="display: flex; justify-content: center; margin: 10px 0;">
    <div style="display: flex; align-items: center; background: white; padding: 5px 15px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <span style="margin-right: 10px; font-weight: bold;">Priority Score:</span>
        <span style="color: #00ff00;">Low ({min_score:.0f})</span>
        <div style="width: 150px; height: 15px; background: linear-gradient(to right, #00ff00, #ffff00, #ff0000); margin: 0 10px; border-radius: 10px;"></div>
        <span style="color: #ff0000;">High ({max_score:.0f})</span>
    </div>
</div>
""", unsafe_allow_html=True)

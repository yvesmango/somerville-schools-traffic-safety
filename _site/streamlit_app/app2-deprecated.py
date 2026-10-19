# streamlit_app/app.py
import streamlit as st
import leafmap.foliumap as leafmap
import folium
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
    schools = load_geojson_from_url('somerville_schools_processed.geojson')
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
    - Injury severity
    
    **Color scale**: Green (🟢 = low priority, 🌕 = medium, 🔴 = high priority)
    """)
    
    st.header("Priority Rankings")
    st.dataframe(priority_df[['school_name', 'crashes_025mi', 'injury_pct', 'avg_aadt', 'priority_score', 'rank',]])
    
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

# Create map
m = leafmap.Map(center=[42.3875, -71.0995], zoom=13)

m.add_basemap('CartoDB.Positron')

# Add boundary
m.add_gdf(
    boundary,
    layer_name="Somerville Boundary",
    style={'color': '#E39414', 'weight': 3, 'opacity': 0.5, 'fill': False},
    info_mode=None
)

st.write("crashes CRS:", crashes.crs)

# # Add crashes
m.add_circle_markers_from_xy(
    crashes,
    x="X_Cooordinate",
    y="Y_Cooordinate",
    radius=1.5,
    color="red",
    fill_color="#1a58e8"

)


# Add buffers with dynamic coloring using style_callback
buffers_geojson = json.loads(buffers.to_json())

m.add_geojson(
    buffers_geojson,
    layer_name="School Priority Buffers",
    style_callback=lambda f: {
        'color': 'black',
        'weight': 1,
        'fillColor': f['properties']['fill_color'],
        'fillOpacity': 0.3
    },
    hover_style={
        'fillOpacity': 0.8,
        'weight': 1
    },
    info_mode='on_hover'  # This enables hover tooltips in leafmap
)

# Add schools
m.add_gdf(schools, layer_name="Schools",
          style={'color': 'purple', 'fillColor': 'white', 'radius': 8, 'weight': 2})


# Display the map using Streamlit
m.to_streamlit(height=700)

# Add some analysis below the map
st.header("Key Insights")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Crashes (2023-2025)", f"{len(crashes)}")
with col2:
    st.metric("Schools Analyzed", f"{len(schools)}")
with col3:
    st.metric("Priority Score Range", f"{min_score:.0f} - {max_score:.0f}")

# Show top 3 priority schools
st.subheader("Top Priority Schools")
top3 = priority_df.nlargest(3, 'priority_score')[['school_name', 'crashes_025mi', 'injury_pct', 'priority_score']]
st.dataframe(top3, width='stretch')
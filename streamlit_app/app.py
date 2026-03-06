# streamlit_app/app.py
import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import pandas as pd
import json
import os


# Page configuration
st.set_page_config(
    page_title="Somerville School Safety - Interactive Map",
    page_icon="🚸",
    layout="wide"
)

# Title and description
st.title("🚸 Somerville School Safety Interactive Map")
st.markdown("""
This interactive map shows school safety priority zones in Somerville, MA. 
**Hover over any colored buffer** to see detailed statistics for that school.
""")

# Load data with caching
@st.cache_data
def load_data():
    """Load all necessary GeoDataFrames."""
    # Adjust paths to go up one level from streamlit_app/
    data_processed = '../data/processed'
    
    # Load buffers with priority scores
    buffers = gpd.read_file(f'{data_processed}/school_buffers_025mi.geojson')
    
    # Load crashes
    crashes = gpd.read_file(f'{data_processed}/crashes_somerville_2023_2025_processed.geojson')
    
    # Load boundary
    boundary = gpd.read_file(f'{data_processed}/somerville_boundary.geojson')
    
    # Load schools with priority rankings
    schools = gpd.read_file(f'{data_processed}/somerville_schools_processed.geojson')
    
    # Load priority data (assuming you saved as CSV)
    priority_df = pd.read_csv('../outputs/school_safety_summary.csv')
    
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
    
    **Color scale**: Green (low priority) → Yellow → Red (high priority)
    """)
    
    st.header("Priority Rankings")
    st.dataframe(priority_df[['rank', 'school_name', 'crashes_025mi', 'injury_pct', 'priority_score']])
    
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

# Add boundary
m.add_gdf(
    boundary,
    layer_name="Somerville Boundary",
    style={'color': '#E39414', 'weight': 3, 'opacity': 0.5, 'fill': False}
)

# Add crashes
m.add_gdf(
    crashes,
    layer_name="Crashes (2023-2025)",
    style={'color': 'none', 'radius': 2, 'fillColor': '#3366cc', 
           'opacity': 0.5, 'fillOpacity': 0.6},
    hover_style={'fillColor': '#3366cc', 'fillOpacity': 0.2}
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
        'color': 'white',
        'fillOpacity': 0.6,
        'weight': 2
    },
    info_mode='on_hover'  # This enables hover tooltips in leafmap
)

# Add schools
m.add_gdf(
    schools,
    layer_name="Schools",
    style={'color': 'black', 'fillColor': 'white', 'radius': 8, 'weight': 2},
    tooltip=['school_name', 'rank', 'priority_score']
)

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
st.dataframe(top3, use_container_width=True)
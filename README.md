**[Home](https://yvesmango.github.io/) >> [Projects](https://yvesmango.github.io/projects) >>  Somerville Schools Traffic Safety**

# Somerville Schools Traffic Analysis

**Goal**: To identify and prioritize Somerville public schools for safety interventions by analyzing crash data and traffic volumes.

## Introduction

This project combines spatial analysis and data visualization to assess school zone safety. By integrating three years of crash records with traffic volume data, we developed a data-driven priority ranking for eight Somerville schools.

## Data Sources

- **Crash Data (2023-2025)** : Obtained from the MassDOT IMPACT portal, filtered to Somerville.
- **Traffic Volume Data (2024)** : Accessed via the MassDOT Road Inventory API (line segments with AADT).
- **School Locations**: Geocoded addresses for eight selected Somerville public schools.

## Methodology

1.  **Data Collection**: Downloaded crash data, pulled traffic data via API, and geocoded school addresses.
2.  **Spatial Analysis**: Created 0.25-mile school buffers and performed spatial joins to count crashes and sum traffic exposure per school.
3.  **Priority Ranking**: Developed a composite priority score weighting crash counts and total traffic volume (AADT) to rank schools.
4.  **Visualization**: Created static maps with Matplotlib and an interactive map with Leafmap.

## Key Findings

<details>
  <summary>🔍<strong><em> Click to reveal Key Findings</em></strong></summary>
  
  - **Winter Hill** and **East Somerville** schools are the top priorities due to high crash counts and traffic exposure.
  - **Healey School** has a high injury crash rate relative to its traffic, suggesting specific risks near I-93.
  - **Argenziano School** faces the highest total traffic volume from a dense street network.
  
</details>

## Outputs

- [Final Priority Map](./outputs/somerville_school_priority_final.png)
- [Interactive Priority Map](./outputs/somerville_school_priority_folium.html)
- [Crash vs. Traffic Combo Chart](./outputs/crashes_vs_traffic_total_aadt.png)

## Technologies Used

`Python`, `GeoPandas`, `Pandas`, `Matplotlib`, `Leafmap`, `Jupyter Notebooks`, `REST APIs`

## License

MIT License
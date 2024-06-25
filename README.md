# Streamlit App for Visualizing Disaster Risk Zones

## Overview

This Streamlit app visualizes disaster risk zones on a map. Users can input an address to see its location marked on the map. The app also displays risk zones from a CSV file and additional polygon data from multiple JSON files, each in different colors.

## Functionality

### User Input

- **Address Input**: Users can enter an address in the text input field. The app uses the Kakao Maps API to convert the address to latitude and longitude coordinates.
- **CSV Data**: The app reads a CSV file containing disaster risk zone data, including coordinates, area, and various risk-related attributes.
- **JSON Data**: The app reads multiple JSON files, each containing polygon coordinates and associated metadata (UID, PNU).

### Map Visualization

- **Folium Map**: The app uses the Folium library to create an interactive map. The map is centered based on the input address or the mean coordinates from the CSV data.
- **Markers and Polygons**: 
  - Markers are added to the map for the input address.
  - Circles are drawn for each disaster risk zone in the CSV file, with popup information detailing the risk attributes.
  - Polygons from the JSON files are displayed in different colors, with popup information showing UID and PNU.

### Data Visualization

- **Risk Area Grades Plot**: A bar plot shows the count of disaster risk zones by type and grade, providing a visual summary of the risk distribution.

## Code Explanation

### Importing Libraries

```python
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import folium
import json
from pyproj import Transformer
from streamlit_folium import folium_static
import requests
```
- **pandas**: For reading and manipulating CSV data.
- **matplotlib.pyplot**: For creating plots.
- **streamlit**: For building the web application.
- **folium**: For creating interactive maps.
- **json**: For handling JSON data.
- **pyproj**: For transforming coordinates.
- **requests**: For making HTTP requests to the Kakao Maps API.
- **streamlit_folium**: For integrating Folium maps with Streamlit.

### Functions

#### `lat_long`

This function takes an address and a REST API key as input and returns the latitude and longitude of the address using the Kakao Maps API.

```python
def lat_long(address, rest_api_key):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
    headers = {"Authorization": "KakaoAK " + rest_api_key}
    try:
        response = requests.get(url, headers=headers)
        json_result = response.json()
        address_xy = json_result['documents'][0]['address']
        return float(address_xy['x']), float(address_xy['y'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None
```

#### `mark_address_on_map`

This function marks a given address on the map by adding a Folium marker at the latitude and longitude obtained from `lat_long`.

```python
def mark_address_on_map(address, folium_map, rest_api_key):
    x, y = lat_long(address, rest_api_key)
    if x is None or y is None:
        st.error("Failed to get coordinates for the address.")
        return

    folium.Marker([y, x], popup=address).add_to(folium_map)
    st.success("Address marker has been added to the map.")
```

### Streamlit UI Setup

#### Title and Address Input

```python
st.title("재해위험지구 지도시각화 sample")
address = st.text_input("주소지를 입력해주세요:")
```

#### Loading CSV Data

```python
csv_file_path = './data/crisis_address(utf-8).csv'
df = pd.read_csv(csv_file_path)
```

#### Color Map for Circle Markers

```python
color_map = {
    1: 'blue',
    2: 'purple',
    3: 'gray',
    4: 'orange',
    5: 'green',
    6: 'darkblue'
}
```

#### Map Initialization

The map is centered at the address coordinates if provided, otherwise at the mean coordinates from the CSV data.

```python
if address:
    address_x, address_y = lat_long(address, rest_api_key)
else:
    address_x, address_y = df['x'].mean(), df['y'].mean()

m = folium.Map(location=[address_y, address_x], zoom_start=15 if address else 8)
```

#### Adding Circles from CSV Data

Each row in the CSV file represents a risk zone. Circles are drawn on the map with attributes displayed in popups.

```python
for i, row in df.iterrows():
    if pd.notnull(row['y']) and pd.notnull(row['x']) and pd.notnull(row['DSGN_AREA']):
        popup_content = f"""
        <b>재해위험지구관리번호:</b> {row['DST_RSK_DSTRCT_NM']}<br>
        <b>재해위험지구등급코드:</b> {row['DST_RSK_DSTRCT_GRD_CD']}<br>
        <b>재해위험지구유형코드:</b> {row['DST_RSK_DSTRCT_TYPE_CD']}<br>
        <b>재해위험지구코드:</b> {row['DST_RSK_DSTRCTCD']}<br>
        <b>재해위험지구지역코드:</b> {row['DST_RSK_DSTRCT_RGN_CD']}<br>
        <b>시설명:</b> {row['FCLT_NM']}<br>
        <b>지정일자:</b> {row['DSGN_YMD']}<br>
        <b>지정사유:</b> {row['DSGN_RSN']}
        """
        popup = folium.Popup(popup_content, max_width=300)
        
        radius = (row['DSGN_AREA'] ** 0.5)
        color = color_map.get(row['DST_RSK_DSTRCT_TYPE_CD'], 'red')
        
        folium.Circle(
            location=[row['y'], row['x']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=popup
        ).add_to(m)
```

#### Adding Address Marker

If an address is provided, it is marked on the map.

```python
if address:
    mark_address_on_map(address, m, rest_api_key)
```

### Adding Polygons from JSON Files

The app reads multiple JSON files, transforms the coordinates, and adds polygons to the map with different colors.

```python
json_files = [
    {'path': './data/충청북도_보은읍_이평리.json', 'color': 'blue'},
    # Add paths for your other JSON files here
    # {'path': '/path/to/your/second_file.json', 'color': 'green'},
    # {'path': '/path/to/your/third_file.json', 'color': 'red'},
    # {'path': '/path/to/your/fourth_file.json', 'color': 'purple'},
    # {'path': '/path/to/your/fifth_file.json', 'color': 'orange'}
]

# Initialize the coordinate transformer (example: from EPSG:5179 to EPSG:4326)
transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326")

# Process each JSON file
for file_info in json_files:
    with open(file_info['path'], encoding='utf-8') as f:
        data = json.load(f)

    # Extract the coordinates from the JSON data and convert them to lat/lon
    coordinates_list = []
    for item in data['output']['farmmapData']['data']:
        polygon_info = {
            'uid': item['uid'],
            'pnu': item['pnu'],
            'coordinates': []
        }
        for geometry in item['geometry']:
            coordinates = [(transformer.transform(coord['y'], coord['x'])) for coord in geometry['xy']]
            polygon_info['coordinates'].append(coordinates)
        coordinates_list.append(polygon_info)

    # Add polygons to the map with popup info and different colors
    for polygon_info in coordinates_list:
        for coordinates in polygon_info['coordinates']:
            folium.Polygon(
                locations=coordinates, 
                color=file_info['color'], 
                weight=2, 
                fill=True, 
                fill_color=file_info['color'],
                popup=f"UID: {polygon_info['uid']}<br>PNU: {polygon_info['pnu']}"
            ).add_to(m)
```

### Displaying the Map

The Folium map is displayed in the Streamlit app.

```python
folium_static(m)
```

### Plotting Risk Area Grades

A bar plot shows the count of disaster risk zones by type and grade.

```python
def plot_risk_area_grades(df):
    import matplotlib.pyplot as plt
    
    grouped = df.groupby(['DST_RSK_DSTRCT_TYPE_CD', 'DST_RSK_DSTRCT_GRD_CD']).size().reset_index(name='count')

    pivot_table = grouped.pivot(index='DST_RSK_DSTRCT_TYPE_CD', columns='DST_RSK_DSTRCT_GRD_CD', values='

count')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_table.plot(kind='bar', ax=ax)
    ax.set_title('재해위험지구 유형에 따른 재해 등급')
    ax.set_xlabel('DST_RSK_DSTRCT_GRD_CD')
    ax.set_ylabel('Count')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    st.pyplot(fig)

plot_risk_area_grades(df)
```

---

This document explains the functionality and the steps involved in creating the Streamlit app. The app visualizes disaster risk zones on a map with interactive features, allowing users to see detailed information about each risk zone.
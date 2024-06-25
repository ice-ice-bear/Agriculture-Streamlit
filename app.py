import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import folium
import json
from pyproj import Transformer
from streamlit_folium import folium_static
import requests

# Function to get latitude and longitude from an address
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

# Function to mark an address on the map
def mark_address_on_map(address, folium_map, rest_api_key):
    x, y = lat_long(address, rest_api_key)
    if x is None or y is None:
        st.error("Failed to get coordinates for the address.")
        return

    folium.Marker([y, x], popup=address).add_to(folium_map)
    st.success("Address marker has been added to the map.")

# Streamlit UI
st.title("재해위험지구 지도시각화 sample")

address = st.text_input("주소지를 입력해주세요:")


rest_api_key = 'bf0070cbed9ecd623aeead721c91397b'

# Load CSV data
csv_file_path = './data/crisis_address(utf-8).csv'
df = pd.read_csv(csv_file_path)

color_map = {
    1: 'blue',
    2: 'purple',
    3: 'gray',
    4: 'orange',
    5: 'green',
    6: 'darkblue'
}

if address:
    address_x, address_y = lat_long(address, rest_api_key)
else:
    address_x, address_y = df['x'].mean(), df['y'].mean()

m = folium.Map(location=[address_y, address_x], zoom_start=15 if address else 8)

# Add circles from CSV data
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

if address:
    mark_address_on_map(address, m, rest_api_key)

# Adding polygons from JSON files
json_files = [
    {'path': './data/전라남도_나주시_노안면_학산리_논.json', 'color': 'yellow'},
    {'path': './data/전라남도_나주시_노안면_학산리_밭.json', 'color': 'green'},
    {'path': './data/전라남도_나주시_노안면_학산리_과수.json', 'color': 'red'},
    {'path': './data/전라남도_나주시_노안면_학산리_비경지.json', 'color': 'brown'},
    {'path': './data/전라남도_나주시_노안면_학산리_시설', 'color': 'gray'}
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

# Display the map in the Streamlit app
folium_static(m)

def plot_risk_area_grades(df):
    import matplotlib.pyplot as plt

    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    grouped = df.groupby(['DST_RSK_DSTRCT_TYPE_CD', 'DST_RSK_DSTRCT_GRD_CD']).size().reset_index(name='count')

    pivot_table = grouped.pivot(index='DST_RSK_DSTRCT_TYPE_CD', columns='DST_RSK_DSTRCT_GRD_CD', values='count')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_table.plot(kind='bar', ax=ax)
    ax.set_title('재해위험지구 유형에 따른 재해 등급')
    ax.set_xlabel('DST_RSK_DSTRCT_GRD_CD')
    ax.set_ylabel('Count')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    st.pyplot(fig)

plot_risk_area_grades(df)

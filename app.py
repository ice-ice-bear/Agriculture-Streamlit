import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import streamlit as st
import folium
import json
from pyproj import Transformer
from streamlit_folium import folium_static
import requests
import platform

# # Base URL for the financial records API
# base_url = 'http://localhost:8080/api/financial-records'

# # Add record
# def add_record_page():
#     st.subheader("수입 및 지출 기록 추가")
#     record_type = st.selectbox("유형", ("income", "expense"))
#     category = st.text_input("카테고리")
#     amount = st.number_input("금액", min_value=0.0, format="%.2f")
#     date = st.date_input("날짜", datetime.date.today())
#     description = st.text_area("설명")
#     if st.button("추가"):
#         record = {
#             "type": record_type,
#             "category": category,
#             "amount": amount,
#             "date": date.isoformat(),
#             "description": description
#         }
#         response = requests.post(base_url, json=record)
#         if response.status_code == 201:
#             st.success("기록이 추가되었습니다.")
#         else:
#             st.error("기록 추가 실패")

# add_record_page()

# # View
# def view_records_page():
#     st.subheader("기록 조회")
#     start_date = st.date_input("시작 날짜", datetime.date.today() - datetime.timedelta(days=30))
#     end_date = st.date_input("종료 날짜", datetime.date.today())
#     if st.button("조회"):
#         response = requests.get(base_url, params={"startDate": start_date.isoformat(), "endDate": end_date.isoformat()})
#         if response.status_code == 200:
#             records = response.json()
#             df = pd.DataFrame(records)
#             st.dataframe(df)
#         else:
#             st.error("기록 조회 실패")

# view_records_page()

# # Update
# def update_record_page():
#     st.subheader("기록 수정")
#     record_id = st.number_input("기록 ID", min_value=1)
#     record_type = st.selectbox("유형", ("income", "expense"))
#     category = st.text_input("카테고리")
#     amount = st.number_input("금액", min_value=0.0, format="%.2f")
#     date = st.date_input("날짜", datetime.date.today())
#     description = st.text_area("설명")
#     if st.button("수정"):
#         record = {
#             "type": record_type,
#             "category": category,
#             "amount": amount,
#             "date": date.isoformat(),
#             "description": description
#         }
#         response = requests.put(f"{base_url}/{record_id}", json=record)
#         if response.status_code == 200:
#             st.success("기록이 수정되었습니다.")
#         else:
#             st.error("기록 수정 실패")

# update_record_page()

# # Delete
# def delete_record_page():
#     st.subheader("기록 삭제")
#     record_id = st.number_input("기록 ID", min_value=1)
#     if st.button("삭제"):
#         response = requests.delete(f"{base_url}/{record_id}")
#         if response.status_code == 204:
#             st.success("기록이 삭제되었습니다.")
#         else:
#             st.error("기록 삭제 실패")

# delete_record_page()

# Load Korean font
# font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_path ='./Fonts/NanumGothic.ttf'
font_name = fm.FontProperties(fname=font_path).get_name()
plt.rc('font', family=font_name)

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

address = st.text_input("주소지를 입력해주세요:", value='전남 나주시 노안면 학산길 70-17')


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
    {'path': './data/전라남도_나주시_노안면_학산리_시설.json', 'color': 'gray'}
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

    # Set the font family globally
    # plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    grouped = df.groupby(['DST_RSK_DSTRCT_TYPE_CD', 'DST_RSK_DSTRCT_GRD_CD']).size().reset_index(name='count')

    pivot_table = grouped.pivot(index='DST_RSK_DSTRCT_TYPE_CD', columns='DST_RSK_DSTRCT_GRD_CD', values='count')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_table.plot(kind='bar', ax=ax)
    st.title("재해위험지구 유형에 따른 재해 등급")
    ax.set_xlabel('DST_RSK_DSTRCT_GRD_CD')
    ax.set_ylabel('Count')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    st.pyplot(fig)

def make_additional_plot(df):
    # Count of districts by grade code
    grade_count = df['DST_RSK_DSTRCT_GRD_CD'].value_counts().reset_index()
    grade_count.columns = ['Grade Code', 'Count']

    # Count of districts by type code
    type_count = df['DST_RSK_DSTRCT_TYPE_CD'].value_counts().reset_index()
    type_count.columns = ['Type Code', 'Count']

    # Designation reasons and their counts
    designation_reasons_count = df['DSGN_RSN'].value_counts().reset_index()
    designation_reasons_count.columns = ['Designation Reason', 'Count']

    # Total designation area by district
    total_designation_area = df.groupby('DST_RSK_DSTRCT_NM')['DSGN_AREA'].sum().reset_index()
    total_designation_area.columns = ['District Name', 'Total Designation Area']

    # Risk factor content grouped by district
    risk_factor_content = df.groupby('DST_RSK_DSTRCT_NM')['RSK_FACTR_CN'].apply(lambda x: ' | '.join(x.dropna())).reset_index()
    risk_factor_content.columns = ['District Name', 'Risk Factor Content']

    # Streamlit app
    st.title("기타 재해위험 지구정보")

    st.header("재해등급 코드 빈도")
    fig1, ax1 = plt.subplots()
    ax1.pie(grade_count['Count'], labels=grade_count['Grade Code'], autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig1)
    
    st.header("유형 코드별 재해 지구 수")
    fig2, ax2 = plt.subplots()
    sns.histplot(data=type_count, x='Type Code', weights='Count', bins=range(1, 8), kde=False, ax=ax2)
    st.pyplot(fig2)

    st.header("재해 위험지구 지정사유 및 빈도")
    st.dataframe(designation_reasons_count)
    # fig3, ax3 = plt.subplots()
    # sns.boxplot(y='Designation Reason', x='Count', data=designation_reasons_count, ax=ax3)
    # st.pyplot(fig3)
    
    st.header("지구별 총 지정 면적")
    st.dataframe(total_designation_area)
    # fig4, ax4 = plt.subplots()
    # sns.scatterplot(x='Total Designation Area', y='District Name', data=total_designation_area, ax=ax4)
    # st.pyplot(fig4)

    st.header("지역별 그룹화된 위험 요인")
    st.dataframe(risk_factor_content)


plot_risk_area_grades(df)

make_additional_plot(df)

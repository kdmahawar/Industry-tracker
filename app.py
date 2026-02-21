import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

# ऐप की सेटिंग
st.set_page_config(page_title="Advance Industry Visit Tracker", layout="wide")

st.title("🏭 एडवांस इंडस्ट्री विजिट ट्रैकर (Industry Visit Tracker)")

ORIGINAL_FILE = "Merged_T7_Customer_List.xlsx"
SAVED_FILE = "Updated_Customer_List.csv" 

# डेटा लोड करने का फंक्शन
@st.cache_data
def load_data():
    if os.path.exists(SAVED_FILE):
        df = pd.read_csv(SAVED_FILE)
    else:
        df = pd.read_excel(ORIGINAL_FILE, engine='openpyxl')
        
        if 'Visited' not in df.columns:
            df['Visited'] = False
        if 'New Remarks' not in df.columns:
            df['New Remarks'] = ""
            
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    return df

df = load_data()

# --- साइडबार (Sidebar) में फ़िल्टर ---
st.sidebar.header("🔍 विजिट की प्लानिंग करें")

if 'District' in df.columns:
    district_list = ["All"] + list(df['District'].dropna().unique())
    selected_district = st.sidebar.selectbox("ज़िला चुनें (District):", district_list)
else:
    selected_district = "All"

if 'Priority' in df.columns:
    priority_list = ["All"] + list(df['Priority'].dropna().unique())
    selected_priority = st.sidebar.selectbox("प्राथमिकता चुनें (Priority):", priority_list)
else:
    selected_priority = "All"

filtered_df = df.copy()
if selected_district != "All" and 'District' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
if selected_priority != "All" and 'Priority' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]

# --- डैशबोर्ड और आंकड़े ---
st.markdown("### 📊 आपकी प्रोग्रेस (Progress)")
total_industries = len(filtered_df)
visited_count = int(filtered_df['Visited'].sum())
pending_count = total_industries - visited_count

col1, col2, col3 = st.columns(3)
col1.metric("कुल इंडस्ट्रीज (Total)", total_industries)
col2.metric("विजिट हो गई (Visited)", visited_count)
col3.metric("बाकी हैं (Pending)", pending_count)

st.divider()

# --- एडवांस मैप (Map) दिखाना ---
st.markdown("### 🗺️ एडवांस इंडस्ट्री लोकेशन मैप")
st.caption("नक्शे में किसी भी पिन (Pin) पर क्लिक करें और कंपनी की जानकारी देखें। हरा पिन = विजिट हो गई, लाल पिन = बाकी है।")

if 'Latitude' in filtered_df.columns and 'Longitude' in filtered_df.columns:
    map_data = filtered_df.dropna(subset=['Latitude', 'Longitude'])
    
    if not map_data.empty:
        # मैप का बीच का हिस्सा तय करना
        center_lat = map_data['Latitude'].mean()
        center_lon = map_data['Longitude'].mean()
        
        # मैप बनाना
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        
        # हर कंपनी के लिए एक पिन (Marker) लगाना
        for index, row in map_data.iterrows():
            # रंग तय करना
            marker_color = "green" if row['Visited'] else "red"
            
            # पॉपअप बॉक्स में क्या लिखा होगा, वो सेट करना
            popup_text = f"""
            <div style="font-family: Arial; font-size: 14px; min-width: 200px;">
                <b>🏢 कंपनी:</b> {row['CD Name']}<br>
                <b>📍 ज़िला:</b> {row['District']}<br>
                <b>⭐ प्राथमिकता:</b> {row['Priority']}<br>
                <b>📝 स्टेटस:</b> {'✅ विजिट हो गई' if row['Visited'] else '❌ विजिट बाकी है'}
            </div>
            """
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=row['CD Name'],
                icon=folium.Icon(color=marker_color, icon="info-sign")
            ).add_to(m)
        
        # ऐप में मैप को दिखाना
        st_folium(m, width="100%", height=400, returned_objects=[])
    else:
        st.info("इस फ़िल्टर के लिए लोकेशन डेटा उपलब्ध नहीं है।")
else:
    st.info("आपके डेटा में लोकेशन (Latitude/Longitude) नहीं है।")

st.divider()

# --- विजिट अपडेट और रिमार्क्स ---
st.markdown("### 📝 विजिट अपडेट करें और रिमार्क्स लिखें")

edited_df = st.data_editor(
    filtered_df,
    column_config={
        "Visited": st.column_config.CheckboxColumn("विजिट हो गई? (Tick)"),
        "New Remarks": st.column_config.TextColumn("मैनेजर/ओनर के रिमार्क्स"),
        "CD Name": st.column_config.TextColumn("कंपनी का नाम", disabled=True),
        "District": st.column_config.TextColumn("ज़िला", disabled=True),
        "Priority": st.column_config.TextColumn("प्राथमिकता", disabled=True),
        "Mobile Number": st.column_config.TextColumn("मोबाइल नंबर", disabled=True)
    },
    disabled=["Custcd", "CD Name", "District", "Zone", "Ind Type", "Mobile Number", "Priority"], 
    hide_index=True,
    use_container_width=True
)

# --- सेव और डाउनलोड बटन ---
col_save, col_download = st.columns(2)

with col_save:
    if st.button("💾 बदलाव सेव करें (Save Changes)", use_container_width=True):
        if 'Custcd' in df.columns:
            df.set_index('Custcd', inplace=True)
            edited_df_index = edited_df.set_index('Custcd')
            df.update(edited_df_index)
            df.reset_index(inplace=True)
        else:
            df.update(edited_df)
            
        df.to_csv(SAVED_FILE, index=False)
        st.success("✅ डेटा सफलतापूर्वक सेव हो गया है!")
        st.cache_data.clear()

with col_download:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 अपडेटेड लिस्ट डाउनलोड करें (Download CSV)",
        data=csv,
        file_name='Final_Updated_Customer_List.csv',
        mime='text/csv',
        use_container_width=True
    )
    

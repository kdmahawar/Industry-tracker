import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

# App settings
st.set_page_config(page_title="Advance Industry Visit Tracker", layout="wide")

st.title("🏭 Advance Industry Visit Tracker")

ORIGINAL_FILE = "Merged_T7_Customer_List.xlsx"
SAVED_FILE = "Updated_Customer_List.csv" 

# Function to load data
@st.cache_data
def load_data():
    # Load previously saved data if available
    if os.path.exists(SAVED_FILE):
        df = pd.read_csv(SAVED_FILE)
    else:
        # Otherwise load the original excel file
        df = pd.read_excel(ORIGINAL_FILE, engine='openpyxl')
        
        # Create new columns if they don't exist
        if 'Visited' not in df.columns:
            df['Visited'] = False
        if 'New Remarks' not in df.columns:
            df['New Remarks'] = ""
            
    # Convert Latitude and Longitude to numeric values for mapping
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Plan Your Visit")

# District Filter
if 'District' in df.columns:
    district_list = ["All"] + list(df['District'].dropna().unique())
    selected_district = st.sidebar.selectbox("Select District:", district_list)
else:
    selected_district = "All"

# Priority Filter
if 'Priority' in df.columns:
    priority_list = ["All"] + list(df['Priority'].dropna().unique())
    selected_priority = st.sidebar.selectbox("Select Priority:", priority_list)
else:
    selected_priority = "All"

# Apply Filters
filtered_df = df.copy()
if selected_district != "All" and 'District' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
if selected_priority != "All" and 'Priority' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]

# --- Dashboard and Stats ---
st.markdown("### 📊 Your Progress")
total_industries = len(filtered_df)
visited_count = int(filtered_df['Visited'].sum())
pending_count = total_industries - visited_count

col1, col2, col3 = st.columns(3)
col1.metric("Total Industries", total_industries)
col2.metric("Visited", visited_count)
col3.metric("Pending", pending_count)

st.divider()

# --- Advanced Map ---
st.markdown("### 🗺️ Advanced Industry Location Map")
st.caption("Click on any pin on the map to view complete company details. Green = Visited, Red = Pending.")

if 'Latitude' in filtered_df.columns and 'Longitude' in filtered_df.columns:
    map_data = filtered_df.dropna(subset=['Latitude', 'Longitude'])
    
    if not map_data.empty:
        # Center of the map
        center_lat = map_data['Latitude'].mean()
        center_lon = map_data['Longitude'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
        
        # Adding markers
        for index, row in map_data.iterrows():
            marker_color = "green" if row['Visited'] else "red"
            
            # Handling blank data
            survey_remarks = row.get('Survey Remarks', '')
            if pd.isna(survey_remarks): survey_remarks = "-"
            
            total_a = row.get('Total_A', '0')
            if pd.isna(total_a): total_a = "0"
            
            total_b = row.get('Total_B', '0')
            if pd.isna(total_b): total_b = "0"
            
            total_l = row.get('Total_L', '0')
            if pd.isna(total_l): total_l = "0"

            # Popup box details
            popup_text = f"""
            <div style="font-family: Arial; font-size: 14px; min-width: 250px;">
                <b>🏢 Company:</b> {row['CD Name']}<br>
                <b>📍 District:</b> {row['District']}<br>
                <b>⭐ Priority:</b> {row['Priority']}<br>
                <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
                <b>💬 Survey Remarks:</b> {survey_remarks}<br>
                <b>📦 Total A:</b> {total_a}<br>
                <b>📦 Total B:</b> {total_b}<br>
                <b>📦 Total L:</b> {total_l}<br>
                <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
                <b>📝 Status:</b> {'✅ Visited' if row['Visited'] else '❌ Pending'}
            </div>
            """
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_text, max_width=350),
                tooltip=row['CD Name'],
                icon=folium.Icon(color=marker_color, icon="info-sign")
            ).add_to(m)
        
        st_folium(m, width="100%", height=400, returned_objects=[])
    else:
        st.info("Location data is not available for this filter.")
else:
    st.info("Location (Latitude/Longitude) data is missing in your file.")

st.divider()

# --- Visit Update and Remarks ---
st.markdown("### 📝 Update Visit and Add Remarks")

# Editable Dataframe
edited_df = st.data_editor(
    filtered_df,
    column_config={
        "Visited": st.column_config.CheckboxColumn("Visited? (Tick)"),
        "New Remarks": st.column_config.TextColumn("Manager/Owner Remarks"),
        "CD Name": st.column_config.TextColumn("Company Name", disabled=True),
        "District": st.column_config.TextColumn("District", disabled=True),
        "Priority": st.column_config.TextColumn("Priority", disabled=True),
        "Mobile Number": st.column_config.TextColumn("Mobile Number", disabled=True)
    },
    disabled=["Custcd", "CD Name", "District", "Zone", "Ind Type", "Mobile Number", "Priority", "Survey Remarks", "Total_A", "Total_B", "Total_L"], 
    hide_index=True,
    use_container_width=True
)

# --- Save and Download Buttons ---
col_save, col_download = st.columns(2)

with col_save:
    if st.button("💾 Save Changes", use_container_width=True):
        # Error-free update method
        df.update(edited_df)
            
        # Save to CSV
        df.to_csv(SAVED_FILE, index=False)
        st.success("✅ Data saved successfully!")
        st.cache_data.clear()
        st.rerun()

with col_download:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Updated CSV",
        data=csv,
        file_name='Final_Updated_Customer_List.csv',
        mime='text/csv',
        use_container_width=True
    )

# --- Footer ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 16px; font-weight: bold;'>Created by K D Mahawar</p>", unsafe_allow_html=True)

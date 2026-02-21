import streamlit as st
import pandas as pd
import os

# ऐप की सेटिंग
st.set_page_config(page_title="Advance Industry Visit Tracker", layout="wide")

st.title("🏭 एडवांस इंडस्ट्री विजिट ट्रैकर (Industry Visit Tracker)")

# आपकी एक्सेल फाइल का नाम (ध्यान दें, यहाँ .xlsx कर दिया गया है)
ORIGINAL_FILE = "Merged_T7_Customer_List.xlsx"
# हम सेव करने के लिए CSV का ही इस्तेमाल करेंगे ताकि डेटा तेजी से लोड हो सके
SAVED_FILE = "Updated_Customer_List.csv" 

# डेटा लोड करने का फंक्शन
@st.cache_data
def load_data():
    # अगर हमने पहले कोई डेटा सेव किया है, तो उसे पढ़ें
    if os.path.exists(SAVED_FILE):
        df = pd.read_csv(SAVED_FILE)
    else:
        # अगर सेव नहीं किया है, तो आपकी ओरिजिनल एक्सेल फाइल पढ़ें
        # एक्सेल फाइल पढ़ने के लिए engine='openpyxl' का उपयोग किया जाता है
        df = pd.read_excel(ORIGINAL_FILE, engine='openpyxl')
        
        # अगर ये कॉलम नहीं हैं तो नए बना लें
        if 'Visited' not in df.columns:
            df['Visited'] = False
        if 'New Remarks' not in df.columns:
            df['New Remarks'] = ""
            
    # लोकेशन (Latitude/Longitude) को मैप के लिए सही फॉर्मेट में बदलना
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    return df

df = load_data()

# --- साइडबार (Sidebar) में फ़िल्टर ---
st.sidebar.header("🔍 विजिट की प्लानिंग करें")

# ज़िले (District) के हिसाब से फ़िल्टर (अगर आपके डेटा में District है)
if 'District' in df.columns:
    district_list = ["All"] + list(df['District'].dropna().unique())
    selected_district = st.sidebar.selectbox("ज़िला चुनें (District):", district_list)
else:
    selected_district = "All"

# प्रायोरिटी (Priority) के हिसाब से फ़िल्टर (अगर आपके डेटा में Priority है)
if 'Priority' in df.columns:
    priority_list = ["All"] + list(df['Priority'].dropna().unique())
    selected_priority = st.sidebar.selectbox("प्राथमिकता चुनें (Priority):", priority_list)
else:
    selected_priority = "All"

# डेटा को फ़िल्टर करना
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

# --- मैप (Map) दिखाना ---
st.markdown("### 🗺️ इंडस्ट्री लोकेशन मैप")
if 'Latitude' in filtered_df.columns and 'Longitude' in filtered_df.columns:
    map_data = filtered_df.dropna(subset=['Latitude', 'Longitude'])
    if not map_data.empty:
        st.map(map_data, latitude='Latitude', longitude='Longitude', color="#00ff00" if visited_count > 0 else "#ff0000")
    else:
        st.info("इस फ़िल्टर के लिए लोकेशन डेटा उपलब्ध नहीं है।")
else:
    st.info("आपके डेटा में लोकेशन (Latitude/Longitude) नहीं है।")

st.divider()

# --- विजिट अपडेट और रिमार्क्स ---
st.markdown("### 📝 विजिट अपडेट करें और रिमार्क्स लिखें")

# डेटा एडिटर (यहाँ आप अपनी जरूरत के अनुसार कॉलम इनेबल/डिसएबल कर सकते हैं)
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
        # मूल डेटा को अपडेट करना
        if 'Custcd' in df.columns:
            df.set_index('Custcd', inplace=True)
            edited_df_index = edited_df.set_index('Custcd')
            df.update(edited_df_index)
            df.reset_index(inplace=True)
        else:
            df.update(edited_df)
            
        # डेटा को सुरक्षित (Save) करना
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
  

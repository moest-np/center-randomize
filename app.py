import folium
import subprocess
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from utils.pretty import pretty_dataframe, custom_map_zoom, custom_map_tooltip
from utils.temp_files import saved_uploads


#Page Setup
st.set_page_config(
   page_title="MOEST Exam Center Calculator",
   page_icon=":school:",
#    page_icon="https://avatars.githubusercontent.com/u/167545222?s=200&v=4", # official logo
   layout="wide",
   initial_sidebar_state="expanded",
)

#  Custom CSS 
custom_css = """
<style>
.st-ag.st-e4.st-e5 {
    flex-direction: row !important;
}
</style>
"""

# Render custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Session setup
if 'calculate_clicked' not in st.session_state:
    st.session_state.calculate_clicked = False
if 'calculation_completed' not in st.session_state:
    st.session_state.calculation_completed = False
if 'calculated_data' not in st.session_state:
    st.session_state.calculated_data = {}
if 'filter_type' not in st.session_state:
    st.session_state.filter_type = None
if 'filter_value' not in st.session_state:
    st.session_state.filter_value = None

#Sidebar
with st.sidebar:
    add_side_header = st.sidebar.title("Random Center Calculator")
    
    schools_file = st.sidebar.file_uploader("Upload School/College file", type="tsv")
    centers_file = st.sidebar.file_uploader("Upload Centers file", type="tsv")
    prefs_file = st.sidebar.file_uploader("Upload Preferences file", type="tsv")

    calculate = st.sidebar.button("Calculate Centers", type="primary", use_container_width=True)

school_df = None
divider_color = "red"
# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 School Center",
    "🚌 School Center Distance",
    "🏫 View School Data",
    "📍 View Centers Data",
    "🧮 View Pref Data" 
    ])

tab1.subheader("School Center", divider=divider_color)
tab2.subheader("School Center Distance", divider=divider_color)
tab3.subheader("School Data", divider=divider_color)
tab4.subheader("Center Data", divider=divider_color)
tab5.subheader("Pref Data", divider=divider_color)

# Show data in Tabs as soon as the files are uploaded
if schools_file:
    df = pd.read_csv(schools_file, sep="\t")
    school_df = df
    tab3.dataframe(pretty_dataframe(df), use_container_width=True)
    
else:
    tab3.info("Upload data to view it.", icon="ℹ️")

if centers_file:
    df = pd.read_csv(centers_file, sep="\t")
    tab4.dataframe(pretty_dataframe(df), use_container_width=True)
else:
    tab4.info("Upload data to view it.", icon="ℹ️")

if prefs_file:
    df = pd.read_csv(prefs_file, sep="\t")
    tab5.dataframe(pretty_dataframe(df), use_container_width=True)
else:
    tab5.info("Upload data to view it.", icon="ℹ️")


# Function to run the center randomizer program
def run_center_randomizer(schools_tsv, centers_tsv, prefs_tsv):
    cmd = f"python school_center.py {schools_tsv} {centers_tsv} {prefs_tsv}"
    subprocess.run(cmd, shell=True)

#Function to filter the data
def filter_data(df, filter_type, filter_value):
    if filter_type in df.columns:
        df = df[df[filter_type] == filter_value]
        return df
    else:
        st.error(f"{filter_type} is not a valid column in the DataFrame.")
        return pd.DataFrame() 
    
# Run logic after the button is clicked
if calculate:
    st.session_state.calculate_clicked = True
    
    if st.session_state.calculate_clicked:
        # Ensure all files are uploaded
        if schools_file and centers_file and prefs_file:
            # Run the program with the uploads saved in a private temporary directory,
            # which is deleted with the files in it when the block ends
            uploads = {"schools": schools_file, "centers": centers_file, "prefs": prefs_file}
            with saved_uploads(uploads) as paths:
                run_center_randomizer(paths["schools"], paths["centers"], paths["prefs"])
            st.toast("Calculation successful!", icon="🎉")
            st.session_state.calculation_completed = True

            # Set the paths for the output files[UPDATE LATER TO BE FLEXIBLE]
            school_center_file = "results/school-center.tsv"
            school_center_distance_file = "results/school-center-distance.tsv"

            # Store calculated data in session state
            if school_center_file and school_center_distance_file:
                st.session_state.calculated_data['school_center'] = school_center_file
                st.session_state.calculated_data['school_center_distance'] = school_center_distance_file
            else:
                tab1.error("Calculated data not found", icon="🚨")

        else:
            st.sidebar.error("Please upload all required files.", icon="🚨")

elif not st.session_state.calculate_clicked:
    tab1_msg = tab1.info("Results will be shown only after the calculation is completed.", icon="ℹ️")
    tab2_msg = tab2.info("Results will be shown only after the calculation is completed.", icon="ℹ️")

if st.session_state.calculate_clicked and st.session_state.calculation_completed:
    # Display data from session state
    if 'school_center' in st.session_state.calculated_data:
        df_school_center = pd.read_csv(st.session_state.calculated_data['school_center'], sep="\t")
        allowed_filter_types = ['school', 'center']
        st.session_state.filter_type = tab1.radio("Choose a filter type:", allowed_filter_types, horizontal=True)

        # Display an input field based on the selected filter type
        if st.session_state.filter_type:
         if st.session_state.filter_type == 'school':
          # Create filter options with school name and code
          filter_options = [f"{code} | {name}" for name, code in zip(df_school_center['school'].unique(), df_school_center['scode'].unique())]

         elif st.session_state.filter_type == 'center':
          # Create filter options with center name and code
          filter_options = [f"{code} | {name}" for name, code in zip(df_school_center['center'].unique(), df_school_center['cscode'].unique())]

         # Display a selectbox for selection
         st.session_state.filter_value = tab1.selectbox(f"Select a value for {st.session_state.filter_type.capitalize()}:", filter_options)

         # Split the selected value to extract name and code
         code, name = st.session_state.filter_value.split(' | ')

         # Filter the DataFrame based on the selected type and value
         filtered_df = filter_data(df_school_center, st.session_state.filter_type, name)

        with tab1:
          if st.session_state.filter_value:
            # Remove thousand separator comma in scode and cscode 
            styled_df  = pretty_dataframe(filtered_df).style.format({
              "cscode": lambda x: '{:.0f}'.format(x),
              "scode": lambda x: '{:.0f}'.format(x)
            })
            st.dataframe(styled_df , hide_index=True, use_container_width=True)
            st.markdown("<br/><br/>", unsafe_allow_html=True)
            st.subheader('Map', divider=divider_color)
            
            # Initialize data for map
            map_data = filtered_df[['center_lat', 'center_long', 'center', 'allocation']].copy()
            map_data.columns = ['lat', 'long', 'name', 'allocation']
            map_data['type'] = 'Center'
            
            if school_df is not None:
                filter_school = school_df[school_df['scode'].isin(filtered_df['scode']) & school_df['lat'].notnull() & school_df['long'].notnull()]
                school_map_data = filter_school[['lat', 'long', 'name-address']].copy().rename(columns={'name-address': 'name'})
                school_map_data['type'] = 'School'
                map_data = pd.concat([map_data, school_map_data], ignore_index=True)
            
            map_data.drop_duplicates(inplace=True)
            
            try:
                if st.session_state.map_type:
                    st.session_state.map_type = st.radio("Choose a map type:", ["cartodbpositron", "openstreetmap"], horizontal=True)
            except Exception:
                st.session_state.map_type = "cartodbpositron"
            
            show_heatmap = st.checkbox("View allocation distribution", value=False)
            
            # Maps setup
            m = folium.Map(
                location=[map_data['lat'].mean(), map_data['long'].mean()],         # Center map on the mean of the lat and long
                zoom_start=custom_map_zoom(map_data['lat'].values, map_data['long'].values),
                tiles=st.session_state.map_type
            )
            
            fg = folium.FeatureGroup(name="Allocated Centers")
            for _, row in map_data.iterrows(): 
                fg.add_child(folium.Marker(
                    location=[row['lat'], row['long']],
                    tooltip=custom_map_tooltip(row),
                    popup=custom_map_tooltip(row),
                    icon= folium.CustomIcon(
                        "https://cdn-icons-png.flaticon.com/256/4996/4996117.png" if row['type'] == "School" else "https://cdn-icons-png.flaticon.com/256/15092/15092199.png",
                        icon_size=(38, 40),
                        icon_anchor=(21, 38),
                        shadow_image="https://static.vecteezy.com/system/resources/thumbnails/013/169/090/small_2x/oval-shadow-for-object-or-product-png.png",
                        shadow_size=(28, 30) if row['type'] == "School" else (22, 24),
                        shadow_anchor=(8, 19) if row['type'] == "School" else (8, 13),
                    )
                ))
            m.add_child(fg)
            
            if show_heatmap:
                max_allocation = map_data['allocation'].max()
                for _, row in map_data[map_data.allocation > 0].iterrows():
                    folium.CircleMarker(
                        location=[row['lat'], row['long']],
                        radius=row['allocation'] / max_allocation * 25,
                        color="#3c844a",
                        opacity=0.35,
                        fill=True,
                        fill_color="green",
                        fill_opacity=0.3
                    ).add_to(m)
            
            st_folium( m, width=1200, height=400)
         
          st.markdown("<br/><br/>", unsafe_allow_html=True)
          st.subheader('All Data', divider=divider_color)
          st.dataframe(pretty_dataframe(df_school_center), use_container_width=True)
    else:
        tab1.info("No calculated data available.", icon="ℹ️")
    
    if 'school_center_distance' in st.session_state.calculated_data:
        df = pd.read_csv(st.session_state.calculated_data['school_center_distance'], sep="\t")
        tab2.dataframe(pretty_dataframe(df), use_container_width=True)

    else:
        tab2.error("School Center Distance file not found.")

elif st.session_state.calculate_clicked and not st.session_state.calculated_data:
    tab1.error("School Center data not found in session state.")

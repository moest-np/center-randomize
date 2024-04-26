import os
import folium
import tempfile
import subprocess
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import pdfkit

#Page Setup
st.set_page_config(
   page_title="MOEST Exam Center Calculator",
   page_icon=":school:",
#    page_icon="https://avatars.githubusercontent.com/u/167545222?s=200&v=4", # official logo
   layout="wide",
   initial_sidebar_state="expanded",
)

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


#Maps setup
m = folium.Map(location=[27.7007, 85.3001], zoom_start=12, )
fg = folium.FeatureGroup(name="Allocated Centers")

#Sidebar
with st.sidebar:

    add_side_header = st.sidebar.title("Random Center Calculator")

    schools_file = st.sidebar.file_uploader("Upload School/College file", type="tsv")
    centers_file = st.sidebar.file_uploader("Upload Centers file", type="tsv")
    prefs_file = st.sidebar.file_uploader("Upload Preferences file", type="tsv")

    calculate = st.sidebar.button("Calculate Centers", type="primary", use_container_width=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "School Center",
    "School Center Distance",
    "View School Data",
    "View Centers Data",
    "View Pref Data" 
    ])

tab1.subheader("School Center")
tab2.subheader("School Center Distance")
tab3.subheader("School Data")
tab4.subheader("Center Data")
tab5.subheader("Pref Data")

# Show data in Tabs as soon as the files are uploaded
if schools_file:
    df = pd.read_csv(schools_file, sep="\t")
    tab3.dataframe(df)
else:
    tab3.info("Upload data to view it.", icon="ℹ️")

if centers_file:
    df = pd.read_csv(centers_file, sep="\t")
    tab4.dataframe(df)
else:
    tab4.info("Upload data to view it.", icon="ℹ️")

if prefs_file:
    df = pd.read_csv(prefs_file, sep="\t")
    tab5.dataframe(df)
else:
    tab5.info("Upload data to view it.", icon="ℹ️")


# Function to run the center randomizer program
def run_center_randomizer(schools_tsv, centers_tsv, prefs_tsv):
    cmd = f"python school_center.py {schools_tsv} {centers_tsv} {prefs_tsv}"
    subprocess.run(cmd, shell=True)


def generate_pdf(results_data,filename,title):
    st.toast("Generating Pdf..")
    st.write("Generating pdf...")

    # Convert DataFrame to HTML with modern table styling
    html_content = results_data.to_html(index=False, classes=['modern-table'])

    # HTML template for the PDF content
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>School Center</title>
        <style>
            /* Modern table styling */
            .modern-table {{
                width: 100%;
                border-collapse: collapse;
                border-spacing: 0;
            }}
            .modern-table th,
            .modern-table td {{
                border: 1px solid #e0e0e0;
                padding: 10px;
                text-align: center;
            }}
            .modern-table th {{
                background-color: #f8f8f8;
                color: #333333;  /* Header text color */
                font-weight: bold;  /* Bold header text */
                text-transform: uppercase;  /* Uppercase header text */
                letter-spacing: 1px;  /* Increased letter spacing for header text */
            }}
            .modern-table tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .modern-table tr:hover {{
                background-color: #eaeaea;
            }}
           #main-header {{
         display: flex;
        align-items: center;
        justify-content: center;
    }}
 
    .header-text-container {{
    text-align: center;
    }}
        </style>
    </head>
    <body>
  <header id="main-header">
       <div class="header-text-container">
      <img src='https://avatars.githubusercontent.com/u/167545222?s=200&v=4' height= '90px'>
      <h1 class="header-title">नेपाल सरकार</h1>
      <h2 class="header-subtitle">शिक्षा, विज्ञान तथा प्रविधि मन्त्रालय</h2>
      <p class="header-address">सिंहदरबार, काठमाडौं</p>
      <h1>{title}</h1> 
      <p>Randomly generated using center-randomize project by MOEST, Government of Nepal</p>
    </div>
  </header>
        {html_content}
    </body>
    </html>
    """

    # Generate the PDF from the HTML content
    pdfkit.from_string(html_template, f"{filename}.pdf", options={'encoding': 'utf-8'})
    st.success(f"Successfully Downloaded {filename}.pdf!")

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
    
    def save_file_to_temp(file_obj):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_obj.seek(0)  # Go to the start of the file
            temp_file.write(file_obj.read())
            return temp_file.name
    
    if st.session_state.calculate_clicked:
        # Ensure all files are uploaded
        if schools_file and centers_file and prefs_file:
            schools_path = save_file_to_temp(schools_file)
            centers_path = save_file_to_temp(centers_file)
            prefs_path = save_file_to_temp(prefs_file)

            # Run the program with the temporary file paths
            run_center_randomizer(schools_path, centers_path, prefs_path)
            st.toast("Calculation successful!", icon="🎉")
            st.session_state.calculation_completed = True

            # Delete the temporary files after use
            os.unlink(schools_path)
            os.unlink(centers_path)
            os.unlink(prefs_path)

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
        allowed_filter_types = ['scode', 'school', 'cscode', 'center']
        st.session_state.filter_type = tab1.radio("Choose a filter type:", allowed_filter_types)

        # Display an input field based on the selected filter type
        if st.session_state.filter_type:
            st.session_state.filter_value = tab1.selectbox(f"Select a value for {st.session_state.filter_type}:", df_school_center[st.session_state.filter_type].unique())
        # Filter the DataFrame based on the selected filter type and value
        if st.session_state.filter_value:
            filtered_df = filter_data(df_school_center, st.session_state.filter_type, st.session_state.filter_value)
            tab1.dataframe(filtered_df)
            tab1.subheader('Map')
            tab1.divider()
            for index, center in filtered_df.iterrows():
                fg.add_child(
                    folium.Marker(
                        location=[center.center_lat, center.center_long],
                        popup=f"{(center.center).title()}\nAllocation: {center.allocation}",
                        tooltip=f"{center.center}",
                        icon=folium.Icon(color="red")
                    )
                )
            m.add_child(fg)
            with tab1:
                st_folium( m, width=1200, height=400 )
        
        tab1.divider()
        tab1.subheader('All Data')
        tab1.dataframe(df_school_center)



    else:
        tab1.info("No calculated data available.", icon="ℹ️")
    
    if 'school_center_distance' in st.session_state.calculated_data:
        df_school_center_distance = pd.read_csv(st.session_state.calculated_data['school_center_distance'], sep="\t")
        tab2.dataframe(df_school_center_distance)
    else:
        tab2.error("School Center Distance file not found.")
    # Download Button

    def download_handler():
        print(df_school_center.columns)
        print(df_school_center_distance.columns)
        generate_pdf(df_school_center.drop(['center_lat','center_long'],axis=1), "school_center", "School Center")
        generate_pdf(df_school_center_distance.drop(['school_lat','school_long'],axis=1),"school_center_distance","School Center Distance")
    st.button("Download Results as PDF!", on_click=download_handler)

elif st.session_state.calculate_clicked and not st.session_state.calculated_data:
    tab1.error("School Center data not found in session state.")

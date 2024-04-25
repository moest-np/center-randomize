import os
import tempfile
import subprocess
import pandas as pd
import streamlit as st

#Page Setup
st.set_page_config(
   page_title="MOEST Exam Center Calculator",
   page_icon=":school:",
#    page_icon="https://avatars.githubusercontent.com/u/167545222?s=200&v=4", # official logo
   layout="wide",
   initial_sidebar_state="expanded",
)

st.title("Ministry of Education, science and technology - MOEST")
st.caption("MOEST exam center calculator")

#Sidebar
with st.sidebar:

    add_side_header = st.sidebar.title(
    "Random Center Calculator"
    )
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

# Run logic after the button is clicked
if calculate:

    def save_file_to_temp(file_obj):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_obj.seek(0)  # Go to the start of the file
            temp_file.write(file_obj.read())
            return temp_file.name
    
    # Ensure all files are uploaded
    if schools_file and centers_file and prefs_file:
        schools_path = save_file_to_temp(schools_file)
        centers_path = save_file_to_temp(centers_file)
        prefs_path = save_file_to_temp(prefs_file)

        # Run the program with the temporary file paths
        run_center_randomizer(schools_path, centers_path, prefs_path)

        # Set the paths for the output files
        school_center_file = "results/school-center.tsv"
        school_center_distance_file = "results/school-center-distance.tsv"

        # Delete the temporary files after use
        os.unlink(schools_path)
        os.unlink(centers_path)
        os.unlink(prefs_path)

        # Display data in the specified tabs
        if school_center_file:
            df = pd.read_csv(school_center_file, sep="\t")
            tab1.dataframe(df)
        else:
            tab1.error("School Center file not found.")
        
        if school_center_distance_file:
            df = pd.read_csv(school_center_distance_file, sep="\t")
            tab2.dataframe(df)
        else:
            tab2.error("School Center Distance file not found.")

        st.toast("Calculation successful!", icon="🎉")
        
    else:
        st.sidebar.error("Please upload all required files.", icon="🚨")
else:
    tab1_msg = tab1.info("Results will be shown only after the calculation is completed.", icon="ℹ️")
    tab2_msg = tab2.info("Results will be shown only after the calculation is completed.", icon="ℹ️")

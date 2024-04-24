import os
import tempfile
import subprocess
import pandas as pd
import streamlit as st

# Page Setup
st.set_page_config(
    page_title="MOEST Exam Center Calculator",
    page_icon=":school:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
with st.sidebar:
    st.title("Random Center Calculator")
    schools_file = st.file_uploader("Upload School/College file", type="tsv")
    centers_file = st.file_uploader("Upload Centers file", type="tsv")
    prefs_file = st.file_uploader("Upload Preferences file", type="tsv")
    num_centers = st.number_input("Number of Centers", min_value=1, value=5, step=1)

    calculate = st.button("Calculate Centers", help="Calculate the exam centers")

# Tabs
tabs = st.columns(5)

with tabs[0]:
    st.subheader("School Center")

with tabs[1]:
    st.subheader("School Center Distance")

with tabs[2]:
    st.subheader("School Data")

with tabs[3]:
    st.subheader("Center Data")

with tabs[4]:
    st.subheader("Pref Data")

# Function to run the center randomizer program
def run_center_randomizer(schools_tsv, centers_tsv, prefs_tsv, num_centers):
    cmd = f"python school_center.py --schools {schools_tsv} --centers {centers_tsv} --prefs {prefs_tsv} --num_centers {num_centers}"
    subprocess.run(cmd, shell=True)

# Display uploaded data
def display_uploaded_data(file, tab):
    if file:
        df = pd.read_csv(file, sep="\t")
        tab.dataframe(df)
    else:
        tab.info("Upload data to view it.", icon="ℹ️")

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
        run_center_randomizer(schools_path, centers_path, prefs_path, num_centers)

        # Set the paths for the output files
        school_center_file = "results/school-center.tsv"
        school_center_distance_file = "results/school-center-distance.tsv"

        # Delete the temporary files after use
        os.unlink(schools_path)
        os.unlink(centers_path)
        os.unlink(prefs_path)

        # Display data in the specified tabs
        display_uploaded_data(school_center_file, tabs[0])
        display_uploaded_data(school_center_distance_file, tabs[1])

        st.sidebar.success("Calculation successful!")
        
    else:
        st.sidebar.error("Please upload all required files.", icon="🚨")
else:
    tabs[0].info("Results will be shown only after the calculation is completed.", icon="ℹ️")
    tabs[1].info("Results will be shown only after the calculation is completed.", icon="ℹ️")

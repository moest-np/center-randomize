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
    st.sidebar.title("Random Center Calculator")
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
def show_uploaded_data(file, tab):
    if file:
        df = pd.read_csv(file, sep="\t")
        tab.dataframe(df)
    else:
        tab.info("Upload data to view it.", icon="ℹ️")

show_uploaded_data(schools_file, tab3)
show_uploaded_data(centers_file, tab4)
show_uploaded_data(prefs_file, tab5)

# Function to run the center randomizer program
def run_center_randomizer(schools_tsv, centers_tsv, prefs_tsv):
    cmd = ["python", "school_center.py", schools_tsv, centers_tsv, prefs_tsv]
    subprocess.run(cmd)

# Run logic after the button is clicked
if calculate:
    if schools_file and centers_file and prefs_file:
        with st.spinner('Calculating...'):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    schools_path = os.path.join(temp_dir, "schools.tsv")
                    centers_path = os.path.join(temp_dir, "centers.tsv")
                    prefs_path = os.path.join(temp_dir, "prefs.tsv")

                    with open(schools_path, "wb") as f:
                        f.write(schools_file.read())
                    with open(centers_path, "wb") as f:
                        f.write(centers_file.read())
                    with open(prefs_path, "wb") as f:
                        f.write(prefs_file.read())

                    run_center_randomizer(schools_path, centers_path, prefs_path)

                    school_center_file = os.path.join(temp_dir, "results", "school-center.tsv")
                    school_center_distance_file = os.path.join(temp_dir, "results", "school-center-distance.tsv")

                    if os.path.exists(school_center_file):
                        tab1.dataframe(pd.read_csv(school_center_file, sep="\t"))
                    else:
                        tab1.error("School Center file not found.")

                    if os.path.exists(school_center_distance_file):
                        tab2.dataframe(pd.read_csv(school_center_distance_file, sep="\t"))
                    else:
                        tab2.error("School Center Distance file not found.")

                    st.success("Calculation successful!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.sidebar.error("Please upload all required files.", icon="🚨")

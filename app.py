import streamlit as st
import pandas as pd #to get data in excelsheet 
import os
import tempfile
from pathlib import Path
import shutil
import subprocess

# Function to run the center randomizer program
def run_center_randomizer(schools_tsv, centers_tsv, prefs_tsv, output_file):
    # Run the provided program with the specified arguments
    cmd = f"python center_randomizer.py {schools_tsv} {centers_tsv} {prefs_tsv} -o {output_file}"
    subprocess.run(cmd, shell=True)


def main():
    st.title("Center Randomizer")

    #file uploads
    st.header("Upload Files")

    schools_file = st.file_uploader("Upload Schools TSV file", type="tsv")
    centers_file = st.file_uploader("Upload Centers TSV file", type="tsv")
    prefs_file = st.file_uploader("Upload Preferences TSV file", type="tsv")

    output_format = st.selectbox("Select Output Format", ["CSV", "Excel", "JSON"])

    # Output file path
    output_file = 'results/'

    if st.button("Run Center Randomizer"):
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded files to temporary directory
            if schools_file and centers_file and prefs_file:
                schools_path = Path(temp_dir) / "schools.tsv"
                schools_file.seek(0)
                with open(schools_path, "wb") as f:
                    f.write(schools_file.getvalue())

                centers_path = Path(temp_dir) / "centers.tsv"
                centers_file.seek(0)
                with open(centers_path, "wb") as f:
                    f.write(centers_file.getvalue())

                prefs_path = Path(temp_dir) / "prefs.tsv"
                prefs_file.seek(0)
                with open(prefs_path, "wb") as f:
                    f.write(prefs_file.getvalue())

                #run the center randomizer program
                output_file = Path(temp_dir) / "output.tsv"
                run_center_randomizer(schools_path, centers_path, prefs_path, output_file)

                st.success("Center Randomization completed!")
                st.markdown(f"Download the output file [here](/{output_file})")
        finally:
            # Delete temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
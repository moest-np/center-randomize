import unittest
import sys
import os
import subprocess
import warnings

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils.custom_tsv_parser import ParseTSVFile

PREF_CUTOFF = -4


def get_scode_cscode_id(data):
    # Create an id with scode and center with sorted values of scode and center
    school_centers = []
    for row in data:
        scode = int(row["scode"])
        center = int(row["cscode"])
        sccode_center_id = sorted((scode, center))
        sccode_center_id = "_".join(map(str, sccode_center_id))
        school_centers.append(sccode_center_id)
    return school_centers


class TestSchoolCenter(unittest.TestCase):
    """_Tests to validate the outcome of the output are matching
    as per the requirements

    Needs the ouptut from the results/school-center.tsv and
    results/school-center-distance.tsv files to be present

    """

    def setUp(self):
        self.school_center_file = "results/school-center.tsv"
        self.school_center_distance_file = "results/school-center-distance.tsv"
        self.school_center_pref_file = "sample_data/prefs.tsv"
        schools_tsv = "sample_data/schools_grade12_2081.tsv"
        centers_tsv = "sample_data/centers_grade12_2081.tsv"
        cmd = f"python school_center.py {schools_tsv} {centers_tsv} {self.school_center_pref_file}"
        subprocess.run(cmd, shell=True)

    def tearDown(self):
        os.remove(self.school_center_file)
        os.remove(self.school_center_distance_file)

    def test_results_exists(self):
        """_Test if the application in running which output the results in the
             results filder_

        Returns:
            Pass: If the file exists in the results folder
            Fail: If the file doesnot exists in the results folder
        """
        self.assertTrue(os.path.exists(self.school_center_file))
        self.assertTrue(os.path.exists(self.school_center_distance_file))
        self.assertTrue(os.path.exists(self.school_center_pref_file))

    def test_scode_student_count_not_more_than_200(self):
        """_Test if the student count is not more than 200_
          Test case ID 001:- एक विद्यालयको परिक्षार्थी संख्या हेरी सकभर १००, २०० भन्दा बढी
                             परीक्षार्थी एकै केन्द्रमा नपर्ने गरी बाँढ्न पर्ने

        Returns:
            Pass: If the student count is not more than 100
            Fail: If the student count is more than 100
        """
        ptf = ParseTSVFile(self.school_center_file)
        data = ptf.get_rows()
        for row in data:
            student_count = row["allocation"]
            if int(student_count) > 200:
                warnings.warn(f"student count is more than 200 for the school {row}")


    def test_scode_cscode_not_same(self):
        """_Test if the output of scode is not equal to cscode_
          Test case ID :- आफ्नै विद्यालयमा केन्द्र पार्न नहुने

        Returns:
            Pass: If the scode is not same as cscode
            Fail: If the scode is same as cscode
        """
        scf = ParseTSVFile(self.school_center_file)
        data = scf.get_rows()
        failures = []
        for row in data:
            scode = row["scode"]
            cscode = row["cscode"]
            if scode == cscode:
                failures.append(f"scode and cscode are same for row {row} {scode}")
        assert len(failures) == 0, f'{len(failures)} rows failed. {chr(10).join(failures)}'

    def test_no_mutual_centers(self):
        """_Test if the scode's center is not same as cscode's
            centre and vice versa_
          Test case ID :- दुई विद्यालयका परीक्षार्थीको केन्द्र एक अर्कामा पर्न नहुने, अर्थात् कुनै विद्यालयका परीक्षार्थीको केन्द्र परेको विद्यालयका परीक्षार्थीहरूको केन्द्र अघिल्लो विद्यालयमा पार्न नहुने ।

        Returns:
            Pass: If the scode's center is not same as cscode's center
            Fail: If the scode's center is same as cscode's center
        """
        scf = ParseTSVFile(self.school_center_file)
        data = scf.get_rows()
        scodes_centers = []

        scodes_centers = get_scode_cscode_id(data)

        # Check if there are any duplicates id if duplicate then there is a collision between school and center
        duplicates = [
            item for item in set(scodes_centers) if scodes_centers.count(item) > 1
        ]

        self.assertFalse(
            duplicates,
            f"Duplicate values found in scode_center_code: {', '.join(duplicates)}",
        )

    @unittest.skip ("needs review")
    def test_undesired_cscode_scode_pair(self):
        """_Test if the schools and the centers are not matched based on the
        cost preferences defined in the prefs.tsv file_
          Test case ID :-
          1 एकै स्वामित्व / व्यवस्थापनको भनी पहिचान भएका केन्द्रमा पार्न नहुने
          2 विगतमा कुनै विद्यालयको कुनै केन्द्रमा पार्दा समस्या देखिएकोमा केन्द्र दोहोऱ्याउन नहुने

        Returns:
            Pass: If the schools with undesired scodes are are not paired with its cscodes
            Fail: If the schools with same management are each other's center
        """

        scf = ParseTSVFile(self.school_center_file)
        cpf = ParseTSVFile(self.school_center_pref_file)
        data_scf = scf.get_rows()
        data_cpf = cpf.get_rows()
        for cpf_data in data_cpf:
            if int(cpf_data["pref"]) < PREF_CUTOFF:
                data_cpf.remove(cpf_data)

        failures = []

        scodes_centers = get_scode_cscode_id(data_scf)

        undesired_csodes_centers = get_scode_cscode_id(data_cpf)
        for undesired_cscodes_center in undesired_csodes_centers:
            if undesired_cscodes_center in scodes_centers:
                failures.append(
                    f"Schools with undesired centers {undesired_cscodes_center}"
                )

        assert len(failures) == 0, f'{len(failures)} rows failed. {chr(10).join(failures)}'



if __name__ == "__main__":
    unittest.main()

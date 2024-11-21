import unittest
from unittest.mock import patch, MagicMock
from school_center import read_tsv, read_prefs, haversine_distance, filter_and_sort_centers, allocate_centers, main

class TestSchoolCenterScript(unittest.TestCase):

    def test_haversine_distance(self):
        # Test the distance calculation for known coordinates
        distance = haversine_distance(36.12, -86.67, 33.94, -118.40)
        self.assertAlmostEqual(distance, 2887, places=0)  # Approximate distance in km

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="scode\tcscode\tpref\treason\n27001\t28001\t-5\tsame management\n")
    def test_read_prefs(self, mock_file):
        result = read_prefs('dummy_path')
        expected = {'27001': {'28001': -5}}
        self.assertEqual(result, expected)

    @patch('school_center.read_tsv')
    def test_filter_and_sort_centers(self, mock_read_tsv):
        mock_read_tsv.return_value = [
            {'cscode': '28001', 'capacity': '120', 'name': 'Center A', 'address': 'Location X', 'lat': '27.0', 'long': '85.0'},
            {'cscode': '28002', 'capacity': '200', 'name': 'Center B', 'address': 'Location Y', 'lat': '27.5', 'long': '85.5'}
        ]
        school = {'scode': '27001', 'lat': '27.0', 'long': '85.0'}
        centers = mock_read_tsv()
        prefs = {'27001': {'28001': 0, '28002': 3}}
        sorted_centers = filter_and_sort_centers(school, centers, 10, prefs)
        self.assertEqual(len(sorted_centers), 2)
        self.assertEqual(sorted_centers[0]['cscode'], '28002')  # Should be sorted by preference score

    @patch('school_center.read_tsv')
    @patch('school_center.filter_and_sort_centers')
    def test_allocate_centers(self, mock_filter_and_sort, mock_read_tsv):
        mock_read_tsv.return_value = [
            {'cscode': '28001', 'capacity': '120', 'lat': '27.0', 'long': '85.0'},
            {'cscode': '28002', 'capacity': '200', 'lat': '27.5', 'long': '85.5'}
        ]
        mock_filter_and_sort.return_value = [
            {'cscode': '28001', 'capacity': '120', 'name': 'Center A', 'address': 'Location X', 'lat': '27.0', 'long': '85.0', 'distance_km': 0, 'pref_score': 0},
            {'cscode': '28002', 'capacity': '200', 'name': 'Center B', 'address': 'Location Y', 'lat': '27.5', 'long': '85.5', 'distance_km': 10, 'pref_score': 3}
        ]
        schools = [{'scode': '27001', 'count': '150', 'lat': '27.0', 'long': '85.0'}]
        centers = mock_read_tsv()
        prefs = {'27001': {'28001': 0, '28002': 3}}
        allocations, remaining_students = allocate_centers(schools, centers, prefs)
        self.assertEqual(remaining_students, 0)
        self.assertIn('27001', allocations)
        self.assertTrue(allocations['27001']['28002'] > 0)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('school_center.allocate_centers', return_value=({}, 0))
    @patch('school_center.read_prefs', return_value={})
    @patch('school_center.read_tsv', return_value=[])
    def test_main(self, mock_read_tsv, mock_read_prefs, mock_allocate, mock_open, mock_args):
        mock_args.return_value = MagicMock(schools_tsv='schools.tsv', centers_tsv='centers.tsv', prefs_tsv='prefs.tsv', output='output.tsv')
        main()
        mock_read_tsv.assert_called()
        mock_read_prefs.assert_called()
        mock_allocate.assert_called()

if __name__ == '__main__':
    unittest.main()

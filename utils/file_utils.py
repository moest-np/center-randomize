''' File handler '''
import csv
import os
from typing import Dict, List

class FileUtils():

    """
    Create the given directory if it doesn't exists
    - Creates all the directories needed to resolve to the provided directory path
    """
    def create_dir(self,dirPath:str):
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

    def read_tsv(self,file_path: str) -> List[Dict[str, str]]:
        data = []
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                data.append(dict(row))
        return data
    
    def read_prefs(self,file_path: str) -> Dict[str, Dict[str, int]]:
        prefs = {}
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                if prefs.get(row['scode']):
                    if prefs[row['scode']].get(row['cscode']):
                        prefs[row['scode']][row['cscode']] += int(row['pref'])
                    else:
                        prefs[row['scode']][row['cscode']] = int(row['pref'])
                else:
                    prefs[row['scode']] = {row['cscode']: int(row['pref'])}

        return prefs

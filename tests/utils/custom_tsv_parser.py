import csv


class ParseTSVFile:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_file(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            return reader

    def get_columns(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            return reader.fieldnames

    def get_row_count(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            return len(list(reader))

    def get_column_count(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            return len(reader.fieldnames)

    def get_rows(self):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            data = []
            for row in reader:
                data.append(row)
            return data

    def get_column_data(self, column_name):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            data = []
            for row in reader:
                data.append(row[column_name])
            return data

    def get_row_data(self, row_number):
        with open(self.file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            data = []
            for row in reader:
                data.append(row)
            return data[row_number]

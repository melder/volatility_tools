import csv


def fetch_tickers_from_csv(filename, delimiter="\t"):
    with open(filename, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=delimiter)
        return list(map(lambda x: x[0], csv_reader))

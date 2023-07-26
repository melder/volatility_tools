"""
redis caching functions for IV related datapoints
"""

import csv
import os
from datetime import datetime

import pytz
import redis

# Specify the path to the folder containing the CSV files
folder_path = "csvs"

r = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)


def key_join(*segments, delimiter=":"):
    return delimiter.join([str(x) for x in segments])


IV_DATA_NAMESPACE = "iv_data"
AVERAGE_NAMESPACE = key_join(IV_DATA_NAMESPACE, "average")
MEDIAN_NAMESPACE = key_join(IV_DATA_NAMESPACE, "median")

def pretty_timestamp(timestamp):
    utc_datetime = datetime.utcfromtimestamp(timestamp)

    utc_timezone = pytz.timezone('UTC')
    est_timezone = pytz.timezone('US/Eastern')
    est_datetime = utc_timezone.localize(utc_datetime).astimezone(est_timezone)

    # Mon Jul 31 2023
    # return est_datetime.strftime("%a %b %d %Y")
    return est_datetime.strftime("%c")

def fetch_average_ivs(ticker, percentage=True, _start=0, _end=-1):
    redis_average_key = key_join(AVERAGE_NAMESPACE, ticker)
    res = r.zrange(redis_average_key, _start, _end, withscores=True)
    if percentage:
        return [(float(x[0]) * 100, pretty_timestamp(x[1])) for x in res]
    return res

def insert_to_redis(line, timestamp):
    ticker, _, _, _avg, _median, _, _ = line.split("\t")

    redis_average_key = key_join(AVERAGE_NAMESPACE, ticker)
    redis_median_key = key_join(MEDIAN_NAMESPACE, ticker)

    r.zadd(redis_average_key, {_avg: float(timestamp)})
    r.zadd(redis_median_key, {_median: float(timestamp)})


def purge_redis_keys():
    average_keys = key_join(AVERAGE_NAMESPACE, "*")
    median_keys = key_join(MEDIAN_NAMESPACE, "*")
    r.delete(*(list(r.scan_iter(average_keys)) + list(r.scan_iter(median_keys))))


def parse_csvs():
    for filename in os.listdir(folder_path):
        if not filename.endswith(".csv"):
            continue

        file_path = os.path.join(folder_path, filename)
        timestamp = filename.replace(".csv", "")

        with open(file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                insert_to_redis(row[0], timestamp)


if __name__ == "__main__":
    purge_redis_keys()
    parse_csvs()

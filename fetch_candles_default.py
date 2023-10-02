"""
Script to populate and store last 13 weeks (1 quarter window) of candle data for
either all options or weekly options
"""

import datetime

from helpers.csv_helpers import fetch_tickers_from_csv
from strategies.polygon_api.polygon_candle import Polygon


def get_most_recent_saturday():
    today = datetime.date.today()
    days_since_saturday = (today.weekday() - 5) % 7
    most_recent_saturday = today - datetime.timedelta(days=days_since_saturday)
    return most_recent_saturday.isoformat()


def subtract_weeks_from_iso_date(iso_date, num_weeks=13):
    date_obj = datetime.datetime.fromisoformat(iso_date)
    new_date_obj = date_obj - datetime.timedelta(weeks=num_weeks)
    return new_date_obj.date().isoformat()


if __name__ == "__main__":
    tickers = fetch_tickers_from_csv("csv/options_weeklies.csv")
    iso_to = get_most_recent_saturday()
    # iso_to = subtract_weeks_from_iso_date(iso_to, num_weeks=2)
    iso_from = subtract_weeks_from_iso_date(iso_to, num_weeks=13)
    agg_timestamp = int(datetime.datetime.utcnow().timestamp())

    Polygon.process_tickers(tickers, iso_from, iso_to)

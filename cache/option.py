from models.option import Option
from helpers import csv_helpers


class RedisOption:
    """
    redis caching of anything related to option data that
    1. may not neatly fit within option model
    2. is a one-off function to seed / sync / purge data and best to
       be executed within interpreter or command-line
    """

    redis = Option.redis
    namespace = Option.redis_namespace

    @classmethod
    def sync_all_median_iv(cls):
        """
        initializes / rewrites median iv chart data to redis for all tickers
        """
        for ticker in csv_helpers.fetch_all_options_tickers():
            print(f"SYNC ALL MEDIAN IV - {ticker}")
            Option(ticker).cache_all_median_ivs()

    def __init__(self, ticker):
        self.ticker = ticker
        self.key = f"{self.namespace}:{self.ticker}"

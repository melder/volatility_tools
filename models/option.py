from datetime import datetime
from statistics import mean, median

import pytz

from config import config


class Option:
    """
    Option model

    Properties:

    todo
    """

    # db attributes
    db = config.mongo_db()
    collection = db["options"]

    @classmethod
    def test_mongo(cls):
        print("Returns estimated document count for 'options' collection")
        return cls(config.mongo_db()).db.options.estimated_document_count()

    @classmethod
    def last_scrape_timestamp(cls):
        return sorted(list(cls.collection.distinct("scraper_timestamp")))[-1]

    @classmethod
    def all_last_scrape(cls):
        return list(
            cls.collection.find({"scraper_timestamp": cls.last_scrape_timestamp()})
        )

    def __init__(self, ticker, _last=None):
        self.ticker = ticker
        self._last = _last

    def last(self):
        self._last = self._last or self.collection.find_one(
            {"ticker": self.ticker}, sort=[("_id", -1)]
        )
        return self._last

    def all(self):
        return self.collection.find({"ticker": self.ticker})

    def average_ivs(self, percentage=True):
        res = []
        for doc in list(self.all()):
            try:
                ivs = []
                for opt in doc["options"]:
                    ivs.append(float(opt["implied_volatility"]))
                avg = round(mean(ivs) * 100, 2) if percentage else mean(ivs)
                res.append(
                    {
                        "average": avg,
                        "scraper_timestamp": doc["scraper_timestamp"],
                        "scraper_timestamp_pretty": self.pretty_datetime(
                            doc["scraper_timestamp"]
                        ),
                        "expires_at": doc["expiration"],
                        "created_at_pretty": doc["created_at"]
                        .replace(tzinfo=pytz.utc)
                        .astimezone(pytz.timezone("US/Eastern"))
                        .strftime("%a %b %d %Y %-I:%M %p"),
                    }
                )
            except TypeError as err:
                print(err)
                continue
        return res

    # TODO: compress into single function
    def median_ivs(self, percentage=True):
        res = []
        for doc in list(self.all()):
            try:
                ivs = []
                for opt in doc["options"]:
                    ivs.append(float(opt["implied_volatility"]))
                avg = round(median(ivs) * 100, 2) if percentage else median(ivs)
                res.append(
                    {
                        "average": avg,
                        "scraper_timestamp": doc["scraper_timestamp"],
                        "scraper_timestamp_pretty": self.pretty_datetime(
                            doc["scraper_timestamp"]
                        ),
                        "expires_at": doc["expiration"],
                        "created_at_pretty": doc["created_at"]
                        .replace(tzinfo=pytz.utc)
                        .astimezone(pytz.timezone("US/Eastern"))
                        .strftime("%a %b %d %Y %-I:%M %p"),
                    }
                )
            except TypeError:
                continue
        return res

    @staticmethod
    def iv(docs):
        if not isinstance(docs, list):
            docs = [docs]

        res = []
        for doc in docs:
            for opt in doc["options"]:
                res.append(float(opt["implied_volatility"]))

        return {"avg": sum(res) / len(res), "median": median(res)}

    # crude tightness evaluation of bid/ask spread
    @staticmethod
    def spread_score(doc, padding=0.10):
        res = []
        for opt in doc["options"]:
            ask = float(opt["ask_price"])
            bid = float(opt["bid_price"])
            score = (ask - bid) / (ask + padding)
            res.append(score)

        return sum(res) / len(res)

    @staticmethod
    def volume(docs):
        if not isinstance(docs, list):
            docs = [docs]

        res = []
        for doc in docs:
            for opt in doc["options"]:
                res.append(int(opt["volume"]))

        return sum(res)

    @staticmethod
    def open_interest(docs):
        if not isinstance(docs, list):
            docs = [docs]

        res = []
        for doc in docs:
            for opt in doc["options"]:
                res.append(int(opt["open_interest"]))

        return sum(res)

    def last_iv(self):
        return self.iv(self.last())

    def last_spread_score(self):
        return self.spread_score(self.last())

    def last_volume(self):
        return self.volume(self.last())

    def last_open_interest(self):
        return self.open_interest(self.last())

    @staticmethod
    def pretty_datetime(timestamp, _format="%a %b %d %Y"):
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime(_format)

from datetime import datetime
from statistics import mean, median
import json
import pytz

from config import config


class Option:
    """
    Option model

    Properties:

    todo

    Indexes:

    db.options.createIndex({ scraper_timestamp: 1 })
    db.options.createIndex({ ticker: 1 })
    """

    collection_name = "options"

    # db attributes
    db = config.mongo_db()
    collection = db[collection_name]

    redis = config.redis_client()
    redis_namespace = ":".join(["vol", "option"])

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

    @classmethod
    def all_tickers(cls):
        return list(cls.collection.distinct("ticker"))

    def __init__(self, ticker, _last=None):
        self.ticker = ticker
        self._last = _last
        self._all = []

    def last(self):
        self._last = self._last or self.collection.find_one(
            {"ticker": self.ticker}, sort=[("_id", -1)]
        )
        return self._last

    def all_docs(self):
        self._all = self._all or list(self.collection.find({"ticker": self.ticker}))
        return self._all

    def remove_all(self):
        return self.collection.delete_many({"ticker": self.ticker})

    def average_ivs(self, percentage=True):
        res = []
        for doc in list(self.all_docs()):
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
    def median_ivs(self):
        res = []
        for doc in list(self.all_docs()):
            if item := self.to_chart(doc):
                res.append(item)

        return res

    @staticmethod
    def to_chart(doc, percentage=True):
        try:
            ivs = []
            for opt in doc["options"]:
                ivs.append(float(opt["implied_volatility"]))
            avg = round(median(ivs) * 100, 2) if percentage else median(ivs)
            return {
                "average": avg,
                "scraper_timestamp": doc["scraper_timestamp"],
                "scraper_timestamp_pretty": Option.pretty_datetime(
                    doc["scraper_timestamp"]
                ),
                "expires_at": doc["expiration"],
                "created_at_pretty": doc["created_at"]
                .replace(tzinfo=pytz.utc)
                .astimezone(pytz.timezone("US/Eastern"))
                .strftime("%a %b %d %Y %-I:%M %p"),
            }
        except TypeError:
            return {}

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

    #########
    # REDIS #
    #########

    def median_ivs_redis(self):
        redis_key = ":".join([self.redis_namespace, "median_iv", self.ticker])
        return [
            json.loads(k) | {"scraper_timestamp": str(int(v))}
            for k, v in self.redis.zrange(redis_key, 0, -1, withscores=True)
        ]

    def cache_last_median_iv(self):
        """
        cache last median implied volatility to redis
        """
        if chart_item := self.to_chart(self.last()):
            score = float(chart_item.pop("scraper_timestamp"))

            redis_key = ":".join([self.redis_namespace, "median_iv", self.ticker])
            self.redis.zadd(redis_key, {json.dumps(chart_item): score})

    def cache_all_median_ivs(self):
        """
        cache median implied volatility for all options to redis
        """
        redis_key = ":".join([self.redis_namespace, "median_iv", self.ticker])
        for chart_item in self.median_ivs():
            if not chart_item:
                continue

            score = float(chart_item.pop("scraper_timestamp"))
            self.redis.zadd(redis_key, {json.dumps(chart_item): score})

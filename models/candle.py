from config import config


class Candle:
    """
    Candle model

    Properties:

    ticker (str) - stock symbol
    interval_minutes (int) - interval of price measurements in minutes
    filled_gaps (bool) - whether missing price data was filled
    prices (dict) - index aligned candle data
        open, close, high, low (list of float)
        timestamp - timestamp of price sample (list of int)

    Optional properties:

    premarket (bool) - if premarket data is included
    aftermarket (bool) - if aftermarket data is
    """

    # db attributes
    client = config.mongo_client()
    db = client["aggregator"]
    collection = db["candles"]

    def __init__(self, ticker):
        self.ticker = ticker

    def find(self):
        return self.collection.find_one({"ticker": self.ticker}, sort=[("_id", -1)])

    def upsert(self, params):
        document = self.find()
        if not document:
            params["created_at"] = params["updated_at"]
            self.collection.insert_one(params)
        else:
            if document["interval_minute"] != params["interval_minute"]:
                raise ValueError("Interval value mismatch")
            if document["filled_gaps"] != params["filled_gaps"]:
                raise ValueError("Filled gaps value mismatch")

            prices = params["prices"]
            first_index = 0
            for i, timestamp in enumerate(prices["timestamp"]):
                if timestamp not in document["prices"]["timestamp"]:
                    first_index = i
                    break

            if first_index == 0:
                raise ValueError(
                    "Could not find timestamp where to append to existing document"
                )

            self.collection.update_one(
                {"_id": document["_id"]},
                {
                    "$push": {
                        "prices.open": {"$each": prices["open"][first_index:]},
                        "prices.close": {"$each": prices["close"][first_index:]},
                        "prices.high": {"$each": prices["high"][first_index:]},
                        "prices.low": {"$each": prices["low"][first_index:]},
                        "prices.timestamp": {
                            "$each": prices["timestamp"][first_index:]
                        },
                    }
                },
            )

    @staticmethod
    def squash(document, interval):
        """
        Takes minute data and squeezes candles to N / interval samples.
        E.g. interval == 15 returns 15 minute candle

        Only feasible if

        1. interval > interval_minute
        2. interval must be common denominator of interval_minute (interval % interval_minute == 0)
        3. interval must be common denominator of 390 (minutes that market is open)

        Note that infeasibility for point (3) is weak and can be addressed with logic changes,
        but 2, 3, 5, 10, 15, 30 minute candles are acceptable and sufficent.
        Also, let's say 60 minute candle is desired. 65 minute candle can be used instead
        and is approximately equivalent.

        For now assumption is interval_minute == 1
        """

        if not document or "interval_minute" not in document:
            return {}
        if not interval > document["interval_minute"]:
            return {}
        if not 390 % interval == 0:
            return {}
        if not document["interval_minute"] == 1:
            return {}

        open_arr = []
        timestamp_arr = []
        for i, price in enumerate(document["prices"]["open"]):
            if i % interval == 0:
                open_arr.append(price)
                timestamp_arr.append(document["prices"]["timestamp"][i])

        close_arr = []
        for i, price in enumerate(document["prices"]["close"]):
            if i % interval == interval - 1:
                close_arr.append(price)

        temp = []
        high_arr = []
        for i, price in enumerate(document["prices"]["high"], start=1):
            temp.append(price)
            if i % interval == 0:
                high_arr.append(max(temp))
                temp = []

        temp = []
        low_arr = []
        for i, price in enumerate(document["prices"]["low"], start=1):
            temp.append(price)
            if i % interval == 0:
                low_arr.append(min(temp))
                temp = []

        return {
            "open": open_arr,
            "close": close_arr,
            "high": high_arr,
            "low": low_arr,
            "timestamp": timestamp_arr,
        }

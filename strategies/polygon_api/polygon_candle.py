import time
from datetime import datetime
from pprint import pprint  # pylint: disable=unused-import

import pytz
from polygon import RESTClient
from polygon.rest.models.aggs import Agg

from config import config
from strategies.candle_strategy import CandleStrategy
from models.candle import Candle


class Polygon(CandleStrategy):
    """
    polygon.io API candles implementation
    """

    # api parameters
    api_key = config.conf.polygon.api_key
    rate_limit_seconds = config.conf.polygon.rate_limit_seconds
    limit = 50000
    retries = 5

    # data parsing constants
    timestamp_minute_step = 60000  # milliseconds
    premarket_minutes_range = range(240, 570)
    market_minutes_range = range(570, 960)
    aftermarket_minutes_range = range(960, 1200)

    # TODO: support half days
    ignore_iso_dates = ["2022-11-25", "2023-07-03"]

    @classmethod
    def process_tickers(cls, tickers, iso_from, iso_to, interval=1, fill_gaps=True):
        for ticker in tickers:
            print(f"Processing {ticker} ...")

            try:
                _self = cls(ticker, iso_from, iso_to, interval, fill_gaps)
                _self.store_to_mdb()
                time.sleep(cls.rate_limit_seconds)
            except PolygonParseException as err:
                print(err)

    def __init__(self, ticker, iso_from, iso_to, interval=1, fill_gaps=True):
        self.ticker = ticker
        self.iso_from = iso_from
        self.iso_to = iso_to
        self.interval = interval
        self.fill_gaps = fill_gaps

        # v2: support potential gaps
        if interval > 1:
            self.fill_gaps = True

        self.candles = []

        self.prices = {}
        self.prices["open"] = []
        self.prices["close"] = []
        self.prices["high"] = []
        self.prices["low"] = []
        self.prices["timestamp"] = []

    def fetch_candles_from_api(self):
        if self.candles:
            return None

        client = RESTClient(self.api_key)
        for _ in range(self.retries):
            try:
                for i, candle in enumerate(
                    client.list_aggs(
                        self.ticker,
                        1,
                        "minute",
                        self.iso_from,
                        self.iso_to,
                        limit=self.limit,
                    )
                ):
                    self.candles.append(candle)
                    if i > 0 and i % self.limit == 0:
                        # print(f"Grabbed {i} samples. Pausing ...")
                        time.sleep(self.rate_limit_seconds)
                if not self.candles:
                    print(f"No results for {self.iso_from} to {self.iso_to}")
                break
            except Exception as e:
                print(f"Request failed: {e=}, {type(e)=} . Retrying ...")
                time.sleep(self.rate_limit_seconds)

        return None

    def sample_count(self):
        if not self.prices:
            return 0
        return len(self.prices["open"])

    def parse(self):
        """
        * polygon returns regular hours + premarket and aftermarket data so requires some digestion
        * want to allow sampling from 1 minute - 1 week range

        params:
        - fill_gaps: if timestamps for a particular minute is missing, apply following strategy:
            1.  copy previous candle into missing minute
            2.  edge case: if first candle is (or sequence of candles are) missing,
                backfill gaps with first candle encountered


        parsing makes the following assumptions:
        - premarket 04:00 -> 09:30 ET (minutes 240 -> 570)
        - market open from 09:30 -> 16:00 ET (minutes 570 -> 960)
        - aftermarket 16:00 -> 20:00 ET (minutes 960 -> 1200)
        - omit short days (unless sampling interval is from 1 day - 1 week)

        polygon candle attributes:
        - timestamp
        - open, close, high, low
        - vwap, volume, transactions
        """

        self.fetch_candles_from_api()
        if not self.candles:
            raise PolygonParseException("Candle dataset is empty")

        # v2: support frequencies > 1 minute
        # v2: support premarket / aftermarket frontfills / backfills ?
        prev_candle = None
        prev_dt = None
        days = []  # for debugging
        for candle in self.candles:
            eastern_dt = self.timestamp_to_datetime(candle.timestamp)
            minutes = eastern_dt.hour * 60 + eastern_dt.minute

            if eastern_dt.date().isoformat() in self.ignore_iso_dates:
                continue
            if not minutes in self.market_minutes_range:
                continue
            if prev_dt and (eastern_dt.date() > prev_dt.date()):
                days.append(prev_dt.date())
                if self.fill_gaps:
                    self.frontfill_eod_candles(prev_candle)
                prev_candle = None

            if self.fill_gaps:
                if not prev_candle:
                    self.backfill_candles(candle, minutes)
                else:
                    self.frontfill_candles(candle, prev_candle)

            self.append_candle(candle)
            prev_candle = candle
            prev_dt = eastern_dt

        if self.fill_gaps:
            self.frontfill_eod_candles(prev_candle)

        days.append(prev_dt.date())

        # pprint(days)
        # pprint(len(days))
        # pprint(self.prices["timestamp"][0:1200])
        # pprint(self.sample_count())

    def backfill_candles(self, first_candle, minutes):
        diff_minutes = minutes - self.market_minutes_range[0]
        for i in range(diff_minutes):
            backfilled_candle = self.copy_candle(first_candle, diff_minutes - i, "back")
            self.append_candle(backfilled_candle)

    def frontfill_candles(self, candle, prev_candle):
        diff_minutes = (
            candle.timestamp - prev_candle.timestamp
        ) // self.timestamp_minute_step
        for i in range(diff_minutes - 1):
            frontfilled_candle = self.copy_candle(prev_candle, i, "front")
            self.append_candle(frontfilled_candle)

    def frontfill_eod_candles(self, prev_candle):
        count = self.sample_count()
        remainder = count % len(self.market_minutes_range)
        if remainder > 0:
            for i in range(len(self.market_minutes_range) - remainder):
                frontfilled_candle = self.copy_candle(prev_candle, i, "front")
                self.append_candle(frontfilled_candle)

    @staticmethod
    def timestamp_to_datetime(timestamp, timezone="US/Eastern"):
        utc_dt = datetime.utcfromtimestamp(timestamp / 1000)
        return utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(timezone))

    @staticmethod
    def copy_candle(candle, index, fill_type):
        if fill_type not in ["back", "front"]:
            raise PolygonParseException(
                "Copy candle fill must be either of type 'back' or 'front'"
            )

        new_candle = Agg()
        new_candle.volume = 0
        new_candle.vwap = candle.vwap
        new_candle.transactions = None
        new_candle.otc = candle.otc

        if fill_type == "back":
            new_candle.open = candle.open
            new_candle.close = candle.open
            new_candle.high = candle.open
            new_candle.low = candle.open
            new_candle.timestamp = (
                candle.timestamp - index * Polygon.timestamp_minute_step
            )

        if fill_type == "front":
            new_candle.open = candle.close
            new_candle.close = candle.close
            new_candle.high = candle.close
            new_candle.low = candle.close
            new_candle.timestamp = (
                candle.timestamp + (index + 1) * Polygon.timestamp_minute_step
            )

        return new_candle

    def append_candle(self, candle):
        self.prices["open"].append(candle.open)
        self.prices["close"].append(candle.close)
        self.prices["high"].append(candle.high)
        self.prices["low"].append(candle.low)
        self.prices["timestamp"].append(candle.timestamp)

    def fetch_prices(self):
        if not self.candles:
            self.parse()

    def open_prices(self):
        return self.prices["open"]

    def close_prices(self):
        return self.prices["close"]

    def high_prices(self):
        return self.prices["high"]

    def low_prices(self):
        return self.prices["low"]

    # TODO: MUST redesign this to append
    # handle code in candle model instead
    # agg_timestamp is redundant, remove
    # replace with updated_at timestamp
    def store_to_mdb(self):
        if not self.candles:
            self.parse()

        Candle(self.ticker).upsert(
            {
                "ticker": self.ticker,
                "interval_minute": self.interval,
                "filled_gaps": self.fill_gaps,
                "updated_at": datetime.utcnow(),
                "prices": self.prices,
            }
        )


class PolygonParseException(Exception):
    """
    Custom exception class
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

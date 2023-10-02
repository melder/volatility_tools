from abc import ABC, abstractmethod


class CandleStrategy(ABC):
    """
    Strategy pattern for retrieving / parsing candle data

    Purpose is to facilitate plugging in different sources of candle data,
    e.g. through 3rd party vendors, scraping, or other.
    """

    @abstractmethod
    def fetch_prices(self):
        pass

    @abstractmethod
    def open_prices(self):
        pass

    @abstractmethod
    def close_prices(self):
        pass

    @abstractmethod
    def high_prices(self):
        pass

    @abstractmethod
    def low_prices(self):
        pass

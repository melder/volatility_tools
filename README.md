# IV history charts

Web client for data scraped from https://github.com/melder/iv_scraper

**Note** This is in prototype phase _and_ is the first web app I've written in Flask. Also frontend is not my forte. Expect spaghetti code / strange design choices / poor polish.

## Requirements

1. Python 3.11.4
2. pyenv + pipenv
3. redis7 server

## Installation

1. Get pyenv + install python 3.11.4
2. Get pipenv
3. Clone, init environment, init submodules:

```
$ git clone git@github.com:melder/iv_history_charts.git
$ cd iv_history_charts
$ pipenv install
$ git submodule update --init --recursive
```

3. Populate cache

```
$ pipenv shell
$ python cache_datapoints.py
```

4. Launch flask app server

```
$ flask --app home run --debug
```

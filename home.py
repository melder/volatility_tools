from statistics import mean, median

from flask import Flask, jsonify, render_template, request

import cache_autocomplete
import cache_datapoints
from models.option import Option

app = Flask(__name__)


@app.route("/chart-data")
def chart_data():
    # Retrieve data from your database or any other source
    ticker = request.args.get("ticker").upper()
    # average_ivs = cache_datapoints.fetch_average_ivs (ticker)
    # average_ivs = Option(ticker).average_ivs()
    average_ivs = Option(ticker).median_ivs_redis()
    data = {
        "ticker": ticker,
        "average_ivs": average_ivs,
        "mean": mean([x["average"] for x in average_ivs]),
        "median": median([x["average"] for x in average_ivs]),
    }
    return jsonify(data)


@app.route("/autocomplete")
def autocomplete():
    data = {"members": sorted(cache_autocomplete.get_autocomplete_members())}
    return jsonify(data)


@app.route("/")
def home():
    return render_template("index.html")

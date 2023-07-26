from flask import Flask, render_template, jsonify, request
import cache_datapoints
import cache_autocomplete
from statistics import mean, median

app = Flask(__name__)

@app.route('/chart-data')
def chart_data():
    # Retrieve data from your database or any other source
    ticker = request.args.get('ticker').upper()
    average_ivs = cache_datapoints.fetch_average_ivs(ticker)
    data = {
        "ticker": ticker,
        "average_ivs": average_ivs,
        "mean": mean([x[0] for x in average_ivs]),
        "median": median([x[0] for x in average_ivs])
      }
    return jsonify(data)

@app.route('/autocomplete')
def autocomplete():
    data = {
        "members": sorted(cache_autocomplete.get_autocomplete_members())
      }
    return jsonify(data)

@app.route("/")
def home():
    return render_template("index.html")

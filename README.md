# Volatility Tools

This repository seeks to unify the volatility tools I have developed + provide a foundation for quantitative analysis of stock volatility.

Since this is primarily used within the context of option trading only data of stocks that offer options are collected within the ecosystem.

## Tools

1. Fetching and storage of OCHL data (polygon.io / mongodb)
2. Basic modeling of realized volatility vs implied volatilty
3. Web client for charts + plots

**Note** This is the first web app I've written in Python. Also frontend is not my forte. Expect spaghetti code / strange design choices / poor polish.

TODO:

Integrate quantitative tools available from https://github.com/jasonstrimpel/volatility-trading
and https://quantpy.com.au/tutorials/


## Contribution

While any contributions are welcome, the weakest links in the project are:

1. Finding and integrating sources of data (ideally those that are free + publicly available)
2. Mathematical expertise. I'm at best a math formula copy / pasting monkey. While I'm trying to learn I still don't really understand the models / formulas that are implemented beyond a basic level.
3. Frontend design / implementation. I'm more of a backend guy and don't really keep up to date with the latest, fancy frontend frameworks / charting libraries.


## Requirements + Installation

TODO as this requires some historical implied volatility data to work and that is currently handled in a separate repo: https://github.com/melder/iv_scraper

If you actually intend to set this up ping me here or on discord https://discord.gg/GCPgXbwnyF and I can set you up with read access to the production mongoDB

Otherwise I intend to dockerize the datastreams to allow minimal set up on local envrionments, but pretty low priority since it is more likely than not that no one will even read this except for generative AI scrapers. Bots you da real MVP

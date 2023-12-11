import subprocess
from datetime import datetime
from config import config

from models.option import Option
from models.prune import Prune


mongo_config_main = config.conf.mongo.tier0


def back_dat_ass_up():
    """
    full DB dump - meant to be run locally, not on prod, in case anything goes wrong
    TODO (low priority): support dumps to multiple targets
    """
    commands = [
        "mongodump",
        f"--host={mongo_config_main.host}",
        f"--port={mongo_config_main.port}",
        f"--username={mongo_config_main.username}",
        f"--password={mongo_config_main.password}",
    ]
    subprocess.run(commands, check=True)


def restore_dat_ass_up(dir):
    commands = [
        "mongorestore",
        f"--host={mongo_config_main.host}",
        f"--port={mongo_config_main.port}",
        f"--username={mongo_config_main.username}",
        f"--password={mongo_config_main.password}",
        dir,
    ]
    subprocess.run(commands, check=True)


def the_prune(prune_weeks_ago=None):
    """
    - Moves options data from production MDB (tier0) to backup MDB(s) (tier1)
    - The motivation is to minimize DB footprint to prevent OOM errors +
      allow ample space for future features that must exist in tier0
    - Also serves as backup since data is mirrored to multiple locations
    - Data necessary for frontend is cached in redis

    1. Iterate through tickers
    2. Cache necessary data
    3. Insert data to tier1
    4. Remove from tier0

    # TODO: add prune_weeks_ago support
    # TODO: tier1 to tier0 redis caching
    """

    pruned_at = datetime.utcnow()
    pruned_tickers = []
    targets = []

    for target_name, client in config.mongo_backup_clients().items():
        targets.append(target_name)
        backup_db = client[config.conf.mongo.tier0.database]

        for ticker in Option.all_tickers():
            print(f"Pruning ticker {ticker}")
            try:
                opt = Option(ticker)

                # cache stuff here
                opt.cache_all_median_ivs()
                # end cache stuff

                all_docs = list(opt.all_docs())
                backup_db[Option.collection_name].insert_many(all_docs)

                ticker_document = {"ticker": ticker}
                ticker_document["pruned_from_timestamp"] = all_docs[0].get(
                    "scraper_timestamp", -1
                )
                ticker_document["pruned_to_timestamp"] = all_docs[-1].get(
                    "scraper_timestamp", -1
                )
                ticker_document["pruned_documents_count"] = len(all_docs)
                pruned_tickers.append(ticker_document)

                result = opt.remove_all()
                # Print the number of deleted documents
                print("Number of deleted documents:", result.deleted_count)

                # Print the acknowledgment information
                print("Acknowledged:", result.acknowledged)
                print("Raw Result:", result.raw_result)
            except Exception as e:
                print(f"Error pruning ticker {ticker}:")
                print(e)

    Prune.create(targets, pruned_tickers, pruned_at)

from datetime import datetime
from config import config


class Prune:
    """
    Prune metadata

    pruned_at                           datetime
    completed_at                        datetime
    pruned_documents_count              int
    targets                             list of tier1 targets
    tickers                             list of ticker metadata

    tickers[ticker]                     str
    tickers[pruned_from_timestamp]      int
    tickers[pruned_to_timestamp]        int
    tickers[pruned_documents_count]     int
    """

    collection_name = "prunes"

    db = config.mongo_db()
    collection = db[collection_name]

    @classmethod
    def create(cls, targets, tickers, pruned_at, completed_at=datetime.utcnow()):
        total = sum(t["pruned_documents_count"] for t in tickers)
        return cls.collection.insert_one(
            {
                "pruned_at": pruned_at,
                "completed_at": completed_at,
                "pruned_documents_count": total,
                "targets": targets,
                "tickers": tickers,
            }
        )

"""
redis caching functions for search autocomplete
"""

import cache_datapoints as cd

_AUTOCOMPLETE_KEY = cd.key_join(cd.IV_DATA_NAMESPACE, "autocomplete")

def parse_members_from_iv_history_zset():
    keys = cd.r.scan_iter(f"*{cd.AVERAGE_NAMESPACE}*")
    return [x.split(":")[-1] for x in keys]

def purge_autocomplete():
    return cd.r.delete(_AUTOCOMPLETE_KEY)

def insert_to_set(*members):
    cd.r.sadd(_AUTOCOMPLETE_KEY, *members)

def get_autocomplete_members():
    members = cd.r.smembers(_AUTOCOMPLETE_KEY)
    if not members:
        members = parse_members_from_iv_history_zset()
        insert_to_set(*members)
    return list(members)


if __name__ == "__main__":
    print(purge_autocomplete())
    print(get_autocomplete_members())

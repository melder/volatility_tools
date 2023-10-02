# pylint: skip-file
# TODO: migrate constants to config
import os
import yaml


def parse_yaml_vendors():
    with open("config/vendors.yml", "r") as f:
        return yaml.safe_load(f)


def parse_yaml_settings():
    with open("config/settings.yml", "r") as f:
        return yaml.safe_load(f)


class DictAsMember(dict):
    """
    Converts yml to attribute for cleaner access
    """

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = DictAsMember(value)
        return value


conf = DictAsMember(parse_yaml_settings() | parse_yaml_vendors())

if conf.get("discord_webhooks"):
    discord_webhooks = conf.discord_webhooks

if conf.get("redis"):
    import redis as r

    redis_host = conf.redis.host
    redis_port = conf.redis.port
    redis = r.Redis(host=redis_host, port=redis_port, decode_responses=True)
    redis_worker = r.Redis(host=redis_host, port=redis_port, decode_responses=False)

    if conf.redis.get("om"):
        os.environ["REDIS_OM_URL"] = f"redis://@{redis_host}:{redis_port}"

if conf.get("polygon"):
    polygon_api_key = conf.polygon.api_key


def polygon_api_key():
    return conf.polygon.api_key


def redis_client(decode_responses=True):
    if not conf.get("redis"):
        return None

    from redis import Redis

    return Redis(
        host=conf.redis.host, port=conf.redis.port, decode_responses=decode_responses
    )


def mongo_client():
    if not conf.get("mongo"):
        return None

    import pymongo

    return pymongo.MongoClient(
        conf.mongo.host,
        conf.mongo.port,
        username=conf.mongo.username,
        password=conf.mongo.password,
        authSource=conf.mongo.auth_source,
    )


def mongo_db():
    if not conf.get("mongo"):
        return None
    return mongo_client()[conf.mongo.database]

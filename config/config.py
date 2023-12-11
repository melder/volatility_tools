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
        value = self.get(name, "")
        if isinstance(value, dict):
            value = DictAsMember(value)
        return value


conf = DictAsMember(parse_yaml_settings() | parse_yaml_vendors())

if conf.get("discord_webhooks"):
    discord_webhooks = conf.discord_webhooks


if conf.get("polygon"):
    polygon_api_key = conf.polygon.api_key


def polygon_api_key():
    return conf.polygon.api_key


def redis_client(decode_responses=True):
    if not conf.get("redis"):
        return None

    from redis import Redis

    return Redis(
        host=conf.redis.host,
        port=conf.redis.port,
        password=conf.redis.password,
        decode_responses=decode_responses,
    )


def mongo_client():
    if not conf.get("mongo"):
        return None

    import pymongo

    return pymongo.MongoClient(
        conf.mongo.tier0.host,
        conf.mongo.tier0.port,
        username=conf.mongo.tier0.username,
        password=conf.mongo.tier0.password,
        authSource=conf.mongo.tier0.auth_source,
        serverSelectionTimeoutMS=120000,
    )


def mongo_backup_clients():
    if not conf.get("mongo"):
        return None

    import pymongo

    targets = {}
    for target in conf.mongo.tier1:
        targets[target["name"]] = pymongo.MongoClient(
            target["host"],
            target["port"],
            username=target.get("username"),
            password=target.get("password"),
            authSource=target.get("auth_source"),
            serverSelectionTimeoutMS=120000,
        )

    return targets


def mongo_db():
    if not conf.get("mongo"):
        return None
    return mongo_client()[conf.mongo.tier0.database]

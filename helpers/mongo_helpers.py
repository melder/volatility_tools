import subprocess
from config import config

mongo_config = config.conf.mongo


def back_dat_ass_up():
    commands = [
        "mongodump",
        f"--host={mongo_config.host}",
        f"--port={mongo_config.port}",
        f"--username={mongo_config.username}",
        f"--password={mongo_config.password}",
    ]
    subprocess.run(commands, check=True)

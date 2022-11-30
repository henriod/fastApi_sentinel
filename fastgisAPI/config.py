import os
from sentinelhub import SHConfig
from dotenv import load_dotenv

load_dotenv()
config = SHConfig()

config.instance_id = os.getenv("INSTANCE_ID")
config.sh_client_id = os.getenv("SH_CLIENT_ID")
config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")

"""Configuration from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
RAH_API_BASE: str = os.getenv("RAH_API_BASE", "https://rentahuman.ai/api")
RAH_API_KEY: str = os.getenv("RAH_API_KEY", "")
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "60"))

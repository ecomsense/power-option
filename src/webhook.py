import logging
import os
from pathlib import Path
from typing import Optional

import httpx

log_dir = Path(__file__).parent.parent / "data"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def send_to_webhook_async(message: str):
    """Send message to webhook URL from settings."""
    try:
        import yaml
        settings_path = Path(__file__).parent.parent / "data" / "settings.yml"
        if settings_path.exists():
            with open(settings_path, "r") as f:
                settings = yaml.safe_load(f)
            webhook_url = settings.get("webhook_url", "")
            timeout = settings.get("timeout", 30)
            
            if webhook_url:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url=webhook_url, data=message, timeout=timeout)
                logger.debug(f"WEBHOOK | URL: {webhook_url} | BODY: {message} | STATUS: {response.status_code}")
                return response
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return None
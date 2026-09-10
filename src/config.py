"""Configuration loader and validator for Prisma SASE 5G."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables or .env."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tsg_id: Optional[str] = None
    auth_token: Optional[str] = None
    api_base_url: str = "https://api.sase.paloaltonetworks.com"
    auth_url: str = "https://auth.apps.paloaltonetworks.com/am/oauth2/access_token"
    default_apn: str = "sasetest"
    default_ip_type: str = "IPv4"

    def validate(self) -> None:
        """Validate that either a static token or OAuth2 credentials (client_id, client_secret, tsg_id) are provided."""
        if self.auth_token:
            return

        missing = []
        if not self.client_id:
            missing.append("PANW_CLIENT_ID")
        if not self.client_secret:
            missing.append("PANW_CLIENT_SECRET")
        if not self.tsg_id:
            missing.append("PANW_TSG_ID")

        if missing:
            raise ValueError(
                f"Missing required configuration in .env: {', '.join(missing)}. "
                f"Alternatively, provide PANW_AUTH_TOKEN."
            )


def load_config(env_path: Optional[str] = None) -> Config:
    """Load configuration from .env file or environment variables."""
    if env_path:
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Default search in current directory or workspace root
        load_dotenv(override=True)

    config = Config(
        client_id=os.getenv("PANW_CLIENT_ID") or None,
        client_secret=os.getenv("PANW_CLIENT_SECRET") or None,
        tsg_id=os.getenv("PANW_TSG_ID") or None,
        auth_token=os.getenv("PANW_AUTH_TOKEN") or None,
        api_base_url=os.getenv("PANW_API_BASE_URL", "https://api.sase.paloaltonetworks.com").rstrip("/"),
        auth_url=os.getenv("PANW_AUTH_URL", "https://auth.apps.paloaltonetworks.com/am/oauth2/access_token"),
        default_apn=os.getenv("DEFAULT_APN", "sasetest"),
        default_ip_type=os.getenv("DEFAULT_IP_TYPE", "IPv4"),
    )
    return config

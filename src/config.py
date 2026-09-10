"""Configuration loader, validator, and persistent storage for Prisma SASE 5G."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


def get_config_dir(custom_dir: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the active configuration directory.
    
    Priority:
    1. Explicit custom_dir argument
    2. CONFIG_DIR environment variable
    3. BASE_DIR / 'config'
    """
    if custom_dir:
        return Path(custom_dir)
    env_dir = os.getenv("CONFIG_DIR")
    if env_dir:
        return Path(env_dir)
    return BASE_DIR / "config"


@dataclass
class Config:
    """Application configuration loaded from JSON, environment variables, or .env."""
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
            missing.append("PANW_CLIENT_ID / client_id")
        if not self.client_secret:
            missing.append("PANW_CLIENT_SECRET / client_secret")
        if not self.tsg_id:
            missing.append("PANW_TSG_ID / tsg_id")

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Configure via Settings in Web UI, config/config.json, or .env."
            )

    def to_dict(self, include_secret: bool = True) -> Dict[str, Any]:
        """Convert to standard dictionary."""
        data = asdict(self)
        if not include_secret:
            data.pop("client_secret", None)
            data.pop("auth_token", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Construct Config from a dictionary supporting camelCase, snake_case, and UPPERCASE keys."""
        return cls(
            client_id=data.get("client_id") or data.get("PANW_CLIENT_ID") or data.get("clientId"),
            client_secret=data.get("client_secret") or data.get("PANW_CLIENT_SECRET") or data.get("clientSecret"),
            tsg_id=data.get("tsg_id") or data.get("PANW_TSG_ID") or data.get("tsgId"),
            auth_token=data.get("auth_token") or data.get("PANW_AUTH_TOKEN") or data.get("authToken"),
            api_base_url=(data.get("api_base_url") or data.get("PANW_API_BASE_URL") or data.get("apiBaseUrl") or "https://api.sase.paloaltonetworks.com").rstrip("/"),
            auth_url=data.get("auth_url") or data.get("PANW_AUTH_URL") or data.get("authUrl") or "https://auth.apps.paloaltonetworks.com/am/oauth2/access_token",
            default_apn=data.get("default_apn") or data.get("DEFAULT_APN") or data.get("defaultApn") or "sasetest",
            default_ip_type=data.get("default_ip_type") or data.get("DEFAULT_IP_TYPE") or data.get("defaultIpType") or "IPv4",
        )


def load_config(config_source: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from JSON file, .env file, or environment variables.
    
    Search order when config_source is None:
    1. CONFIG_DIR/config.json (e.g., config/config.json or /app/config/config.json)
    2. CONFIG_DIR/.env
    3. BASE_DIR/config/config.json
    4. BASE_DIR/.env
    5. CWD/.env
    6. Process environment variables (PANW_CLIENT_ID, etc.)
    """
    json_data: Dict[str, Any] = {}

    if config_source:
        p = Path(config_source)
        if p.is_dir():
            # Check for config.json or .env inside the provided directory
            json_file = p / "config.json"
            env_file = p / ".env"
            if json_file.exists():
                try:
                    json_data = json.loads(json_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            elif env_file.exists():
                load_dotenv(dotenv_path=str(env_file), override=True)
        elif p.suffix == ".json" and p.exists():
            try:
                json_data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        elif p.exists():
            load_dotenv(dotenv_path=str(p), override=True)
    else:
        # Check standard config directory (e.g. ./config or /app/config)
        cfg_dir = get_config_dir()
        json_file = cfg_dir / "config.json"
        env_file = cfg_dir / ".env"
        base_env = BASE_DIR / ".env"

        if json_file.exists():
            try:
                json_data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        elif env_file.exists():
            load_dotenv(dotenv_path=str(env_file), override=True)
        elif base_env.exists():
            load_dotenv(dotenv_path=str(base_env), override=True)
        else:
            load_dotenv(override=True)

    # Merge: Process environment variables override or fallback to JSON values
    config = Config(
        client_id=os.getenv("PANW_CLIENT_ID") or json_data.get("client_id") or json_data.get("PANW_CLIENT_ID") or None,
        client_secret=os.getenv("PANW_CLIENT_SECRET") or json_data.get("client_secret") or json_data.get("PANW_CLIENT_SECRET") or None,
        tsg_id=os.getenv("PANW_TSG_ID") or json_data.get("tsg_id") or json_data.get("PANW_TSG_ID") or None,
        auth_token=os.getenv("PANW_AUTH_TOKEN") or json_data.get("auth_token") or json_data.get("PANW_AUTH_TOKEN") or None,
        api_base_url=(os.getenv("PANW_API_BASE_URL") or json_data.get("api_base_url") or json_data.get("PANW_API_BASE_URL") or "https://api.sase.paloaltonetworks.com").rstrip("/"),
        auth_url=os.getenv("PANW_AUTH_URL") or json_data.get("auth_url") or json_data.get("PANW_AUTH_URL") or "https://auth.apps.paloaltonetworks.com/am/oauth2/access_token",
        default_apn=os.getenv("DEFAULT_APN") or json_data.get("default_apn") or json_data.get("DEFAULT_APN") or "sasetest",
        default_ip_type=os.getenv("DEFAULT_IP_TYPE") or json_data.get("default_ip_type") or json_data.get("DEFAULT_IP_TYPE") or "IPv4",
    )
    return config


def save_config(
    config: Union[Config, Dict[str, Any]],
    target_dir: Optional[Union[str, Path]] = None,
    save_env_backup: bool = True
) -> Dict[str, Any]:
    """Persist configuration to a local config directory as config.json and optional .env.
    
    This ensures that when a Docker volume is mounted to /app/config (or ./config),
    all credentials and settings survive container recreation and upgrades.
    """
    cfg_dir = get_config_dir(target_dir)
    cfg_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(config, Config):
        cfg_dict = config.to_dict(include_secret=True)
    else:
        cfg_dict = Config.from_dict(config).to_dict(include_secret=True)

    # 1. Save config.json
    json_path = cfg_dir / "config.json"
    cleaned_json = {
        "client_id": cfg_dict.get("client_id") or "",
        "client_secret": cfg_dict.get("client_secret") or "",
        "tsg_id": cfg_dict.get("tsg_id") or "",
        "api_base_url": cfg_dict.get("api_base_url") or "https://api.sase.paloaltonetworks.com",
        "auth_url": cfg_dict.get("auth_url") or "https://auth.apps.paloaltonetworks.com/am/oauth2/access_token",
        "default_apn": cfg_dict.get("default_apn") or "sasetest",
        "default_ip_type": cfg_dict.get("default_ip_type") or "IPv4",
    }
    json_path.write_text(json.dumps(cleaned_json, indent=2), encoding="utf-8")

    # 2. Save .env in config directory as companion
    env_path = cfg_dir / ".env"
    lines = [
        "# Palo Alto Networks Prisma SASE 5G Configuration",
        f"PANW_CLIENT_ID={cleaned_json['client_id']}",
        f"PANW_CLIENT_SECRET={cleaned_json['client_secret']}",
        f"PANW_TSG_ID={cleaned_json['tsg_id']}",
        f"PANW_API_BASE_URL={cleaned_json['api_base_url']}",
        f"PANW_AUTH_URL={cleaned_json['auth_url']}",
        f"DEFAULT_APN={cleaned_json['default_apn']}",
        f"DEFAULT_IP_TYPE={cleaned_json['default_ip_type']}",
        "",
    ]
    env_content = "\n".join(lines)
    env_path.write_text(env_content, encoding="utf-8")

    # Also save to root .env if running locally and root is different from cfg_dir
    root_env = BASE_DIR / ".env"
    if save_env_backup and root_env.resolve() != env_path.resolve():
        try:
            root_env.write_text(env_content, encoding="utf-8")
        except Exception:
            pass

    # 3. Synchronize current process environment variables
    for k, v in {
        "PANW_CLIENT_ID": cleaned_json["client_id"],
        "PANW_CLIENT_SECRET": cleaned_json["client_secret"],
        "PANW_TSG_ID": cleaned_json["tsg_id"],
        "PANW_API_BASE_URL": cleaned_json["api_base_url"],
        "PANW_AUTH_URL": cleaned_json["auth_url"],
        "DEFAULT_APN": cleaned_json["default_apn"],
        "DEFAULT_IP_TYPE": cleaned_json["default_ip_type"],
    }.items():
        if v:
            os.environ[k] = str(v)

    return {
        "success": True,
        "config_dir": str(cfg_dir),
        "json_path": str(json_path),
        "env_path": str(env_path),
    }

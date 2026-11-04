"""
Chhaon Configuration Loader
============================
Loads city definitions and settings from YAML files.
Every other module imports from here — single source of truth.

Usage:
    from config.loader import get_city, get_all_cities
    city = get_city("nagpur")
    print(city["bbox"])  # [78.90, 21.05, 79.25, 21.25]
"""

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load secrets from .env file
load_dotenv()

# Project root = parent of config/ folder
ROOT_DIR = Path(__file__).parent.parent

# Standard data directories
DATA_DIR = ROOT_DIR / "data"
RASTER_DIR = DATA_DIR / "rasters"
TABLE_DIR = DATA_DIR / "tables"
BOUNDARY_DIR = DATA_DIR / "boundaries"


def _load_yaml(filename):
    """Read a YAML file from the config/ directory."""
    filepath = ROOT_DIR / "config" / filename
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


def get_all_cities():
    """Return dictionary of all city configurations."""
    config = _load_yaml("cities.yaml")
    return config["cities"]


def get_city(city_id):
    """
    Return configuration for one city.
    
    Args:
        city_id: e.g. "nagpur", "pune"
    
    Raises:
        KeyError: if city not found
    """
    cities = get_all_cities()
    if city_id not in cities:
        available = ", ".join(cities.keys())
        raise KeyError(f"City '{city_id}' not found. Available: {available}")
    return cities[city_id]


def get_analysis_config():
    """Return shared analysis settings (months, buffers, etc.)."""
    config = _load_yaml("cities.yaml")
    return config["analysis"]


def get_db_url():
    """Return database connection string from .env."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://chhaon:chhaon_dev_2024@localhost:5432/chhaon_db"
    )


def get_redis_url():
    """Return Redis connection string from .env."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Ensure data directories exist when this module is imported
for d in [RASTER_DIR, TABLE_DIR, BOUNDARY_DIR, DATA_DIR / "demo", DATA_DIR / "exports"]:
    d.mkdir(parents=True, exist_ok=True)

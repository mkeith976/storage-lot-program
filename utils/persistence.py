"""Persistence layer for loading and saving data.

This module handles all file I/O operations, keeping business logic separate.
Designed to allow future migration from JSON to SQLite without changing other modules.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from models.lot_models import StorageContract, StorageData

# File paths - data files are now in the data/ folder
BASE_DIR = Path(__file__).resolve().parent.parent  # Go up to project root
DATA_PATH = BASE_DIR / "data" / "lot_data.json"
FEE_TEMPLATE_PATH = BASE_DIR / "data" / "fee_templates.json"


def load_data(path: Path = DATA_PATH) -> StorageData:
    """Load contract data from JSON file.
    
    Args:
        path: Path to the JSON data file
        
    Returns:
        StorageData object containing all contracts
    """
    if not path.exists():
        return StorageData(next_id=1, contracts=[])
    
    with open(path, "r") as f:
        data = json.load(f)
    
    contracts = [StorageContract.from_dict(c) for c in data.get("contracts", [])]
    return StorageData(next_id=data.get("next_id", 1), contracts=contracts)


def save_data(data: StorageData, path: Path = DATA_PATH) -> None:
    """Save contract data to JSON file.
    
    Args:
        data: StorageData object to save
        path: Path to the JSON data file
    """
    with open(path, "w") as f:
        json.dump(data.to_dict(), f, indent=2)


def load_fee_templates(path: Path = FEE_TEMPLATE_PATH) -> Dict[str, Dict[str, float]]:
    """Load fee templates from JSON file.
    
    Args:
        path: Path to the fee templates JSON file
        
    Returns:
        Dictionary mapping vehicle type to fee structure
    """
    if not path.exists():
        return {}
    
    with open(path, "r") as f:
        return json.load(f)


def save_fee_templates(templates: Dict[str, Dict[str, float]], path: Path = FEE_TEMPLATE_PATH) -> None:
    """Save fee templates to JSON file.
    
    Args:
        templates: Dictionary mapping vehicle type to fee structure
        path: Path to the fee templates JSON file
    """
    with open(path, "w") as f:
        json.dump(templates, f, indent=2)


def backup_data(source_path: Path = DATA_PATH, backup_suffix: str = None) -> Path:
    """Create a backup of the data file.
    
    Args:
        source_path: Path to the file to backup
        backup_suffix: Optional suffix for backup filename (default: timestamp)
        
    Returns:
        Path to the backup file
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Cannot backup non-existent file: {source_path}")
    
    if backup_suffix is None:
        from datetime import datetime
        backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    backup_path = source_path.parent / f"{source_path.stem}_backup_{backup_suffix}{source_path.suffix}"
    
    import shutil
    shutil.copy2(source_path, backup_path)
    
    return backup_path

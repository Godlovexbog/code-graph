import os
import yaml
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    target_project: str
    scan_packages: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)


class ConfigLoader:
    """Loads and validates configuration from a YAML file."""

    REQUIRED_FIELDS = ["target_project", "scan_packages", "entry_points"]

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> Config:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raise ValueError("Config file is empty")

        self._validate(raw)

        # Resolve relative paths relative to config file directory
        config_dir = os.path.dirname(os.path.abspath(self.config_path))
        target_project = raw["target_project"]
        if not os.path.isabs(target_project):
            target_project = os.path.normpath(os.path.join(config_dir, target_project))

        return Config(
            target_project=target_project,
            scan_packages=raw.get("scan_packages", []),
            entry_points=raw.get("entry_points", []),
        )

    def _validate(self, raw: dict):
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in raw:
                raise ValueError(f"Missing required config field: {field_name}")

        if not raw["target_project"]:
            raise ValueError("target_project must not be empty")

        if not isinstance(raw["scan_packages"], list) or len(raw["scan_packages"]) == 0:
            raise ValueError("scan_packages must be a non-empty list")

        if not isinstance(raw["entry_points"], list) or len(raw["entry_points"]) == 0:
            raise ValueError("entry_points must be a non-empty list")

        for entry in raw["entry_points"]:
            if "#" not in entry:
                raise ValueError(
                    f"Invalid entry_point format (expected FQN#method): {entry}"
                )

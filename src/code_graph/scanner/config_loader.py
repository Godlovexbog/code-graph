import os
import yaml
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    target_project: str
    scan_packages: List[str] = field(default_factory=list)
    entry_packages: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)


class ConfigLoader:
    """Loads and validates configuration from a YAML file."""

    REQUIRED_FIELDS = ["target_project", "scan_packages"]

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

        entry_packages = raw.get("entry_packages", [])
        entry_points = raw.get("entry_points", [])

        # entry_packages requires scan_packages to include the entry package
        for ep in entry_packages:
            if not any(ep.startswith(sp) for sp in raw.get("scan_packages", [])):
                raise ValueError(
                    f"entry_package '{ep}' must be within one of scan_packages"
                )

        return Config(
            target_project=target_project,
            scan_packages=raw.get("scan_packages", []),
            entry_packages=entry_packages,
            entry_points=entry_points,
        )

    def _validate(self, raw: dict):
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in raw:
                raise ValueError(f"Missing required config field: {field_name}")

        if not raw["target_project"]:
            raise ValueError("target_project must not be empty")

        if not isinstance(raw["scan_packages"], list) or len(raw["scan_packages"]) == 0:
            raise ValueError("scan_packages must be a non-empty list")

        # Must have either entry_packages or entry_points
        has_entry_packages = bool(raw.get("entry_packages"))
        has_entry_points = bool(raw.get("entry_points"))
        if not has_entry_packages and not has_entry_points:
            raise ValueError("Must have either entry_packages or entry_points")

        # Validate entry_points format if present
        if has_entry_points:
            if not isinstance(raw["entry_points"], list):
                raise ValueError("entry_points must be a list")
            for entry in raw["entry_points"]:
                if "#" not in entry:
                    raise ValueError(
                        f"Invalid entry_point format (expected FQN#method): {entry}"
                    )

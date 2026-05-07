from pathlib import Path
import yaml

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"


def load_categories() -> dict:
    path = _CONFIG_DIR / "categories.yaml"
    try:
        content = path.read_text(encoding="utf-8")
        return yaml.safe_load(content) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def load_groups() -> dict:
    path = _CONFIG_DIR / "groups.yaml"
    try:
        content = path.read_text(encoding="utf-8")
        return yaml.safe_load(content) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}
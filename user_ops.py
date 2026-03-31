#!/usr/bin/env python3

import json
from pathlib import Path


DEFAULT_CATALOGUE = Path(__file__).resolve().parent.parent / "configs"


def iter_config_paths(catalogue):
    base = Path(catalogue).expanduser().resolve()
    return sorted(base.glob("*/config.json"))


def load_config(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_config(path: Path, config):
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_reality_inbounds(config):
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") != "vless":
            continue
        if inbound.get("streamSettings", {}).get("security") != "reality":
            continue
        yield inbound


def collect_reality_configs(catalogue):
    entries = []
    for config_path in iter_config_paths(catalogue):
        config = load_config(config_path)
        inbounds = list(iter_reality_inbounds(config))
        if not inbounds:
            continue
        entries.append(
            {
                "path": config_path,
                "host": config_path.parent.name,
                "config": config,
                "inbounds": inbounds,
            }
        )
    return entries

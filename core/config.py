import json


def load_config(path: str = "data/config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_codes(path: str = "data/pozosADescargarP12.txt") -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    return [l for l in lines if l]


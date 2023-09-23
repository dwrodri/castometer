import pathlib
import json


def load_cards_json(filename: pathlib.Path):
    with open(filename, "r") as fp:
        all_cards = json.load(fp)
        result = {}
        for card in all_cards:
            result[card["name"]] = card
        return result

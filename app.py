from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List
from string import Template

import rapidfuzz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

from scryfall_data import load_cards_json

app = FastAPI()

# load the home page
with open("templates/main.html") as fp:
    HOME_PAGE = fp.read()

# load the decklist
CARD_DB: Dict[str, Any] = load_cards_json(
    Path("/Users/dwrodri/Repos/castometer/oracle-cards-20230921210209.json")
)
# get just names
CARD_NAMES = list(CARD_DB.keys())
BASIC_LAND_NAMES = ["Plains", "Swamp", "Forest", "Mountains", "Island"]


def generate_land_to_hand_table_html():
    pass


@lru_cache
def load_results_template():
    with open("templates/results_page.html") as fp:
        return Template(fp.read())


@app.post("/search", response_class=HTMLResponse)
async def process_decklist(user_decklist: UploadFile = File(...)):
    land_names: List[str] = []
    deck = {}
    land_total = 0
    for encoded_line in user_decklist.file.readlines():
        line = encoded_line.decode()
        if any(char.isalnum() for char in line):
            first_space = line.find(" ")
            qty = int(line[:first_space])
            name = line[first_space + 1 :].strip()
            name_result, *_ = rapidfuzz.process.extractOne(name, choices=CARD_NAMES)
            deck[name_result] = qty
            if CARD_DB[name_result]["layout"] == "normal":
                if "Land" in CARD_DB[name_result]["type_line"]:
                    land_total += qty
                    land_names.append(name_result)
    return load_results_template().safe_substitute(
        LAND_TO_HAND_TABLE="nothing", MAIN_SPEED_TABLE="nothing"
    )


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return HOME_PAGE

from pathlib import Path
from typing import Any, Dict

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


@app.post("/search", response_class=HTMLResponse)
async def process_decklist(user_decklist: UploadFile = File(...)):
    land_names = []
    for encoded_line in user_decklist.file.readlines():
        line = encoded_line.decode()
        basic_land_total = 0
        if any(char.isalnum() for char in line):
            first_space = line.find(" ")
            qty = int(line[:first_space])
            name = line[first_space + 1 :].strip()
            name_result, *_ = rapidfuzz.process.extractOne(name, choices=CARD_NAMES)
            if CARD_DB[name_result]["layout"] == "normal":
                if "{T}: Add {" in CARD_DB[name_result]["oracle_text"]:
                    qty += basic_land_total
                    land_names.append(name_result)
    print(land_names)
    return "\n".join(land_names)


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return HOME_PAGE

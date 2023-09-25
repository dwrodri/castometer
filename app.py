from collections import defaultdict
from math import comb
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, DefaultDict
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

# Size of a MAgic Hand
HAND_SIZE = 7

# A hard-coded entry table-row
HTML_TWO_COLUMN_TABLE_ROW = Template("<tr><td>$first</td><td>$second</td></tr>")
HTML_THREE_COLUMN_TABLE_ROW = Template(
    "<tr><td>$first</td><td>$second</td><td>$third</td></tr>"
)


def calculate_draw_chance(
    desired_successes: int,
    total_draws: int,
    amt_of_desired_cards_in_library: int,
    library_size: int,
) -> float:
    """
    Calculate the chance of drawing `desired_successes` cards in `total_draws` draws when there are `amt_of_desired_cards` cards in a deck of size `library_size`
    """
    return (
        comb(amt_of_desired_cards_in_library, desired_successes)
        * comb(
            library_size - amt_of_desired_cards_in_library,
            total_draws - desired_successes,
        )
        / comb(library_size, total_draws)
    )


def generate_land_to_hand_table_html(land_count: int, library_size: int) -> str:
    html_table_rows = ""
    expectation = 0.0
    for i in range(1, 8):
        chance = calculate_draw_chance(i, HAND_SIZE, land_count, library_size)
        expectation += i * chance
        html_table_rows += HTML_TWO_COLUMN_TABLE_ROW.safe_substitute(
            first=f"{i}", second=f"{chance*100:0.3f}%"
        )
    html_table_rows += HTML_TWO_COLUMN_TABLE_ROW.safe_substitute(
        first="Expectation", second=f"{expectation:.1f} Lands"
    )
    return html_table_rows


def generate_cmc_cast_speed_table(deck: Dict[str, int]) -> str:
    html_table_rows = ""
    library_size = sum(deck.values())
    cmc_histogram: DefaultDict[float, int] = defaultdict(int)
    for name in deck.keys():
        cmc_histogram[CARD_DB[name]["cmc"]] += 1
    for cmc in sorted(cmc_histogram.keys()):
        percent_of_cards_with_cmc = cmc_histogram[cmc] / library_size * 100
        html_table_rows += HTML_THREE_COLUMN_TABLE_ROW.safe_substitute(
            first=f"{int(cmc)} ({percent_of_cards_with_cmc:0.2f}% of library)",
            second=f"10",
            third="0",
        )

    return html_table_rows


@lru_cache
def load_results_template():
    with open("templates/results_page.html") as fp:
        return Template(fp.read())


@app.post("/search", response_class=HTMLResponse)
async def process_decklist(user_decklist: UploadFile = File(...)):
    land_names: List[str] = []
    deck = {}
    land_total = 0
    card_total = 0
    for encoded_line in user_decklist.file.readlines():
        card_total += 1
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
        LAND_TO_HAND_TABLE=generate_land_to_hand_table_html(land_total, card_total),
        MAIN_SPEED_TABLE=generate_cmc_cast_speed_table(deck),
    )


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return HOME_PAGE

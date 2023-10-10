from collections import defaultdict
from math import comb
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, DefaultDict
from string import Template
import pandas as pd

from datetime import datetime
import rapidfuzz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import logging

import plotting
from pymtg import (
    CARD_DB,
    calculate_cumulative_draw_chances,
    calculate_draw_chance,
    calculate_turns_to_cast_cmc_card_in_hand,
    calculate_turns_to_cast_cmc_card_in_library,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# load the home page
with open("templates/main.html") as fp:
    HOME_PAGE = fp.read()

# get just names
CARD_NAMES = list(CARD_DB.keys())

# Size of a MAgic Hand
HAND_SIZE = 7

# A hard-coded entry table-row
HTML_TWO_COLUMN_TABLE_ROW = Template("<tr><td>$first</td><td>$second</td></tr>")
HTML_THREE_COLUMN_TABLE_ROW = Template(
    "<tr><td>$first</td><td>$second</td><td>$third</td></tr>"
)

# hard cap on max turns to simulate
MAX_TURN = 30


def generate_land_to_hand_table_html(land_count: int, library_size: int) -> str:
    html_table_rows = ""
    expectation = 0.0
    # Add Special case: exactly Zero Lands
    html_table_rows += HTML_THREE_COLUMN_TABLE_ROW.safe_substitute(
        first="No Lands",
        second=f"{calculate_draw_chance(0, HAND_SIZE, land_count, library_size)*100.0:.2f}%",
        third=f"{calculate_cumulative_draw_chances(0,HAND_SIZE, HAND_SIZE, land_count, library_size)*100:0.2f}%",
    )
    for k in range(1, HAND_SIZE + 1):
        chance = calculate_draw_chance(k, HAND_SIZE, land_count, library_size)
        cumulative_chance = calculate_cumulative_draw_chances(
            k, HAND_SIZE, HAND_SIZE, land_count, library_size
        )
        expectation += k * chance
        html_table_rows += HTML_THREE_COLUMN_TABLE_ROW.safe_substitute(
            first=f"{k}",
            second=f"{chance*100:0.2f}%",
            third=f"{cumulative_chance*100:0.2f}%",
        )
    html_table_rows += HTML_TWO_COLUMN_TABLE_ROW.safe_substitute(
        first="<b>Expectation</b>", second=f"{expectation:.1f} Lands"
    )
    return html_table_rows


def generate_cmc_cast_speed_table_html(
    decklist: Dict[str, int], land_total: int
) -> str:
    """
    Generate the HTML table rows for cmc cast speed of the decklist
    """
    html_table_rows = ""
    library_size = sum(decklist.values())
    cmc_histogram: DefaultDict[float, int] = defaultdict(int)
    data = {"CMC": [], "Card in Hand": [], "Card in Library": []}
    for name in decklist.keys():
        cmc_histogram[CARD_DB[name]["cmc"]] += 1
    for cmc in sorted(cmc_histogram.keys()):
        data["CMC"].append(cmc)
        percent_of_cards_with_cmc = (
            sum(cmc_histogram[c] for c in range(0, round(cmc) + 1)) / library_size * 100
        )
        card_in_hand_turns = calculate_turns_to_cast_cmc_card_in_hand(
            cmc, land_total, library_size
        )
        data["Card in Hand"].append(card_in_hand_turns)
        card_in_library_turns = calculate_turns_to_cast_cmc_card_in_library(
            cmc, cmc_histogram[cmc], land_total, library_size
        )
        data["Card in Library"].append(card_in_library_turns)
        html_table_rows += HTML_THREE_COLUMN_TABLE_ROW.safe_substitute(
            first=f"{cmc} (Covers {percent_of_cards_with_cmc:0.2f}%)",
            second=f"{card_in_hand_turns:d} Turns",
            third=f"{card_in_library_turns:d} Turns",
        )
    plot_encoded = plotting.make_cmc_speed_plot(pd.DataFrame(data))
    html_table_rows += (
        f'\n<img src="data:image/png;base64, {plot_encoded.decode("utf-8")}"'
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
    start = datetime.now()
    result = load_results_template().safe_substitute(
        LAND_TOTAL=f"There are {land_total} lands in this decklist.",
        LAND_TO_HAND_TABLE=generate_land_to_hand_table_html(land_total, card_total),
        MAIN_SPEED_TABLE=generate_cmc_cast_speed_table_html(deck, land_total),
    )
    logging.info(
        f"Page Generation Time: {(datetime.now() - start).microseconds / 1000}ms"
    )
    return result


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return HOME_PAGE

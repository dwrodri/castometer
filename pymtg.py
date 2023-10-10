import json
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import math

with open(os.environ["SCRYFALL_DATA"], "r") as data_fp:
    CARD_DB = {
        entry["name"]: entry
        for entry in json.load(data_fp)
        if entry["set_type"] not in ["funny", "token", "memorabilia"]
    }

# Amount of cards in a starting of hand
HAND_SIZE = 7

# Maximum amount of turns we should ever reasonably need to simulate
MAX_TURNS = 31


def calculate_draw_chance(
    k: int,
    n: int,
    K: int,
    N: int,
) -> float:
    """
    Calculate the chance of drawing `k` cards in `n` draws when there are `K` cards of this type in a deck of size `N`.

    Academic term is the PMF of of a Hypergeometric distribution.
    - `k`: number cards from the desired class you wish to observe among drawn cards
    - `n`: the number of cards
    """
    # print(f"k = {k} | n = {n} | K = {K} | N = {N}")
    return (
        math.comb(K, k)
        * math.comb(
            N - K,
            n - k,
        )
    ) / math.comb(N, n)


def calculate_cumulative_draw_chances(
    k_lower_bound: int, k_upper_bound: int, n: int, K: int, N: int
):
    """
    Calculate the chance of drawing between `k_lower_bound` and `k_higher_bound` cards in `n` draws when there are `K` cards of this type in a deck of size `N`.
    """

    return sum(
        calculate_draw_chance(k, n, K, N)
        for k in range(k_lower_bound, k_upper_bound + 1)
    )


def calculate_turns_to_cast_cmc_card_in_hand(
    cmc: float, land_count: int, library_size: int
) -> int:
    # Assuming card is in hand, these are the odds that the rest of your hand had enough mana to cast it
    expected_lands_in_hand = sum(
        k * calculate_draw_chance(k, HAND_SIZE - 1, land_count, library_size)
        for k in range(HAND_SIZE)
    )
    # You're already expected to have the cards in hand, so just play the lands
    if expected_lands_in_hand >= cmc:
        return round(cmc)
    # otherwise, we're gonna have to draw the rest of the lands
    else:
        for turn_count in range(1, MAX_TURNS):
            chance = sum(
                calculate_draw_chance(
                    k, HAND_SIZE - 1 + turn_count, land_count, library_size
                )
                for k in range(round(cmc), HAND_SIZE + turn_count)
            )
            if chance > 0.50:
                return turn_count
        return MAX_TURNS


def calculate_turns_to_cast_cmc_card_in_library(
    cmc: float, cmc_count: int, land_count: int, library_size: int
) -> int:
    # Note that we assume there are NO cards of that CMC in your hand
    expectation = 0.0
    turns = 0
    for turns in range(1, MAX_TURNS):
        expectation = sum(
            k * calculate_draw_chance(k, turns, cmc_count, library_size - HAND_SIZE)
            for upper_k in range(1, turns + 1)
            for k in range(1, upper_k)
        )
        if expectation > 1.0:
            return turns
    return turns


def cost_to_cmc(cost: str) -> float:
    cmc = 0.0
    unparsed = ""
    return cmc


# def calculate_coverage_cost(qtys: Dict[str, int]) -> List[str]:
#     all_costs = [[CARD_DB[name]["mana_cost"]] * qtys[name] for name in costs.keys()]

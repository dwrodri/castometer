import json
import sys

with open(sys.argv[1]) as fp:
    data = json.load(fp)
    data = {elem["name"]: elem for elem in data}

deck_tuples = []
with open(sys.argv[2]) as fp:
    for line in fp:
        first_space = line.find(" ")
        name = line[first_space + 1 :].strip()
        deck_tuples.append((data[name]["cmc"], data[name]["mana_cost"]))

for i, cost in enumerate(x for x in sorted(deck_tuples, key=lambda n: n[0]) if x[1]):
    print(i+1, cost)

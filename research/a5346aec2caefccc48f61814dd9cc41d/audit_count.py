"""Check the final witness's complete mass-decreasing radius-two search domain."""

import csv
import gzip
import json
import math
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "repo" if (HERE / "repo").is_dir() else HERE.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=Path, default=HERE)
OUT = parser.parse_args().output_dir
model = json.loads((ROOT / "research/readiness-20261021/models/25bar-individual-v2.json").read_text())
candidate = json.loads((OUT / "best-candidate.json").read_text())
summary = json.loads((OUT / "pair-result-continuation.json").read_text())
areas = candidate["areas"]
catalog = [0.0] + model["catalog"]
cost = [math.dist(model["nodes"][a - 1], model["nodes"][b - 1]) * model["density_lbm_in3"]
        for a, b in model["members"]]
base_mass = sum(a * c for a, c in zip(areas, cost))

expected = sum(a < areas[i] for i in range(len(areas)) for a in catalog)
for i in range(len(areas)):
    for j in range(i + 1, len(areas)):
        expected += sum(ai != areas[i] and aj != areas[j] and
                        cost[i] * (ai - areas[i]) + cost[j] * (aj - areas[j]) < -1e-8
                        for ai in catalog for aj in catalog)

seen = set()
with gzip.open(OUT / "pair-attempts-continuation.csv.gz", "rt", newline="") as file:
    for row in csv.DictReader(file):
        assert row["pass"] == "1"
        i, j = int(row["i"]), int(row["j"])
        ai = float(row["area_i"])
        aj = None if j == -1 else float(row["area_j"])
        key = (i, j, ai, aj)
        assert key not in seen
        seen.add(key)
        delta = cost[i] * (ai - areas[i])
        if j == -1:
            assert ai < areas[i]
        else:
            assert 0 <= i < j < len(areas) and ai != areas[i] and aj != areas[j]
            delta += cost[j] * (aj - areas[j])
        assert delta < -1e-8
        assert abs(base_mass + delta - float(row["mass_lbm"])) < 1e-7
        assert row["primary_valid"] == "False" and row["secondary_valid"] == "False"

assert len(seen) == expected == summary["attempts"] == 137848
assert summary["completed_passes"] == 1 and not summary["truncated"]
assert abs(base_mass - summary["best_mass_lbm"]) < 1e-7
print(f"PASS_RADIUS_TWO_AUDIT attempts={expected} primary_feasible=0")

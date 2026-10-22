"""Bounded full-catalogue one- and two-member exchanges on one frozen truss."""

import csv
import gzip
import hashlib
import json
import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "repo" if (HERE / "repo").is_dir() else HERE.parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"),
                str(ROOT / "research/feature-trial/code")]

from prepare_portfolio import model, verify  # noqa: E402
from truss.solver import Solver  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=ROOT / "research/readiness-20261021/25bar-individual-v2-incumbent.json")
    parser.add_argument("--tag", default="")
    parser.add_argument("--max-passes", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    source = args.candidate
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    suffix = "-" + args.tag if args.tag else ""
    initial = json.loads(source.read_text())
    baseline = verify(initial)["primary"]["mass_lbm"]
    b = model(initial["case"])
    solver = Solver(b, initial["profile"])
    catalog = [0.0] + b["catalog"]
    cost = [float(length * b["density_lbm_in3"]) for length in solver.L]
    best = initial
    best_mass = baseline
    start = time.monotonic()
    attempts = valid_primary = valid_both = 0
    trace = []
    completed = 0
    truncated = False
    failures = []

    with gzip.open(out / f"pair-attempts{suffix}.csv.gz", "wt", newline="") as file:
        log = csv.writer(file)
        log.writerow(["pass", "i", "j", "area_i", "area_j", "mass_lbm",
                      "primary_valid", "secondary_valid", "reason"])

        def evaluate(pass_number, anchor, i, ai, j=None, aj=None):
            nonlocal attempts, valid_primary, valid_both, best, best_mass
            x = anchor.copy()
            x[i] = ai
            if j is not None:
                x[j] = aj
            result = solver.evaluate(x)
            attempts += 1
            second = False
            reason = result["reason"]
            if result["valid"]:
                valid_primary += 1
                candidate = dict(initial, areas=x, claimed_mass_lbm=result["mass_lbm"])
                try:
                    verify(candidate)
                    second = True
                    valid_both += 1
                except ValueError as exc:
                    reason = str(exc)
                    failures.append({"pass": pass_number, "i": i, "j": j,
                                     "areas": x, "reason": reason})
                if second and result["mass_lbm"] < best_mass - 1e-8:
                    best, best_mass = candidate, result["mass_lbm"]
                    trace.append({"pass": pass_number, "attempt": attempts,
                                  "i": i, "j": j, "mass_lbm": best_mass,
                                  "areas": x})
            log.writerow([pass_number, i, -1 if j is None else j, ai,
                          "" if aj is None else aj, result["mass_lbm"],
                          result["valid"], second, reason])
            if attempts % 20000 == 0:
                print(f"attempts={attempts} best={best_mass:.9f} elapsed={time.monotonic()-start:.1f}s", flush=True)

        for pass_number in range(1, args.max_passes + 1):
            anchor = list(best["areas"])
            anchor_mass = best_mass
            stop = False
            for i in range(len(anchor)):
                for ai in catalog:
                    if ai >= anchor[i]:
                        continue
                    evaluate(pass_number, anchor, i, ai)
                    if attempts >= 500000 or time.monotonic() - start >= 1200:
                        stop = True
                        break
                if stop:
                    break
            if not stop:
                for i in range(len(anchor)):
                    for j in range(i + 1, len(anchor)):
                        for ai in catalog:
                            if ai == anchor[i]:
                                continue
                            for aj in catalog:
                                if aj == anchor[j] or cost[i] * (ai-anchor[i]) + cost[j] * (aj-anchor[j]) >= -1e-8:
                                    continue
                                evaluate(pass_number, anchor, i, ai, j, aj)
                                if attempts >= 500000 or time.monotonic() - start >= 1200:
                                    stop = True
                                    break
                            if stop:
                                break
                        if stop:
                            break
                    if stop:
                        break
            if stop:
                truncated = True
                break
            completed += 1
            print(f"completed_pass={pass_number} anchor={anchor_mass:.9f} best={best_mass:.9f}", flush=True)
            if best_mass >= anchor_mass - 1e-8:
                break

    final = verify(best)
    summary = {"base_commit": "d3a2a3da00c7cb329474470f9e112f0ac0d32cb1",
               "model_sha256": b["sha256"],
               "input_candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "max_passes": args.max_passes,
               "baseline_mass_lbm": baseline, "best_mass_lbm": best_mass,
               "best_areas": best["areas"], "section_count": final["section_count"],
               "attempts": attempts, "primary_valid": valid_primary,
               "both_valid": valid_both, "completed_passes": completed,
               "truncated": truncated, "elapsed_seconds": time.monotonic()-start,
               "trace": trace, "secondary_failures": failures}
    (out / f"pair-result{suffix}.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / f"best-candidate{suffix}.json").write_text(json.dumps(best, indent=2) + "\n")
    print(f"DONE attempts={attempts} best={best_mass:.9f} completed={completed} truncated={truncated}", flush=True)


if __name__ == "__main__":
    main()

"""
main.py - Top-level orchestrator for the disaster evacuation pipeline.

New run:
    Module 1 -> Module 2 -> Module 3 -> Module 4 -> Module 5 -> Module 6

Existing scenario:
    Module 2 -> Module 3 -> Module 4 -> Module 5 -> Module 6

Module 4 owns its internal radius-expansion logic and re-runs Modules 2/3
when required.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
DATASET_FILE = PROJECT_ROOT / "Dataset1.xlsx"




# ==========================================================
# TEST SCENARIO
# ==========================================================
#
# Change ONLY these values when testing another scenario.
#
# Later, the web application will provide these values
# dynamically instead of keeping them here.
# ==========================================================

DISASTER_TYPE = "Cyclone"

EPICENTER_NAME = "Goregaon"

EPICENTER_LAT = 19.1551480

EPICENTER_LON = 72.8678510

RADIUS_KM = 8.0


MODULE_FILES = {
    1: "1_identify_affected_population.py",
    2: "2_find_candidate_shelters.py",
    3: "3_evaluate_candidate_shelters.py",
    4: "4_select_shelters.py",
    5: "5_rank_shelters.py",
    6: "6_generate_recommendation.py",
}


def print_banner():
    print()
    print("=" * 72)
    print("DISASTER EVACUATION RECOMMENDATION PIPELINE")
    print("=" * 72)
    print()
    print("SCENARIO")
    print("=" * 72)
    print(f"Disaster Type : {DISASTER_TYPE}")
    print(f"Epicenter     : {EPICENTER_NAME}")
    print(f"Latitude      : {EPICENTER_LAT}")
    print(f"Longitude     : {EPICENTER_LON}")
    print(f"Radius        : {RADIUS_KM} km")
    print()

def load_module(number: int):
    """Load a numbered Python file using importlib."""
    filename = MODULE_FILES[number]
    module_path = RUNTIME_DIR / filename

    if not module_path.exists():
        raise FileNotFoundError(
            f"Module {number} not found:\n{module_path}"
        )

    module_name = f"pipeline_module_{number}"

    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load module specification:\n{module_path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "run"):
        raise AttributeError(
            f"Module {number} does not expose run().\n{module_path}"
        )

    return module


def preflight_check(include_module1=True):
    """Check the files required before starting the pipeline."""
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Master dataset not found:\n{DATASET_FILE}"
        )

    if not RUNTIME_DIR.exists():
        raise FileNotFoundError(
            f"Runtime directory not found:\n{RUNTIME_DIR}"
        )

    numbers = range(1, 7) if include_module1 else range(2, 7)

    missing = [
        str(RUNTIME_DIR / MODULE_FILES[n])
        for n in numbers
        if not (RUNTIME_DIR / MODULE_FILES[n]).exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Required module(s) missing:\n" +
            "\n".join(f"  - {item}" for item in missing)
        )

    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


def validate_scenario_file(path):
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Scenario JSON not found:\n{path}"
        )

    if path.suffix.lower() != ".json":
        raise ValueError(
            f"Scenario file must be a .json file:\n{path}"
        )

    return path


def run_module1():
    """
    Current Module 1 interface is run() with no arguments.
    Module 1 creates and returns the scenario JSON path.
    """
    print()
    print("-" * 72)
    print("MAIN | MODULE 1")
    print(f"     {MODULE_FILES[1]}")
    print("-" * 72)

    module = load_module(1)
    scenario_file = module.run(
        DISASTER_TYPE,
        EPICENTER_NAME,
        EPICENTER_LAT,
        EPICENTER_LON,
        RADIUS_KM,
    )

    if not scenario_file:
        raise RuntimeError(
            "Module 1 did not return a scenario file."
        )

    scenario_file = Path(scenario_file)

    if not scenario_file.is_absolute():
        scenario_file = PROJECT_ROOT / scenario_file

    scenario_file = scenario_file.resolve()

    if not scenario_file.exists():
        raise RuntimeError(
            "Module 1 returned a path, but the file does not exist:\n"
            f"{scenario_file}"
        )

    print(f"\n[SUCCESS] Scenario created: {scenario_file}")
    return scenario_file


def run_module(number, scenario_file):
    """Run Modules 2-6 against the same scenario JSON."""
    print()
    print("-" * 72)
    print(f"MAIN | MODULE {number}")
    print(f"     {MODULE_FILES[number]}")
    print("-" * 72)

    module = load_module(number)
    result = module.run(str(scenario_file))

    print(f"\n[SUCCESS] Module {number} completed.")
    return result


def run_pipeline(scenario_file=None, new_scenario=True):
    """
    Execute the complete pipeline.

    New scenario:
        1 -> 2 -> 3 -> 4 -> 5 -> 6

    Existing scenario:
        2 -> 3 -> 4 -> 5 -> 6
    """
    start_time = time.time()

    print_banner()
    preflight_check(include_module1=new_scenario)

    if new_scenario:
        scenario_file = run_module1()
    else:
        if scenario_file is None:
            raise ValueError(
                "An existing scenario JSON is required."
            )

        scenario_file = validate_scenario_file(scenario_file)
        print(f"[INFO] Using existing scenario: {scenario_file}")

    # Module 4 internally handles radius expansion and any required
    # re-execution of Modules 2 and 3.
    for number in range(2, 7):
        run_module(number, scenario_file)

    elapsed = round(time.time() - start_time, 3)

    print()
    print("=" * 72)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 72)
    print(f"Scenario JSON : {scenario_file}")
    print(f"Total Runtime : {elapsed} sec")
    print()


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run the disaster evacuation recommendation pipeline."
    )

    parser.add_argument(
        "--scenario",
        type=Path,
        default=None,
        help=(
            "Use an existing scenario JSON and run Modules 2-6. "
            "If omitted, Module 1 creates a new scenario."
        ),
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.scenario is not None:
            run_pipeline(
                scenario_file=args.scenario,
                new_scenario=False,
            )
        else:
            run_pipeline(new_scenario=True)

    except KeyboardInterrupt:
        print("\n[ERROR] Pipeline interrupted by user.")
        sys.exit(130)

    except Exception as exc:
        print(
            f"\n[ERROR] {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

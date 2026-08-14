import json
import time
from pathlib import Path


# ==========================================================
# CONFIGURATION
# ==========================================================

TOP_RECOMMENDATIONS = 20


# ==========================================================
# LOAD SCENARIO
# ==========================================================

def load_scenario(scenario_file):

    with open(
        scenario_file,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ==========================================================
# SAVE SCENARIO
# ==========================================================

def save_scenario(
    scenario_file,
    scenario_data
):

    with open(
        scenario_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            scenario_data,
            file,
            indent=4
        )


# ==========================================================
# SAFE INTEGER
# ==========================================================

def safe_int(value):

    try:
        return int(value or 0)

    except (
        ValueError,
        TypeError
    ):

        return 0


# ==========================================================
# SAFE FLOAT
# ==========================================================

def safe_float(value):

    try:
        return float(value or 0)

    except (
        ValueError,
        TypeError
    ):

        return 0.0


# ==========================================================
# MEDICAL PRIORITY
# ==========================================================

def medical_priority(
    shelter
):

    value = str(
        shelter.get(
            "MedicalFacility",
            "No"
        )
    ).strip().lower()

    if value == "yes":
        return 1

    return 0


# ==========================================================
# SELECTION TYPE PRIORITY
# ==========================================================

def selection_type_priority(
    shelter
):

    selection_type = str(
        shelter.get(
            "SelectionType",
            ""
        )
    ).strip()

    # GIDS shelters are preferred because
    # they satisfy the independence constraint.

    if selection_type == "GIDS":
        return 2

    if selection_type == "CapacityRecovery":
        return 1

    return 0


# ==========================================================
# BUILD RANKING KEY
# ==========================================================

def build_ranking_key(
    shelter
):

    return (

        # --------------------------------------------------
        # 1. GIDS before CapacityRecovery
        # --------------------------------------------------

        selection_type_priority(
            shelter
        ),

        # --------------------------------------------------
        # 2. Disaster / structural priority
        # --------------------------------------------------

        safe_int(
            shelter.get(
                "PriorityWeight",
                0
            )
        ),

        safe_int(
            shelter.get(
                "StructuralPriority",
                0
            )
        ),

        # --------------------------------------------------
        # 3. Actual population served
        # --------------------------------------------------

        safe_int(
            shelter.get(
                "AssignedPopulation",
                0
            )
        ),

        # --------------------------------------------------
        # 4. Medical capability
        # --------------------------------------------------

        medical_priority(
            shelter
        ),

        # --------------------------------------------------
        # 5. Remaining capacity
        # --------------------------------------------------

        safe_int(
            shelter.get(
                "RemainingCapacity",
                0
            )
        ),

        # --------------------------------------------------
        # 6. Distance
        #
        # Negative because sorting is descending.
        # Smaller distance = better.
        # --------------------------------------------------

        -safe_float(
            shelter.get(
                "Distance(km)",
                999999
            )
        ),

        # --------------------------------------------------
        # 7. Stable final tie-breaker
        # --------------------------------------------------

        str(
            shelter.get(
                "ShelterID",
                ""
            )
        )

    )


# ==========================================================
# ASSIGN RECOMMENDATION TIER
# ==========================================================

def get_recommendation_tier(
    shelter
):

    selection_type = str(
        shelter.get(
            "SelectionType",
            ""
        )
    ).strip()

    assigned_population = safe_int(
        shelter.get(
            "AssignedPopulation",
            0
        )
    )

    if selection_type == "GIDS":

        if assigned_population > 0:
            return "Primary"

        return "Primary - Unutilized"

    if selection_type == "CapacityRecovery":

        if assigned_population > 0:
            return "Supplementary"

        return "Supplementary - Unutilized"

    return "Other"


# ==========================================================
# CREATE RANKED SHELTER OBJECT
# ==========================================================

def create_ranked_shelter(
    shelter,
    rank
):

    ranked = dict(
        shelter
    )

    ranked["RecommendationRank"] = rank

    ranked["RecommendationTier"] = (
        get_recommendation_tier(
            shelter
        )
    )

    return ranked


# ==========================================================
# RANK SHELTERS
# ==========================================================

def rank_shelters(
    selected_shelters
):

    shelters = [
        dict(shelter)
        for shelter in selected_shelters
    ]

    shelters.sort(
        key=build_ranking_key,
        reverse=True
    )

    ranked_shelters = []

    for index, shelter in enumerate(
        shelters,
        start=1
    ):

        ranked_shelters.append(
            create_ranked_shelter(
                shelter,
                index
            )
        )

    return ranked_shelters


# ==========================================================
# CREATE RANKING SUMMARY
# ==========================================================

def create_ranking_summary(
    ranked_shelters,
    module4
):

    total_shelters = len(
        ranked_shelters
    )

    primary_count = sum(
        1
        for shelter in ranked_shelters
        if shelter[
            "RecommendationTier"
        ].startswith("Primary")
    )

    supplementary_count = sum(
        1
        for shelter in ranked_shelters
        if shelter[
            "RecommendationTier"
        ].startswith("Supplementary")
    )

    medical_count = sum(
        1
        for shelter in ranked_shelters
        if str(
            shelter.get(
                "MedicalFacility",
                "No"
            )
        ).lower() == "yes"
    )

    allocated_population = sum(
        safe_int(
            shelter.get(
                "AssignedPopulation",
                0
            )
        )
        for shelter in ranked_shelters
    )

    total_capacity = sum(
        safe_int(
            shelter.get(
                "DefaultCapacity",
                0
            )
        )
        for shelter in ranked_shelters
    )

    return {

        "total_ranked_shelters":
            total_shelters,

        "primary_shelters":
            primary_count,

        "supplementary_shelters":
            supplementary_count,

        "medical_facility_shelters":
            medical_count,

        "total_selected_capacity":
            total_capacity,

        "allocated_population":
            allocated_population,

        "unallocated_population":
            safe_int(
                module4.get(
                    "unallocated_population",
                    0
                )
            ),

        "population_accommodation_percent":
            safe_float(
                module4.get(
                    "population_accommodation_percent",
                    0
                )
            )
    }


# ==========================================================
# MAIN MODULE 5
# ==========================================================

def run(
    scenario_file
):

    start_time = time.time()

    print()
    print("=" * 60)
    print("MODULE 5 - SHELTER RANKING")
    print("=" * 60)
    print()

    # ======================================================
    # LOAD JSON
    # ======================================================

    scenario_data = load_scenario(
        scenario_file
    )

    modules = scenario_data.get(
        "Modules",
        {}
    )

    module4 = modules.get(
        "Module4",
        {}
    )

    # ======================================================
    # VALIDATE MODULE 4
    # ======================================================

    if not module4:

        raise RuntimeError(
            "Module 4 results not found in scenario JSON."
        )

    selected_shelters = module4.get(
        "selected_shelters",
        []
    )

    if not selected_shelters:

        raise RuntimeError(
            "Module 4 contains no selected shelters."
        )

    # ======================================================
    # RANK
    # ======================================================

    ranked_shelters = rank_shelters(
        selected_shelters
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    summary = create_ranking_summary(
        ranked_shelters,
        module4
    )

    execution_time = round(
        time.time() - start_time,
        3
    )

    # ======================================================
    # MODULE 5 RESULT
    # ======================================================

    module5_result = {

        "status":
            "SUCCESS",

        "ranking_method":
            "Deterministic Multi-Criteria Hierarchical Ranking",

        "ranking_criteria": [

            "SelectionType: GIDS before CapacityRecovery",

            "PriorityWeight: descending",

            "StructuralPriority: descending",

            "AssignedPopulation: descending",

            "MedicalFacility: Yes before No",

            "RemainingCapacity: descending",

            "Distance(km): ascending",

            "ShelterID: descending"
        ],

        "source_module":
            "Module4",

        "best_solution_radius_km":
            module4.get(
                "best_solution_radius_km"
            ),

        "population_accommodation_percent":
            module4.get(
                "population_accommodation_percent"
            ),

        "summary":
            summary,

        "ranked_shelters":
            ranked_shelters,

        "top_recommendations":
            ranked_shelters[
                :TOP_RECOMMENDATIONS
            ],

        "execution_time":
            execution_time
    }

    # ======================================================
    # APPEND MODULE 5 TO JSON
    # ======================================================

    scenario_data[
        "Modules"
    ][
        "Module5"
    ] = module5_result

    save_scenario(
        scenario_file,
        scenario_data
    )

    # ======================================================
    # CONSOLE OUTPUT
    # ======================================================

    print(
        f"Source Module 4      : "
        f"{len(selected_shelters):,} shelters"
    )

    print(
        f"Ranked Shelters       : "
        f"{len(ranked_shelters):,}"
    )

    print(
        f"Primary Shelters      : "
        f"{summary['primary_shelters']:,}"
    )

    print(
        f"Supplementary         : "
        f"{summary['supplementary_shelters']:,}"
    )

    print(
        f"Medical Shelters      : "
        f"{summary['medical_facility_shelters']:,}"
    )

    print(
        f"Accommodation         : "
        f"{summary['population_accommodation_percent']:.2f}%"
    )

    print()

    print("-" * 60)
    print("TOP RECOMMENDED SHELTERS")
    print("-" * 60)

    print()

    print(
        f"{'Rank':<6}"
        f"{'ShelterID':<12}"
        f"{'Type':<20}"
        f"{'Assigned':>10}"
        f"{'Priority':>10}"
        f"{'Distance':>10}"
    )

    print("-" * 70)

    for shelter in ranked_shelters[
        :TOP_RECOMMENDATIONS
    ]:

        print(

            f"{shelter.get('RecommendationRank', 0):<6}"

            f"{str(shelter.get('ShelterID', '')):<12}"

            f"{str(shelter.get('BuildingType', ''))[:19]:<20}"

            f"{safe_int(shelter.get('AssignedPopulation', 0)):>10,}"

            f"{safe_int(shelter.get('PriorityWeight', 0)):>10}"

            f"{safe_float(shelter.get('Distance(km)', 0)):>10.2f}"
        )

    print()

    print("=" * 60)
    print("MODULE 5 COMPLETED")
    print("=" * 60)

    return module5_result


# ==========================================================
# STANDALONE EXECUTION
# ==========================================================

if __name__ == "__main__":

    TEST_JSON = (
        "scenarios/"
        "Flood_Dharavi_5km_20260812_174629.json"
    )

    run(
        TEST_JSON
    )
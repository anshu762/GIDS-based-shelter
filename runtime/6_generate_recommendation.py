import json
import time
from pathlib import Path


# ==========================================================
# CONFIGURATION
# ==========================================================

TOP_RECOMMENDATIONS = 20

TOP_PRIMARY_RECOMMENDATIONS = 10

TOP_SUPPLEMENTARY_RECOMMENDATIONS = 10

TOP_MEDICAL_RECOMMENDATIONS = 10


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

        return int(
            value or 0
        )

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

        return float(
            value or 0
        )

    except (
        ValueError,
        TypeError
    ):

        return 0.0


# ==========================================================
# SAFE STRING
# ==========================================================

def safe_string(
    value,
    default=""
):

    if value is None:

        return default

    return str(
        value
    ).strip()


# ==========================================================
# LOAD MODULE 4 + MODULE 5
# ==========================================================

def load_previous_modules(
    scenario_data
):

    modules = scenario_data.get(
        "Modules",
        {}
    )

    module4 = modules.get(
        "Module4",
        {}
    )

    module5 = modules.get(
        "Module5",
        {}
    )

    if not module4:

        raise RuntimeError(
            "Module 4 results not found in scenario JSON."
        )

    if not module5:

        raise RuntimeError(
            "Module 5 results not found in scenario JSON."
        )

    return (
        module4,
        module5
    )


# ==========================================================
# VALIDATE MODULE 4
# ==========================================================

def validate_module4(
    module4
):

    required_fields = [

        "status",

        "best_solution_radius_km",

        "best_solution_accommodation_percent",

        "affected_population",

        "allocated_population",

        "unallocated_population"

    ]

    missing_fields = [

        field

        for field in required_fields

        if field not in module4

    ]

    if missing_fields:

        raise RuntimeError(

            "Module 4 is missing required fields: "

            +

            ", ".join(
                missing_fields
            )

        )


# ==========================================================
# VALIDATE MODULE 5
# ==========================================================

def validate_module5(
    module5
):

    required_fields = [

        "status",

        "ranking_method",

        "ranked_shelters",

        "top_recommendations"

    ]

    missing_fields = [

        field

        for field in required_fields

        if field not in module5

    ]

    if missing_fields:

        raise RuntimeError(

            "Module 5 is missing required fields: "

            +

            ", ".join(
                missing_fields
            )

        )

    if not isinstance(
        module5.get(
            "ranked_shelters"
        ),
        list
    ):

        raise RuntimeError(
            "Module 5 ranked_shelters is not a list."
        )


# ==========================================================
# CREATE BASIC SHELTER RECOMMENDATION
# ==========================================================

def create_shelter_recommendation(
    shelter
):

    return {

        "Rank":
            safe_int(
                shelter.get(
                    "RecommendationRank"
                )
            ),

        "ShelterID":
            safe_string(
                shelter.get(
                    "ShelterID"
                )
            ),

        "ShelterName":
            safe_string(
                shelter.get(
                    "ShelterName"
                )
            ),

        "BuildingType":
            safe_string(
                shelter.get(
                    "BuildingType"
                )
            ),

        "Locality":
            safe_string(
                shelter.get(
                    "Locality"
                )
            ),

        "Latitude":
            safe_float(
                shelter.get(
                    "Latitude"
                )
            ),

        "Longitude":
            safe_float(
                shelter.get(
                    "Longitude"
                )
            ),

        "Distance_km":
            safe_float(
                shelter.get(
                    "Distance(km)"
                )
            ),

        "Capacity":
            safe_int(
                shelter.get(
                    "DefaultCapacity"
                )
            ),

        "AssignedPopulation":
            safe_int(
                shelter.get(
                    "AssignedPopulation"
                )
            ),

        "RemainingCapacity":
            safe_int(
                shelter.get(
                    "RemainingCapacity"
                )
            ),

        "UtilizationPercent":
            safe_float(
                shelter.get(
                    "UtilizationPercent"
                )
            ),

        "PriorityWeight":
            safe_int(
                shelter.get(
                    "PriorityWeight"
                )
            ),

        "StructuralPriority":
            safe_int(
                shelter.get(
                    "StructuralPriority"
                )
            ),

        "MedicalFacility":
            safe_string(
                shelter.get(
                    "MedicalFacility"
                ),
                "No"
            ),

        "IndoorOutdoor":
            safe_string(
                shelter.get(
                    "IndoorOutdoor"
                )
            ),

        "TemporaryShelter":
            safe_string(
                shelter.get(
                    "TemporaryShelter"
                )
            ),

        "SelectionType":
            safe_string(
                shelter.get(
                    "SelectionType"
                )
            ),

        "RecommendationTier":
            safe_string(
                shelter.get(
                    "RecommendationTier"
                )
            ),

        "Remarks":
            safe_string(
                shelter.get(
                    "Remarks"
                )
            )

    }


# ==========================================================
# EXTRACT TOP RECOMMENDATIONS
# ==========================================================

def extract_top_recommendations(
    ranked_shelters
):

    recommendations = []

    for shelter in ranked_shelters[
        :TOP_RECOMMENDATIONS
    ]:

        recommendations.append(

            create_shelter_recommendation(
                shelter
            )

        )

    return recommendations


# ==========================================================
# EXTRACT PRIMARY SHELTERS
# ==========================================================

def extract_primary_shelters(
    ranked_shelters
):

    primary = [

        shelter

        for shelter in ranked_shelters

        if safe_string(
            shelter.get(
                "RecommendationTier"
            )
        ).startswith(
            "Primary"
        )

    ]

    return [

        create_shelter_recommendation(
            shelter
        )

        for shelter in primary[
            :TOP_PRIMARY_RECOMMENDATIONS
        ]

    ]


# ==========================================================
# EXTRACT SUPPLEMENTARY SHELTERS
# ==========================================================

def extract_supplementary_shelters(
    ranked_shelters
):

    supplementary = [

        shelter

        for shelter in ranked_shelters

        if safe_string(
            shelter.get(
                "RecommendationTier"
            )
        ).startswith(
            "Supplementary"
        )

    ]

    return [

        create_shelter_recommendation(
            shelter
        )

        for shelter in supplementary[
            :TOP_SUPPLEMENTARY_RECOMMENDATIONS
        ]

    ]


# ==========================================================
# EXTRACT MEDICAL SHELTERS
# ==========================================================

def extract_medical_shelters(
    ranked_shelters
):

    medical = [

        shelter

        for shelter in ranked_shelters

        if safe_string(
            shelter.get(
                "MedicalFacility",
                "No"
            )
        ).lower() == "yes"

    ]

    return [

        create_shelter_recommendation(
            shelter
        )

        for shelter in medical[
            :TOP_MEDICAL_RECOMMENDATIONS
        ]

    ]
# ==========================================================
# CREATE FINAL SCENARIO SUMMARY
# ==========================================================

def create_scenario_summary(
    scenario_data,
    module4,
    module5
):

    scenario = scenario_data.get(
        "Scenario",
        {}
    )

    ranking_summary = module5.get(
        "summary",
        {}
    )

    affected_population = safe_int(
        module4.get(
            "affected_population",
            0
        )
    )

    allocated_population = safe_int(
        module4.get(
            "allocated_population",
            0
        )
    )

    unallocated_population = safe_int(
        module4.get(
            "unallocated_population",
            0
        )
    )

    accommodation_percent = safe_float(
        module4.get(
            "best_solution_accommodation_percent",
            module4.get(
                "population_accommodation_percent",
                0
            )
        )
    )

    return {

        # --------------------------------------------------
        # SCENARIO
        # --------------------------------------------------

        "ScenarioID":
            safe_string(
                scenario.get(
                    "ScenarioID"
                )
            ),

        "DisasterType":
            safe_string(
                scenario.get(
                    "DisasterType"
                )
            ),

        "Epicenter":
            safe_string(
                scenario.get(
                    "Epicenter"
                )
            ),

        "DisasterRadius_km":
            safe_float(
                scenario.get(
                    "DisasterRadius_km"
                )
            ),

        # --------------------------------------------------
        # FINAL SOLUTION
        # --------------------------------------------------

        "BestSolutionRadius_km":
            safe_float(
                module4.get(
                    "best_solution_radius_km"
                )
            ),

        "AffectedPopulation":
            affected_population,

        "AllocatedPopulation":
            allocated_population,

        "UnallocatedPopulation":
            unallocated_population,

        "PopulationAccommodationPercent":
            accommodation_percent,

        # --------------------------------------------------
        # SHELTER SUMMARY
        # --------------------------------------------------

        "SelectedShelters":
            safe_int(
                module5.get(
                    "summary",
                    {}
                ).get(
                    "total_ranked_shelters",
                    0
                )
            ),

        "PrimaryShelters":
            safe_int(
                ranking_summary.get(
                    "primary_shelters",
                    0
                )
            ),

        "SupplementaryShelters":
            safe_int(
                ranking_summary.get(
                    "supplementary_shelters",
                    0
                )
            ),

        "MedicalFacilityShelters":
            safe_int(
                ranking_summary.get(
                    "medical_facility_shelters",
                    0
                )
            ),

        "TotalSelectedCapacity":
            safe_int(
                ranking_summary.get(
                    "total_selected_capacity",
                    0
                )
            ),

        # --------------------------------------------------
        # MODULE STATUS
        # --------------------------------------------------

        "Module4Status":
            safe_string(
                module4.get(
                    "status"
                )
            ),

        "Module5Status":
            safe_string(
                module5.get(
                    "status"
                )
            )

    }


# ==========================================================
# CREATE HUMAN-READABLE RECOMMENDATION
# ==========================================================

def create_recommendation_message(
    summary
):

    disaster_type = summary.get(
        "DisasterType",
        "disaster"
    )

    epicenter = summary.get(
        "Epicenter",
        ""
    )

    radius = summary.get(
        "BestSolutionRadius_km",
        0
    )

    affected = summary.get(
        "AffectedPopulation",
        0
    )

    allocated = summary.get(
        "AllocatedPopulation",
        0
    )

    unallocated = summary.get(
        "UnallocatedPopulation",
        0
    )

    accommodation = summary.get(
        "PopulationAccommodationPercent",
        0
    )

    return {

        "Headline":
            (
                f"{disaster_type} evacuation "
                f"recommendations generated"
            ),

        "Scenario":
            (
                f"{disaster_type} scenario centered "
                f"at {epicenter}"
            ),

        "AffectedPopulation":
            (
                f"{affected:,} people identified "
                f"within the affected area."
            ),

        "ShelterSolution":
            (
                f"The best shelter solution was found "
                f"at a {radius:.2f} km search radius."
            ),

        "PopulationAccommodation":
            (
                f"{allocated:,} people can be accommodated "
                f"({accommodation:.2f}%)."
            ),

        "UnallocatedPopulation":
            (
                f"{unallocated:,} people remain unallocated."
            )

    }


# ==========================================================
# BUILD FINAL RECOMMENDATION OBJECT
# ==========================================================

def build_final_recommendation(
    scenario_data,
    module4,
    module5
):

    ranked_shelters = module5.get(
        "ranked_shelters",
        []
    )

    summary = create_scenario_summary(
        scenario_data,
        module4,
        module5
    )

    recommendation_message = (
        create_recommendation_message(
            summary
        )
    )

    return {

        "scenario_summary":
            summary,

        "recommendation_message":
            recommendation_message,

        "top_recommendations":
            extract_top_recommendations(
                ranked_shelters
            ),

        "primary_recommendations":
            extract_primary_shelters(
                ranked_shelters
            ),

        "supplementary_recommendations":
            extract_supplementary_shelters(
                ranked_shelters
            ),

        "medical_recommendations":
            extract_medical_shelters(
                ranked_shelters
            )

    }


# ==========================================================
# CREATE MODULE 6 RESULT
# ==========================================================

def create_module6_result(
    scenario_data,
    module4,
    module5
):

    final_recommendation = (
        build_final_recommendation(
            scenario_data,
            module4,
            module5
        )
    )

    return {

        "status":
            "SUCCESS",

        "module":
            "Module6",

        "purpose":
            (
                "Generate final "
                "application-readable "
                "shelter recommendations"
            ),

        "source_modules": [

            "Module4",

            "Module5"

        ],

        "best_solution_radius_km":
            module4.get(
                "best_solution_radius_km"
            ),

        "population_accommodation_percent":
            module4.get(
                "best_solution_accommodation_percent",
                module4.get(
                    "population_accommodation_percent"
                )
            ),

        "final_recommendation":
            final_recommendation

    }


# ==========================================================
# CONSOLE REPORT
# ==========================================================

def print_final_report(
    module6_result
):

    recommendation = module6_result[
        "final_recommendation"
    ]

    summary = recommendation[
        "scenario_summary"
    ]

    messages = recommendation[
        "recommendation_message"
    ]

    print()

    print("=" * 70)

    print(
        "MODULE 6 - FINAL SHELTER RECOMMENDATION"
    )

    print("=" * 70)

    print()

    print(
        f"Scenario               : "
        f"{summary['ScenarioID']}"
    )

    print(
        f"Disaster               : "
        f"{summary['DisasterType']}"
    )

    print(
        f"Epicenter              : "
        f"{summary['Epicenter']}"
    )

    print(
        f"Affected Population    : "
        f"{summary['AffectedPopulation']:,}"
    )

    print(
        f"Best Search Radius     : "
        f"{summary['BestSolutionRadius_km']:.2f} km"
    )

    print(
        f"Selected Shelters      : "
        f"{summary['SelectedShelters']:,}"
    )

    print(
        f"Primary Shelters       : "
        f"{summary['PrimaryShelters']:,}"
    )

    print(
        f"Supplementary Shelters : "
        f"{summary['SupplementaryShelters']:,}"
    )

    print(
        f"Medical Shelters       : "
        f"{summary['MedicalFacilityShelters']:,}"
    )

    print(
        f"Total Capacity         : "
        f"{summary['TotalSelectedCapacity']:,}"
    )

    print(
        f"Allocated Population   : "
        f"{summary['AllocatedPopulation']:,}"
    )

    print(
        f"Unallocated Population : "
        f"{summary['UnallocatedPopulation']:,}"
    )

    print(
        f"Accommodation          : "
        f"{summary['PopulationAccommodationPercent']:.2f}%"
    )

    print()

    print("-" * 70)

    print(
        messages["Headline"]
    )

    print(
        messages["ShelterSolution"]
    )

    print(
        messages["PopulationAccommodation"]
    )

    print(
        messages["UnallocatedPopulation"]
    )

    print()

    # ======================================================
    # TOP RECOMMENDATIONS
    # ======================================================

    print("-" * 70)

    print("TOP SHELTER RECOMMENDATIONS")

    print("-" * 70)

    print()

    print(
        f"{'Rank':<6}"
        f"{'ShelterID':<12}"
        f"{'Type':<20}"
        f"{'Capacity':>12}"
        f"{'Assigned':>12}"
        f"{'Distance':>12}"
    )

    print("-" * 75)

    for shelter in recommendation[
        "top_recommendations"
    ]:

        print(

            f"{shelter['Rank']:<6}"

            f"{shelter['ShelterID']:<12}"

            f"{shelter['BuildingType'][:19]:<20}"

            f"{shelter['Capacity']:>12,}"

            f"{shelter['AssignedPopulation']:>12,}"

            f"{shelter['Distance_km']:>12.2f}"

        )

    print()

    print("=" * 70)

    print(
        "MODULE 6 COMPLETED"
    )

    print("=" * 70)

    # ==========================================================
# MAIN MODULE 6
# ==========================================================

def run(
    scenario_file
):

    start_time = time.time()

    print()

    print("=" * 70)

    print(
        "MODULE 6 - FINAL RECOMMENDATION GENERATION"
    )

    print("=" * 70)

    print()

    # ======================================================
    # LOAD SCENARIO
    # ======================================================

    scenario_data = load_scenario(
        scenario_file
    )

    # ======================================================
    # LOAD MODULE 4 + MODULE 5
    # ======================================================

    module4, module5 = (
        load_previous_modules(
            scenario_data
        )
    )

    # ======================================================
    # VALIDATE
    # ======================================================

    validate_module4(
        module4
    )

    validate_module5(
        module5
    )

    # ======================================================
    # BUILD FINAL RESULT
    # ======================================================

    module6_result = create_module6_result(
        scenario_data,
        module4,
        module5
    )

    # ======================================================
    # EXECUTION TIME
    # ======================================================

    execution_time = round(
        time.time() - start_time,
        3
    )

    module6_result[
        "execution_time"
    ] = execution_time

    # ======================================================
    # APPEND MODULE 6 TO JSON
    # ======================================================

    if "Modules" not in scenario_data:

        scenario_data[
            "Modules"
        ] = {}

    scenario_data[
        "Modules"
    ][
        "Module6"
    ] = module6_result

    save_scenario(
        scenario_file,
        scenario_data
    )

    # ======================================================
    # PRINT REPORT
    # ======================================================

    print_final_report(
        module6_result
    )

    print()

    print(
        f"Execution Time        : "
        f"{execution_time} sec"
    )

    print()

    return module6_result


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
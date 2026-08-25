import math
import time
import json
import copy
import importlib.util
from pathlib import Path


# ==========================================================
# CONFIGURATION
# ==========================================================

# Population nodes within this distance of a shelter
# are considered geographically serviceable by that shelter.
# Coverage radius is dynamic: search radius - disaster radius.
# It is passed into GIDS, allocation, and coverage calculations.

# Preferred minimum distance between selected shelters.
INDEPENDENCE_RADIUS_KM = 1.2

# Comfortable walking-speed assumption for the POC.
WALKING_SPEED_KMPH = 3.0

# Radius expansion scenarios.
#
# Disaster radius = 5 km
#
# 1 hr  -> 8.0 km
# 1.5 hr -> 9.5 km
# 2 hr  -> 11.0 km
# 2.5 hr -> 12.5 km
# 3 hr -> 14.0 km
#
EVACUATION_TIME_STEPS_HOURS = [
    1.0,
    1.5,
    2.0,
    2.5,
    3.0
]

MAX_SEARCH_RADIUS_KM = 14.0

# Baseline POC search radius: 1.4 x disaster radius.
INITIAL_SEARCH_RADIUS_MULTIPLIER = 1.4


# ==========================================================
# LOAD PYTHON MODULE
# ==========================================================

def load_module(module_name, file_name):

    runtime_folder = Path(__file__).resolve().parent

    module_path = runtime_folder / file_name

    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path
    )

    if spec is None or spec.loader is None:

        raise ImportError(
            f"Unable to load module: {file_name}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


# ==========================================================
# HAVERSINE DISTANCE
# ==========================================================

def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))

    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (

        math.sin(dlat / 2) ** 2

        +

        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2

    )

    c = 2 * math.atan2(

        math.sqrt(a),

        math.sqrt(1 - a)

    )

    return R * c


# ==========================================================
# CALCULATE SEARCH RADIUS
# ==========================================================

def calculate_search_radius(
    disaster_radius,
    evacuation_time_hours
):

    walking_reach = (

        WALKING_SPEED_KMPH
        *
        evacuation_time_hours

    )

    return round(

        disaster_radius
        +
        walking_reach,

        2

    )


# ==========================================================
# LOAD SCENARIO
# ==========================================================

def load_scenario(
    scenario_file
):

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
# MODULE 1 DATA
# ==========================================================

def get_population_data(
    scenario_data
):

    module1 = (

        scenario_data
        .get("Modules", {})
        .get("Module1", {})

    )

    affected_population = int(

        module1.get(
            "affected_population",
            0
        )
        or 0

    )

    population_nodes = module1.get(

        "affected_nodes",

        []

    )

    return (

        affected_population,
        population_nodes

    )


# ==========================================================
# MODULE 3 DATA
# ==========================================================

def get_module3_shelters(
    scenario_data
):

    module3 = (

        scenario_data
        .get("Modules", {})
        .get("Module3", {})

    )

    return module3.get(

        "suitable_shelters",

        []

    )


# ==========================================================
# CHECK SHELTER INDEPENDENCE
# ==========================================================

def is_independent(
    shelter,
    selected_shelters
):

    for selected in selected_shelters:

        distance = haversine(

            shelter["Latitude"],
            shelter["Longitude"],

            selected["Latitude"],
            selected["Longitude"]

        )

        if distance < INDEPENDENCE_RADIUS_KM:

            return False

    return True


# ==========================================================
# FIND POPULATION COVERED BY SHELTER
# ==========================================================

def calculate_shelter_coverage(
    shelter,
    population_nodes,
    coverage_radius_km
):

    covered_nodes = []

    covered_population = 0

    for node in population_nodes:

        distance = haversine(

            shelter["Latitude"],
            shelter["Longitude"],

            node["Latitude"],
            node["Longitude"]

        )

        if distance <= coverage_radius_km:

            covered_nodes.append(

                node["PopulationNodeID"]

            )

            covered_population += int(

                node.get(
                    "Population",
                    0
                )
                or 0

            )

    return (

        covered_nodes,
        covered_population

    )


# ==========================================================
# PREPARE SHELTERS
# ==========================================================

def prepare_shelters(
    suitable_shelters,
    population_nodes,
    coverage_radius_km
):

    prepared = []

    for original_shelter in suitable_shelters:

        shelter = dict(
            original_shelter
        )

        capacity = int(

            shelter.get(
                "DefaultCapacity",
                0
            )
            or 0

        )

        shelter["DefaultCapacity"] = capacity

        # --------------------------------------------------
        # Geographic service area
        # --------------------------------------------------

        covered_nodes, local_population = (

            calculate_shelter_coverage(

                shelter,
                population_nodes,
                coverage_radius_km

            )

        )

        shelter["CoveredPopulationNodes"] = (
            covered_nodes
        )

        shelter["LocalPopulation"] = (
            local_population
        )

        # --------------------------------------------------
        # A shelter with zero local population cannot
        # actually serve the affected population.
        # --------------------------------------------------

        shelter["Serviceable"] = (

            local_population > 0
            and
            capacity > 0

        )

        priority = int(

            shelter.get(
                "PriorityWeight",
                0
            )
            or 0

        )

        # --------------------------------------------------
        # Selection score
        #
        # Population coverage is most important.
        # Capacity and priority help break ties.
        # --------------------------------------------------

        shelter["SelectionScore"] = (

            local_population

            +

            capacity

            +

            (
                priority
                *
                1000
            )

        )

        prepared.append(
            shelter
        )

    return prepared


# ==========================================================
# CALCULATE SERVICEABLE CAPACITY
# ==========================================================

def calculate_serviceable_capacity(
    prepared_shelters
):

    serviceable_shelters = [

        shelter

        for shelter in prepared_shelters

        if shelter.get(
            "Serviceable",
            False
        )

    ]

    total_capacity = sum(

        shelter["DefaultCapacity"]

        for shelter in serviceable_shelters

    )

    return (

        serviceable_shelters,
        total_capacity

    )


# ==========================================================
# CREATE SELECTED SHELTER OBJECT
# ==========================================================

def create_selected_shelter(
    shelter,
    selection_type
):

    selected = dict(
        shelter
    )

    selected["SelectionType"] = (
        selection_type
    )

    selected["Selected"] = True

    selected["AssignedPopulation"] = 0

    selected["RemainingCapacity"] = (

        selected["DefaultCapacity"]

    )

    selected["AssignedPopulationNodes"] = []

    selected["UtilizationPercent"] = 0.0

    return selected


# ==========================================================
# GIDS + CAPACITY RECOVERY
# ==========================================================

def run_gids(
    suitable_shelters,
    population_nodes,
    affected_population,
    coverage_radius_km
):

    prepared = prepare_shelters(

        suitable_shelters,

        population_nodes,

        coverage_radius_km

    )

    # ------------------------------------------------------
    # Only shelters capable of serving at least one affected
    # population node participate in selection.
    # ------------------------------------------------------

    serviceable_shelters, serviceable_capacity = (

        calculate_serviceable_capacity(

            prepared

        )

    )

    # ------------------------------------------------------
    # Sort strongest shelters first.
    # ------------------------------------------------------

    serviceable_shelters.sort(

        key=lambda shelter: (

            shelter["SelectionScore"],

            shelter["DefaultCapacity"],

            shelter.get(
                "PriorityWeight",
                0
            )
            or 0

        ),

        reverse=True

    )

    selected_shelters = []

    selected_ids = set()

    total_selected_capacity = 0

    covered_population_nodes = set()

    # ======================================================
    # PHASE 1
    #
    # GEOGRAPHIC GIDS
    #
    # Prefer spatially independent shelters.
    # ======================================================

    for shelter in serviceable_shelters:

        if not is_independent(

            shelter,

            selected_shelters

        ):

            continue

        selected = create_selected_shelter(

            shelter,

            "GIDS"

        )

        selected_shelters.append(
            selected
        )

        selected_ids.add(

            shelter["ShelterID"]

        )

        total_selected_capacity += (

            shelter["DefaultCapacity"]

        )

        covered_population_nodes.update(

            shelter[
                "CoveredPopulationNodes"
            ]

        )

    # ======================================================
    # PHASE 2
    #
    # CAPACITY RECOVERY
    #
    # If independent selection doesn't provide enough
    # capacity, allow overlapping shelters.
    #
    # This is the important correction.
    # ======================================================

    if total_selected_capacity < affected_population:

        for shelter in serviceable_shelters:

            shelter_id = shelter[
                "ShelterID"
            ]

            if shelter_id in selected_ids:

                continue

            # ------------------------------------------------
            # Only add shelters that can serve population
            # not already adequately represented.
            #
            # For now we rank by uncovered population.
            # ------------------------------------------------

            uncovered_nodes = (

                set(
                    shelter[
                        "CoveredPopulationNodes"
                    ]
                )
                -
                covered_population_nodes

            )

            uncovered_population = 0

            if uncovered_nodes:

                for node in population_nodes:

                    if (

                        node[
                            "PopulationNodeID"
                        ]
                        in
                        uncovered_nodes

                    ):

                        uncovered_population += int(

                            node.get(
                                "Population",
                                0
                            )
                            or 0

                        )

            # ------------------------------------------------
            # Even if all its nodes are already geographically
            # covered, its capacity may still be required.
            # Therefore capacity remains part of the score.
            # ------------------------------------------------

            recovery_score = (

                uncovered_population
                +
                shelter["DefaultCapacity"]

                +

                (
                    int(
                        shelter.get(
                            "PriorityWeight",
                            0
                        )
                        or 0
                    )
                    *
                    1000
                )

            )

            shelter["_RecoveryScore"] = (
                recovery_score
            )

        recovery_candidates = [

            shelter

            for shelter in serviceable_shelters

            if shelter[
                "ShelterID"
            ]
            not in
            selected_ids

        ]

        recovery_candidates.sort(

            key=lambda shelter: (

                shelter.get(
                    "_RecoveryScore",
                    0
                ),

                shelter["DefaultCapacity"]

            ),

            reverse=True

        )

        # --------------------------------------------------
        # Add overlapping shelters until:
        #
        # 1. Theoretical selected capacity is sufficient
        # OR
        # 2. All serviceable shelters have been considered.
        # --------------------------------------------------

        for shelter in recovery_candidates:

            selected = create_selected_shelter(

                shelter,

                "CapacityRecovery"

            )

            selected_shelters.append(
                selected
            )

            selected_ids.add(

                shelter["ShelterID"]

            )

            total_selected_capacity += (

                shelter["DefaultCapacity"]

            )

            covered_population_nodes.update(

                shelter[
                    "CoveredPopulationNodes"
                ]

            )

            if (

                total_selected_capacity
                >=
                affected_population

            ):

                break

    # ======================================================
    # FINAL CAPACITY STATE
    # ======================================================

    capacity_shortfall = max(

        affected_population
        -
        total_selected_capacity,

        0

    )

    return {

        "selected_shelters":
            selected_shelters,

        "prepared_shelters":
            prepared,

        "serviceable_shelters":
            serviceable_shelters,

        "serviceable_capacity":
            serviceable_capacity,

        "selected_capacity":
            total_selected_capacity,

        "capacity_shortfall":
            capacity_shortfall,

        "covered_population_nodes":
            covered_population_nodes

    }
# ==========================================================
# POPULATION ALLOCATION
# ==========================================================

def allocate_population(
    selected_shelters,
    population_nodes,
    coverage_radius_km
):

    assignments = []

    # ------------------------------------------------------
    # RESET ALLOCATION DATA
    # ------------------------------------------------------

    for shelter in selected_shelters:

        shelter["AssignedPopulation"] = 0

        shelter["RemainingCapacity"] = (

            shelter.get(
                "DefaultCapacity",
                0
            )
            or 0

        )

        shelter["AssignedPopulationNodes"] = []

        shelter["UtilizationPercent"] = 0.0

    # ======================================================
    # PROCESS EACH POPULATION NODE
    # ======================================================

    for node in population_nodes:

        population_remaining = int(

            node.get(
                "Population",
                0
            )
            or 0

        )

        if population_remaining <= 0:

            continue

        possible_shelters = []

        # --------------------------------------------------
        # Find shelters capable of serving this node
        # --------------------------------------------------

        for shelter in selected_shelters:

            distance = haversine(

                node["Latitude"],
                node["Longitude"],

                shelter["Latitude"],
                shelter["Longitude"]

            )

            if distance <= coverage_radius_km:

                possible_shelters.append(

                    (
                        distance,
                        shelter
                    )

                )

        # --------------------------------------------------
        # Nearest shelter first
        # --------------------------------------------------

        possible_shelters.sort(

            key=lambda item: item[0]

        )

        # --------------------------------------------------
        # Allocate population
        # --------------------------------------------------

        for distance, shelter in possible_shelters:

            if population_remaining <= 0:

                break

            available_capacity = int(

                shelter.get(
                    "RemainingCapacity",
                    0
                )
                or 0

            )

            if available_capacity <= 0:

                continue

            allocated = min(

                population_remaining,

                available_capacity

            )

            shelter["AssignedPopulation"] += (

                allocated

            )

            shelter["RemainingCapacity"] -= (

                allocated

            )

            shelter[
                "AssignedPopulationNodes"
            ].append(

                node[
                    "PopulationNodeID"
                ]

            )

            population_remaining -= allocated

            assignments.append({

                "PopulationNodeID":
                    node[
                        "PopulationNodeID"
                    ],

                "Locality":
                    node.get(
                        "Locality"
                    ),

                "AssignedShelterID":
                    shelter[
                        "ShelterID"
                    ],

                "AssignedShelterName":
                    shelter[
                        "ShelterName"
                    ],

                "PopulationAssigned":
                    allocated,

                "Distance(km)":
                    round(
                        distance,
                        3
                    )

            })

    # ======================================================
    # CALCULATE SHELTER UTILIZATION
    # ======================================================

    for shelter in selected_shelters:

        capacity = int(

            shelter.get(
                "DefaultCapacity",
                0
            )
            or 0

        )

        assigned = int(

            shelter.get(
                "AssignedPopulation",
                0
            )
            or 0

        )

        if capacity > 0:

            shelter["UtilizationPercent"] = round(

                (
                    assigned
                    /
                    capacity
                )
                *
                100,

                2

            )

        else:

            shelter["UtilizationPercent"] = 0.0

    return assignments


# ==========================================================
# CALCULATE ALLOCATION SUMMARY
# ==========================================================

def calculate_allocation_summary(
    selected_shelters,
    population_nodes,
    assignments,
    affected_population,
    coverage_radius_km
):

    # ------------------------------------------------------
    # TOTAL SELECTED CAPACITY
    # ------------------------------------------------------

    total_selected_capacity = sum(

        int(

            shelter.get(
                "DefaultCapacity",
                0
            )
            or 0

        )

        for shelter in selected_shelters

    )

    # ------------------------------------------------------
    # ACTUALLY ALLOCATED POPULATION
    # ------------------------------------------------------

    allocated_population = sum(

        int(

            assignment.get(
                "PopulationAssigned",
                0
            )
            or 0

        )

        for assignment in assignments

    )

    # ------------------------------------------------------
    # GEOGRAPHICALLY COVERED POPULATION
    #
    # This ignores shelter capacity.
    #
    # It simply asks:
    #
    # "Does at least one selected shelter exist within
    #  COVERAGE_RADIUS_KM of this population node?"
    # ------------------------------------------------------

    geographically_covered_nodes = set()

    geographically_covered_population = 0

    for node in population_nodes:

        node_population = int(

            node.get(
                "Population",
                0
            )
            or 0

        )

        covered = False

        for shelter in selected_shelters:

            distance = haversine(

                node["Latitude"],
                node["Longitude"],

                shelter["Latitude"],
                shelter["Longitude"]

            )

            if distance <= coverage_radius_km:

                covered = True

                break

        if covered:

            geographically_covered_nodes.add(

                node[
                    "PopulationNodeID"
                ]

            )

            geographically_covered_population += (

                node_population

            )

    # ------------------------------------------------------
    # UNALLOCATED POPULATION
    # ------------------------------------------------------

    unallocated_population = max(

        affected_population
        -
        allocated_population,

        0

    )

    # ------------------------------------------------------
    # CAPACITY SHORTFALL
    # ------------------------------------------------------

    capacity_shortfall = max(

        affected_population
        -
        total_selected_capacity,

        0

    )

    # ------------------------------------------------------
    # PERCENTAGES
    # ------------------------------------------------------

    if affected_population > 0:

        geographic_coverage_percent = round(

            (
                geographically_covered_population
                /
                affected_population
            )
            *
            100,

            2

        )

        population_accommodation_percent = round(

            (
                allocated_population
                /
                affected_population
            )
            *
            100,

            2

        )

    else:

        geographic_coverage_percent = 0.0

        population_accommodation_percent = 0.0

    # ------------------------------------------------------
    # SERVICEABILITY
    # ------------------------------------------------------

    if total_selected_capacity > 0:

        selected_capacity_utilization_percent = round(

            (
                allocated_population
                /
                total_selected_capacity
            )
            *
            100,

            2

        )

    else:

        selected_capacity_utilization_percent = 0.0

    return {

        "total_selected_capacity":
            total_selected_capacity,

        "affected_population":
            affected_population,

        "geographically_covered_population":
            geographically_covered_population,

        "geographically_covered_nodes":
            len(
                geographically_covered_nodes
            ),

        "allocated_population":
            allocated_population,

        "unallocated_population":
            unallocated_population,

        "capacity_shortfall":
            capacity_shortfall,

        "geographic_coverage_percent":
            geographic_coverage_percent,

        "population_accommodation_percent":
            population_accommodation_percent,

        "selected_capacity_utilization_percent":
            selected_capacity_utilization_percent

    }


# ==========================================================
# SOLVE CURRENT RADIUS
# ==========================================================

def solve_current_radius(
    scenario_file,
    scenario_data,
    coverage_radius_km
):

    affected_population, population_nodes = (

        get_population_data(

            scenario_data

        )

    )

    suitable_shelters = get_module3_shelters(

        scenario_data

    )

    # ======================================================
    # NO SUITABLE SHELTERS
    # ======================================================

    if not suitable_shelters:

        return {

            "selected_shelters": [],

            "assignments": [],

            "prepared_shelters": [],

            "serviceable_shelters": [],

            "serviceable_capacity": 0,

            "summary": {

                "total_selected_capacity": 0,

                "affected_population":
                    affected_population,

                "geographically_covered_population":
                    0,

                "geographically_covered_nodes":
                    0,

                "allocated_population":
                    0,

                "unallocated_population":
                    affected_population,

                "capacity_shortfall":
                    affected_population,

                "geographic_coverage_percent":
                    0.0,

                "population_accommodation_percent":
                    0.0,

                "selected_capacity_utilization_percent":
                    0.0

            }

        }

    # ======================================================
    # RUN GIDS + CAPACITY RECOVERY
    # ======================================================

    gids_result = run_gids(

        suitable_shelters,

        population_nodes,

        affected_population,

        coverage_radius_km

    )

    selected_shelters = gids_result[
        "selected_shelters"
    ]

    # ======================================================
    # POPULATION ALLOCATION
    # ======================================================

    assignments = allocate_population(

        selected_shelters,

        population_nodes,

        coverage_radius_km

    )

    # ======================================================
    # ALLOCATION SUMMARY
    # ======================================================

    summary = calculate_allocation_summary(

        selected_shelters,

        population_nodes,

        assignments,

        affected_population,

        coverage_radius_km

    )

    return {

        "selected_shelters":
            selected_shelters,

        "assignments":
            assignments,

        "prepared_shelters":
            gids_result[
                "prepared_shelters"
            ],

        "serviceable_shelters":
            gids_result[
                "serviceable_shelters"
            ],

        "serviceable_capacity":
            gids_result[
                "serviceable_capacity"
            ],

        "summary":
            summary

    }


# ==========================================================
# RUN MODULE 2
# ==========================================================

def rerun_module2(
    scenario_file
):

    print()
    print("-" * 60)
    print("EXPANSION: RUNNING MODULE 2")
    print("-" * 60)

    module2 = load_module(

        "module2",

        "2_find_candidate_shelters.py"

    )

    module2.run(

        scenario_file

    )


# ==========================================================
# RUN MODULE 3
# ==========================================================

def rerun_module3(
    scenario_file
):

    print()
    print("-" * 60)
    print("EXPANSION: RUNNING MODULE 3")
    print("-" * 60)

    module3 = load_module(

        "module3",

        "3_evaluate_candidate_shelters.py"

    )

    module3.run(

        scenario_file

    )


# ==========================================================
# BUILD RADIUS EXPANSION STEPS
# ==========================================================

def build_expansion_steps(
    disaster_radius,
    current_search_radius
):

    steps = []

    for evacuation_time in (

        EVACUATION_TIME_STEPS_HOURS

    ):

        search_radius = calculate_search_radius(

            disaster_radius,

            evacuation_time

        )

        # --------------------------------------------------
        # Respect maximum operational radius.
        # --------------------------------------------------

        search_radius = min(

            search_radius,

            MAX_SEARCH_RADIUS_KM

        )

        # --------------------------------------------------
        # Only generate a step if it is actually larger
        # than the current radius.
        # --------------------------------------------------

        if search_radius <= current_search_radius:

            continue

        steps.append({

            "EvacuationTimeHours":
                evacuation_time,

            "WalkingReach_km":
                round(

                    WALKING_SPEED_KMPH
                    *
                    evacuation_time,

                    2

                ),

            "SearchRadius_km":
                search_radius

        })

    # ------------------------------------------------------
    # Remove duplicate radii.
    # ------------------------------------------------------

    unique_steps = []

    seen_radii = set()

    for step in steps:

        radius = step[
            "SearchRadius_km"
        ]

        if radius in seen_radii:

            continue

        seen_radii.add(
            radius
        )

        unique_steps.append(
            step
        )

    return unique_steps


# ==========================================================
# CHECK WHETHER CURRENT SOLUTION IS SUCCESSFUL
# ==========================================================

def solution_is_complete(
    summary,
    affected_population
):

    return (

        summary[
            "allocated_population"
        ]

        >=

        affected_population

    )


# ==========================================================
# MAIN MODULE 4
# ==========================================================

def run(
    scenario_file
):

    start_time = time.time()

    print()
    print("=" * 60)
    print("MODULE 4 - SHELTER SELECTION & ALLOCATION")
    print("=" * 60)
    print()

    # ======================================================
    # LOAD SCENARIO
    # ======================================================

    scenario_data = load_scenario(

        scenario_file

    )

    scenario = scenario_data[
        "Scenario"
    ]

    disaster_type = scenario.get(

        "DisasterType",

        "Unknown"

    )

    disaster_radius = float(

        scenario.get(
            "DisasterRadius_km",
            0
        )
        or 0

    )

    # ------------------------------------------------------
    # ALWAYS start Module 4 from the POC baseline radius.
    # This prevents a previous run that ended at 14 km from
    # becoming the starting radius of the next run.
    # ------------------------------------------------------
    current_search_radius = round(
        disaster_radius * INITIAL_SEARCH_RADIUS_MULTIPLIER,
        2
    )

    current_search_radius = min(
        current_search_radius,
        MAX_SEARCH_RADIUS_KM
    )

    scenario_data["Scenario"]["ShelterSearchRadius_km"] = current_search_radius
    save_scenario(
        scenario_file,
        scenario_data
    )

    # Refresh Module 2 and Module 3 for the baseline radius.
    rerun_module2(scenario_file)
    rerun_module3(scenario_file)

    # Reload the scenario after Module 2/3 have updated it.
    scenario_data = load_scenario(scenario_file)

    affected_population, population_nodes = (

        get_population_data(

            scenario_data

        )

    )

    print(

        f"Scenario ID             : "
        f"{scenario.get('ScenarioID')}"

    )

    print(

        f"Disaster Type            : "
        f"{disaster_type}"

    )

    print(

        f"Disaster Radius          : "
        f"{disaster_radius} km"

    )

    print(

        f"Initial Search Radius    : "
        f"{current_search_radius} km"

    )

    print(

        f"Affected Population      : "
        f"{affected_population:,}"

    )

    print()

    # ======================================================
    # INITIAL SOLUTION
    # ======================================================

    initial_coverage_radius = max(
        current_search_radius - disaster_radius,
        0.0
    )

    result = solve_current_radius(

        scenario_file,

        scenario_data,

        initial_coverage_radius

    )

    summary = result[
        "summary"
    ]

    expansion_history = []

    expansion_triggered = False

    selected_radius = current_search_radius

    # ======================================================
    # BEST SOLUTION TRACKING
    # ======================================================
    #
    # Every radius gets a fresh GIDS + allocation result.
    # Keep the best result instead of automatically keeping
    # the result from the largest radius.
    #
    # Primary metric  : Population Accommodation %
    # Tie-breaker     : Allocated Population
    # Final tie-breaker: Smaller Search Radius
    # ======================================================

    best_result = copy.deepcopy(result)
    best_summary = copy.deepcopy(summary)
    best_radius = current_search_radius

    def is_better_solution(
        candidate_summary,
        candidate_radius,
        current_summary,
        current_radius
    ):

        candidate_accommodation = (
            candidate_summary[
                "population_accommodation_percent"
            ]
        )

        current_accommodation = (
            current_summary[
                "population_accommodation_percent"
            ]
        )

        if candidate_accommodation > current_accommodation:
            return True

        if candidate_accommodation < current_accommodation:
            return False

        candidate_allocated = (
            candidate_summary[
                "allocated_population"
            ]
        )

        current_allocated = (
            current_summary[
                "allocated_population"
            ]
        )

        if candidate_allocated > current_allocated:
            return True

        if candidate_allocated < current_allocated:
            return False

        return candidate_radius < current_radius

    # ======================================================
    # PRINT INITIAL ANALYSIS
    # ======================================================

    print("=" * 60)
    print("INITIAL CAPACITY ANALYSIS")
    print("=" * 60)
    print()

    print(

        f"Suitable Shelters       : "
        f"{len(get_module3_shelters(scenario_data)):,}"

    )

    print(

        f"Serviceable Shelters    : "
        f"{len(result['serviceable_shelters']):,}"

    )

    print(

        f"Serviceable Capacity    : "
        f"{result['serviceable_capacity']:,}"

    )

    print(

        f"Selected Shelters       : "
        f"{len(result['selected_shelters']):,}"

    )

    print(

        f"Selected Capacity       : "
        f"{summary['total_selected_capacity']:,}"

    )

    print(

        f"Allocated Population    : "
        f"{summary['allocated_population']:,}"

    )

    print(

        f"Unallocated Population  : "
        f"{summary['unallocated_population']:,}"

    )

    print(

        f"Accommodation           : "
        f"{summary['population_accommodation_percent']:.2f}%"

    )

    print()

    # ======================================================
    # DETERMINE IF EXPANSION IS REQUIRED
    # ======================================================
    #
    # IMPORTANT:
    #
    # We do NOT expand merely because GIDS selected fewer
    # shelters than expected.
    #
    # Expansion is required when:
    #
    # 1. Actual allocation is incomplete.
    #
    # AND
    #
    # 2. The current radius cannot adequately solve the
    #    evacuation problem.
    #
    # ======================================================

    capacity_sufficient = (

        result[
            "serviceable_capacity"
        ]

        >=

        affected_population

    )

    allocation_complete = solution_is_complete(

        summary,

        affected_population

    )

    # ======================================================
    # IF ALLOCATION IS ALREADY COMPLETE
    # ======================================================

    if allocation_complete:

        final_status = "SUCCESS"

    else:

        expansion_triggered = True

        # ==================================================
        # CAPACITY INSUFFICIENT / ALLOCATION INCOMPLETE
        # ==================================================

        print()
        print("=" * 60)
        print("CAPACITY / ALLOCATION INSUFFICIENT")
        print("=" * 60)
        print()

        print(

            f"Serviceable Capacity    : "
            f"{result['serviceable_capacity']:,}"

        )

        print(

            f"Required Capacity       : "
            f"{affected_population:,}"

        )

        print(

            f"Capacity Shortfall      : "
            f"{max(affected_population - result['serviceable_capacity'], 0):,}"

        )

        print()

        # ==================================================
        # BUILD EXPANSION PLAN
        # ==================================================

        expansion_steps = build_expansion_steps(

            disaster_radius,

            current_search_radius

        )

        # ==================================================
        # PROCESS EACH EXPANSION STEP
        # ==================================================

        for step in expansion_steps:

            target_radius = step[
                "SearchRadius_km"
            ]

            evacuation_time = step[
                "EvacuationTimeHours"
            ]

            walking_reach = step[
                "WalkingReach_km"
            ]

            print()
            print("=" * 60)
            print("DYNAMIC RADIUS EXPANSION")
            print("=" * 60)
            print()

            print(

                f"Evacuation Time        : "
                f"{evacuation_time} hours"

            )

            print(

                f"Walking Reach          : "
                f"{walking_reach} km"

            )

            print(

                f"New Search Radius      : "
                f"{target_radius} km"

            )

            # ==================================================
            # UPDATE SCENARIO SEARCH RADIUS
            # ==================================================

            scenario_data[
                "Scenario"
            ][
                "ShelterSearchRadius_km"
            ] = target_radius

            save_scenario(

                scenario_file,

                scenario_data

            )

            # ==================================================
            # RERUN MODULE 2
            # ==================================================

            rerun_module2(

                scenario_file

            )

            # ==================================================
            # RERUN MODULE 3
            # ==================================================

            rerun_module3(

                scenario_file

            )

            # ==================================================
            # RELOAD UPDATED SCENARIO
            # ==================================================

            scenario_data = load_scenario(

                scenario_file

            )

            # ==================================================
            # SOLVE NEW RADIUS
            # ==================================================

            result = solve_current_radius(

                scenario_file,

                scenario_data,

                walking_reach

            )

            summary = result[
                "summary"
            ]

            # ==================================================
            # COMPARE WITH BEST SOLUTION SO FAR
            # ==================================================

            if is_better_solution(
                summary,
                target_radius,
                best_summary,
                best_radius
            ):

                best_result = copy.deepcopy(result)
                best_summary = copy.deepcopy(summary)
                best_radius = target_radius

                print()
                print("=" * 60)
                print("NEW BEST SOLUTION FOUND")
                print("=" * 60)
                print()

                print(
                    f"Best Search Radius      : "
                    f"{best_radius} km"
                )

                print(
                    f"Best Accommodation      : "
                    f"{best_summary['population_accommodation_percent']:.2f}%"
                )

                print(
                    f"Best Allocated Population: "
                    f"{best_summary['allocated_population']:,}"
                )

            else:

                print()
                print(
                    f"Best solution remains "
                    f"{best_radius} km / "
                    f"{best_summary['population_accommodation_percent']:.2f}%"
                )

            # ==================================================
            # CAPTURE EXPANSION HISTORY
            # ==================================================

            expansion_history.append({

                "EvacuationTimeHours":
                    evacuation_time,

                "WalkingReach_km":
                    walking_reach,

                "CoverageRadius_km":
                    walking_reach,

                "SearchRadius_km":
                    target_radius,

                "SuitableShelters":
                    len(

                        get_module3_shelters(

                            scenario_data

                        )

                    ),

                "ServiceableShelters":
                    len(

                        result[
                            "serviceable_shelters"
                        ]

                    ),

                "ServiceableCapacity":
                    result[
                        "serviceable_capacity"
                    ],

                "SelectedShelters":
                    len(

                        result[
                            "selected_shelters"
                        ]

                    ),

                "SelectedCapacity":
                    summary[
                        "total_selected_capacity"
                    ],

                "AllocatedPopulation":
                    summary[
                        "allocated_population"
                    ],

                "UnallocatedPopulation":
                    summary[
                        "unallocated_population"
                    ],

                "CapacityShortfall":
                    summary[
                        "capacity_shortfall"
                    ],

                "GeographicCoveragePercent":
                    summary[
                        "geographic_coverage_percent"
                    ],

                "PopulationAccommodationPercent":
                    summary[
                        "population_accommodation_percent"
                    ]

            })

            # ==================================================
            # PRINT EXPANSION RESULT
            # ==================================================

            print()
            print("-" * 60)

            print(

                f"Suitable Shelters       : "
                f"{len(get_module3_shelters(scenario_data)):,}"

            )

            print(

                f"Serviceable Shelters    : "
                f"{len(result['serviceable_shelters']):,}"

            )

            print(

                f"Serviceable Capacity    : "
                f"{result['serviceable_capacity']:,}"

            )

            print(

                f"Selected Shelters       : "
                f"{len(result['selected_shelters']):,}"

            )

            print(

                f"Selected Capacity       : "
                f"{summary['total_selected_capacity']:,}"

            )

            print(

                f"Allocated Population    : "
                f"{summary['allocated_population']:,}"

            )

            print(

                f"Unallocated Population  : "
                f"{summary['unallocated_population']:,}"

            )

            print(

                f"Geographic Coverage    : "
                f"{summary['geographic_coverage_percent']:.2f}%"

            )

            print(

                f"Accommodation           : "
                f"{summary['population_accommodation_percent']:.2f}%"

            )

            # ==================================================
            # SUCCESS CHECK
            # ==================================================
            #
            # Do not break here.
            #
            # Even if one radius reaches 100% accommodation,
            # we still evaluate the remaining expansion radii
            # so the BEST result is determined consistently.
            # ==================================================

            if solution_is_complete(
                summary,
                affected_population
            ):

                print()
                print(
                    "Capacity requirement satisfied at "
                    f"{target_radius} km."
                )

                print(
                    "Continuing radius evaluation to verify "
                    "the best solution."
                )

        else:

            # ==================================================
            # ALL EXPANSION STEPS EXHAUSTED
            # ==================================================

            final_status = "CAPACITY_INSUFFICIENT"

    # ======================================================
    # RESTORE BEST SOLUTION
    # ======================================================
    #
    # The largest radius is NOT automatically the final
    # solution. Restore the best complete GIDS/allocation
    # snapshot found during the radius search.
    # ======================================================

    result = copy.deepcopy(best_result)
    summary = copy.deepcopy(best_summary)
    selected_radius = best_radius

    # ======================================================
    # SYNCHRONIZE MODULE 2 + MODULE 3 WITH BEST RADIUS
    # ======================================================
    #
    # The expansion loop may have ended at a larger radius.
    # Rebuild candidate/suitable shelters at the preserved
    # best radius so the JSON remains internally consistent.
    # ======================================================

    scenario_data["Scenario"]["ShelterSearchRadius_km"] = (
        best_radius
    )

    save_scenario(
        scenario_file,
        scenario_data
    )

    rerun_module2(
        scenario_file
    )

    rerun_module3(
        scenario_file
    )

    scenario_data = load_scenario(
        scenario_file
    )

    best_coverage_radius = max(
        best_radius - disaster_radius,
        0.0
    )

    # Re-solve the best radius after synchronization.
    result = solve_current_radius(
        scenario_file,
        scenario_data,
        best_coverage_radius
    )

    summary = result["summary"]

    # The synchronized best-radius run is the authoritative
    # final snapshot written to Module 4.
    best_result = copy.deepcopy(result)
    best_summary = copy.deepcopy(summary)

    # ======================================================
    # FINAL STATUS SAFETY CHECK
    # ======================================================

    if solution_is_complete(

        summary,

        affected_population

    ):

        final_status = "SUCCESS"

    else:

        final_status = "CAPACITY_INSUFFICIENT"

    # ======================================================
    # FINAL EXECUTION TIME
    # ======================================================

    execution_time = round(

        time.time()
        -
        start_time,

        3

    )

    # ======================================================
    # MODULE 4 RESULT
    # ======================================================

    module4_result = {

        "status":
            final_status,

        "disaster_type":
            disaster_type,

        "disaster_radius_km":
            disaster_radius,

        "initial_search_radius_km":
            current_search_radius,

        "final_search_radius_km":
            selected_radius,

        "best_solution_radius_km":
            best_radius,

        "best_solution_accommodation_percent":
            best_summary[
                "population_accommodation_percent"
            ],

        "best_solution_allocated_population":
            best_summary[
                "allocated_population"
            ],

        "best_solution_selected_shelters":
            len(
                best_result[
                    "selected_shelters"
                ]
            ),

        "coverage_radius_km":
            max(selected_radius - disaster_radius, 0.0),

        "independence_radius_km":
            INDEPENDENCE_RADIUS_KM,

        "walking_speed_kmph":
            WALKING_SPEED_KMPH,

        "expansion_triggered":
            expansion_triggered,

        "expansion_history":
            expansion_history,

        "suitable_shelters_at_final_radius":
            len(

                get_module3_shelters(

                    scenario_data

                )

            ),

        "serviceable_shelters_at_final_radius":
            len(

                result[
                    "serviceable_shelters"
                ]

            ),

        "serviceable_capacity_at_final_radius":
            result[
                "serviceable_capacity"
            ],

        "selected_shelters":
            result[
                "selected_shelters"
            ],

        "total_selected_capacity":
            summary[
                "total_selected_capacity"
            ],

        "affected_population":
            summary[
                "affected_population"
            ],

        "geographically_covered_population":
            summary[
                "geographically_covered_population"
            ],

        "geographically_covered_nodes":
            summary[
                "geographically_covered_nodes"
            ],

        "allocated_population":
            summary[
                "allocated_population"
            ],

        "unallocated_population":
            summary[
                "unallocated_population"
            ],

        "capacity_shortfall":
            summary[
                "capacity_shortfall"
            ],

        "geographic_coverage_percent":
            summary[
                "geographic_coverage_percent"
            ],

        "population_accommodation_percent":
            summary[
                "population_accommodation_percent"
            ],

        "selected_capacity_utilization_percent":
            summary[
                "selected_capacity_utilization_percent"
            ],

        "population_assignments":
            result[
                "assignments"
            ],

        "execution_time":
            execution_time

    }

    # ======================================================
    # WRITE MODULE 4 INTO SCENARIO JSON
    # ======================================================

    scenario_data[
        "Modules"
    ][
        "Module4"
    ] = module4_result

    save_scenario(

        scenario_file,

        scenario_data

    )

    # ======================================================
    # FINAL REPORT
    # ======================================================

    print()
    print("=" * 60)
    print("MODULE 4 RESULTS")
    print("=" * 60)
    print()

    print(

        f"Status                   : "
        f"{final_status}"

    )

    print(

        f"Final Search Radius      : "
        f"{selected_radius} km"

    )

    print(

        f"Suitable Shelters        : "
        f"{len(get_module3_shelters(scenario_data)):,}"

    )

    print(

        f"Serviceable Shelters     : "
        f"{len(result['serviceable_shelters']):,}"

    )

    print(

        f"Serviceable Capacity     : "
        f"{result['serviceable_capacity']:,}"

    )

    print(

        f"Selected Shelters        : "
        f"{len(result['selected_shelters']):,}"

    )

    print(

        f"Selected Capacity        : "
        f"{summary['total_selected_capacity']:,}"

    )

    print(

        f"Affected Population      : "
        f"{affected_population:,}"

    )

    print(

        f"Allocated Population     : "
        f"{summary['allocated_population']:,}"

    )

    print(

        f"Unallocated Population   : "
        f"{summary['unallocated_population']:,}"

    )

    print(

        f"Capacity Shortfall       : "
        f"{summary['capacity_shortfall']:,}"

    )

    print(

        f"Geographic Coverage      : "
        f"{summary['geographic_coverage_percent']:.2f}%"

    )

    print(

        f"Population Accommodation : "
        f"{summary['population_accommodation_percent']:.2f}%"

    )

    print(

        f"Execution Time           : "
        f"{execution_time} sec"

    )

    print()

    # ======================================================
    # SELECTED SHELTERS REPORT
    # ======================================================

    print("-" * 60)
    print("SELECTED SHELTERS")
    print("-" * 60)
    print()

    print(

        f"{'ShelterID':<12}"
        f"{'Shelter':<35}"
        f"{'Capacity':>10}"
        f"{'Assigned':>10}"

    )

    print("-" * 70)

    for shelter in result[
        "selected_shelters"
    ][:20]:

        print(

            f"{str(shelter.get('ShelterID')):<12}"

            f"{str(shelter.get('ShelterName', ''))[:34]:<35}"

            f"{shelter.get('DefaultCapacity', 0):>10,}"

            f"{shelter.get('AssignedPopulation', 0):>10,}"

        )

    print()

    print("=" * 60)
    print("MODULE 4 COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return module4_result


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
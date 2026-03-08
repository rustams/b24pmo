def allocations_overview_payload() -> dict:
    return {
        "module": "resources.allocations",
        "status": "scaffolded",
        "next": "Implement List operations for ResourceAllocations",
    }


def capacity_overview_payload() -> dict:
    return {
        "module": "resources.capacity",
        "status": "scaffolded",
        "next": "Implement resource_capacity_cache aggregation",
    }

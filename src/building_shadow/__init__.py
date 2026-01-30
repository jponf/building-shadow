"""Building Shadow - Visualize building shadows using OpenStreetMap data."""

from building_shadow.core import (
    compute_shadows,
    fetch_buildings,
    get_coordinates_from_address,
)


__version__ = "0.1.0"
__all__ = [
    "compute_shadows",
    "fetch_buildings",
    "get_coordinates_from_address",
]

"""Custom building geometry generation from user-defined shapes."""

from pathlib import Path

import geopandas as gpd
from pyproj import Geod
from shapely.geometry import Polygon

from building_shadow.models import (
    WGS84_EPSG,
    CylinderBuilding,
    PolygonBuilding,
    parse_custom_buildings,
)


def create_polygon_from_corners(corners: list[tuple[float, float]]) -> Polygon:
    """Create a Shapely polygon from corner coordinates.

    Args:
        corners: List of [lat, lon] coordinate pairs.

    Returns:
        Shapely Polygon in WGS84 (lon, lat order for Shapely).
    """
    # Convert from [lat, lon] to [lon, lat] for Shapely
    coords = [(lon, lat) for lat, lon in corners]
    return Polygon(coords)


def create_cylinder_polygon(
    lat: float,
    lon: float,
    radius_meters: float,
    num_segments: int = 32,
) -> Polygon:
    """Create a circular polygon approximating a cylinder footprint.

    Uses geodesic buffering for accurate radius in meters.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        radius_meters: Radius in meters.
        num_segments: Number of segments to approximate the circle.

    Returns:
        Shapely Polygon representing the cylinder footprint.
    """
    geod = Geod(ellps="WGS84")

    # Generate points around the circle
    angles = [i * (360.0 / num_segments) for i in range(num_segments)]
    coords = []
    for angle in angles:
        dest_lon, dest_lat, _ = geod.fwd(lon, lat, angle, radius_meters)
        coords.append((dest_lon, dest_lat))

    return Polygon(coords)


def custom_buildings_to_geodataframe(
    buildings: list[PolygonBuilding | CylinderBuilding],
) -> gpd.GeoDataFrame:
    """Convert custom buildings to a GeoDataFrame.

    Args:
        buildings: List of custom building definitions.

    Returns:
        GeoDataFrame with geometry, building_id, and height columns.
    """
    geometries = []
    heights = []

    for building in buildings:
        if isinstance(building, PolygonBuilding):
            geom = create_polygon_from_corners(building.corners)
        else:  # CylinderBuilding
            geom = create_cylinder_polygon(
                building.lat,
                building.lon,
                building.radius,
            )
        geometries.append(geom)
        heights.append(building.height)

    return gpd.GeoDataFrame(
        {
            "geometry": geometries,
            "building_id": range(len(geometries)),
            "height": heights,
        },
        crs=f"EPSG:{WGS84_EPSG}",
    )


def load_custom_buildings(json_path: Path) -> gpd.GeoDataFrame:
    """Load custom buildings from JSON and return as GeoDataFrame.

    Args:
        json_path: Path to JSON file with building definitions.

    Returns:
        GeoDataFrame with custom building geometries.
    """
    buildings = parse_custom_buildings(json_path)
    return custom_buildings_to_geodataframe(buildings)

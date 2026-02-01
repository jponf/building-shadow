"""Core functionality for building shadow computation.

This module provides the main shadow computation logic and geocoding.
Building data fetching is handled by the sources package, and
visualization is handled by the visualization module.
"""

from datetime import UTC, date, datetime

import geopandas as gpd
import pandas as pd
import pybdshadow
from geopy.geocoders import Nominatim

from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    WGS84_EPSG,
    DataSource,
)
from building_shadow.sources import create_source


def get_coordinates_from_address(address: str) -> tuple[float, float]:
    """Convert a street address to latitude/longitude coordinates.

    Uses the Nominatim geocoding service (OpenStreetMap).

    Args:
        address: Street address string (e.g., "123 Main St, City, Country").

    Returns:
        Tuple of (latitude, longitude).

    Raises:
        ValueError: If address could not be geocoded.
    """
    geolocator = Nominatim(user_agent="building_shadow_app")
    location = geolocator.geocode(address)

    if location is None:
        msg = f"Could not geocode address: {address}"
        raise ValueError(msg)

    return (location.latitude, location.longitude)


def fetch_buildings(
    latitude: float,
    longitude: float,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    default_height: float = DEFAULT_BUILDING_HEIGHT,
    source: DataSource = DataSource.OSM,
) -> gpd.GeoDataFrame:
    """Fetch building footprints from the specified data source.

    This is a convenience wrapper around the sources package.

    Args:
        latitude: Center point latitude.
        longitude: Center point longitude.
        radius_meters: Search radius in meters.
        default_height: Default building height when not available.
        source: Data source to use (OSM, OVERTURE, or CATASTRO).

    Returns:
        GeoDataFrame containing building geometries with height information.

    Raises:
        ValueError: If no buildings are found.
    """
    data_source = create_source(source)
    building_data = data_source.fetch(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        default_height=default_height,
    )
    return building_data.buildings


def compute_shadows(
    buildings: gpd.GeoDataFrame,
    target_date: date | None = None,
    start_hour: int = 9,
    end_hour: int = 21,
    timezone: str = "Europe/Madrid",
) -> dict[int, gpd.GeoDataFrame]:
    """Compute shadows for buildings at different hours of the day.

    Args:
        buildings: GeoDataFrame with building geometries and heights.
        target_date: Date for sun position calculation (defaults to today).
        start_hour: Start hour for shadow computation (default: 9).
        end_hour: End hour for shadow computation (default: 21).
        timezone: Local timezone for the location.

    Returns:
        Dictionary mapping hour to shadow GeoDataFrame.
    """
    date_str = _format_date(target_date)
    shadows_by_hour: dict[int, gpd.GeoDataFrame] = {}

    for hour in range(start_hour, end_hour + 1):
        datetime_str = f"{date_str} {hour:02d}:00:00"
        local_dt = pd.to_datetime(datetime_str).tz_localize(timezone)
        utc_dt = local_dt.tz_convert("UTC")

        try:
            shadow_gdf = pybdshadow.bdshadow_sunlight(buildings, utc_dt)
            if shadow_gdf is not None and not shadow_gdf.empty:
                shadows_by_hour[hour] = shadow_gdf
        except Exception:  # noqa: BLE001, S110
            pass

    return shadows_by_hour


def compute_shadow_animation_data(
    buildings: gpd.GeoDataFrame,
    target_date: date | None = None,
    start_hour: int = 9,
    end_hour: int = 21,
    timezone: str = "Europe/Madrid",
) -> gpd.GeoDataFrame:
    """Compute shadow data suitable for animation visualization.

    Creates a single GeoDataFrame with all shadows and a datetime column
    for time-based animation.

    Args:
        buildings: GeoDataFrame with building geometries and heights.
        target_date: Date for sun position calculation (defaults to today).
        start_hour: Start hour for shadow computation (default: 9).
        end_hour: End hour for shadow computation (default: 21).
        timezone: Local timezone for the location.

    Returns:
        GeoDataFrame with all shadows and datetime/hour columns.

    Raises:
        ValueError: If no shadows could be computed.
    """
    date_str = _format_date(target_date)
    all_shadows: list[gpd.GeoDataFrame] = []

    for hour in range(start_hour, end_hour + 1):
        datetime_str = f"{date_str} {hour:02d}:00:00"
        local_dt = pd.to_datetime(datetime_str).tz_localize(timezone)
        utc_dt = local_dt.tz_convert("UTC")

        try:
            shadow_gdf = pybdshadow.bdshadow_sunlight(buildings, utc_dt)
            if shadow_gdf is not None and not shadow_gdf.empty:
                shadow_gdf = shadow_gdf.copy()
                shadow_gdf["datetime"] = local_dt
                shadow_gdf["hour"] = hour
                all_shadows.append(shadow_gdf)
        except Exception:  # noqa: BLE001, S110
            pass

    if not all_shadows:
        msg = "No shadows could be computed for the given time range"
        raise ValueError(msg)

    combined = gpd.GeoDataFrame(pd.concat(all_shadows, ignore_index=True))
    return combined.set_crs(epsg=WGS84_EPSG)


def _format_date(target_date: date | None = None) -> str:
    """Format a date for shadow computation.

    Args:
        target_date: Date to use (defaults to today).

    Returns:
        Date string in YYYY-MM-DD format.
    """
    if target_date is None:
        target_date = datetime.now(tz=UTC).date()
    return target_date.strftime("%Y-%m-%d")

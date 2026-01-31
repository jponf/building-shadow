"""Data models for building shadow computation."""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

import geopandas as gpd
from pydantic import BaseModel, Field, TypeAdapter, field_validator


class Season(str, Enum):
    """Season enum for sun trajectory selection."""

    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class DataSource(str, Enum):
    """Available data sources for building footprints."""

    OSM = "osm"
    OVERTURE = "overture"
    CATASTRO = "catastro"


SEASON_DATES = {
    Season.SPRING: "03-21",
    Season.SUMMER: "06-21",
    Season.AUTUMN: "09-21",
    Season.WINTER: "12-21",
}

WGS84_EPSG = 4326
WEB_MERCATOR_EPSG = 3857

DEFAULT_BUILDING_HEIGHT = 15.0
DEFAULT_RADIUS_METERS = 300
METERS_PER_FLOOR = 3.0


@dataclass
class BuildingData:
    """Container for building data with metadata about the source."""

    buildings: gpd.GeoDataFrame
    source: DataSource
    center_lat: float
    center_lon: float
    radius_meters: float

    @property
    def count(self) -> int:
        """Return the number of buildings."""
        return len(self.buildings)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BuildingData(source={self.source.value}, "
            f"count={self.count}, radius={self.radius_meters}m)"
        )


# Custom building models for user-defined shapes

# Coordinate bounds
MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0


class PolygonBuilding(BaseModel):
    """A polygon building defined by corner coordinates."""

    shape: Literal["polygon"]
    corners: list[tuple[float, float]] = Field(
        ...,
        min_length=3,
        description="List of [lat, lon] coordinate pairs defining vertices",
    )
    height: float = Field(..., gt=0, description="Building height in meters")

    @field_validator("corners")
    @classmethod
    def validate_corners(
        cls,
        v: list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        """Validate that corners form a valid polygon."""
        for lat, lon in v:
            if not MIN_LAT <= lat <= MAX_LAT:
                msg = f"Latitude must be between {MIN_LAT} and {MAX_LAT}, got {lat}"
                raise ValueError(msg)
            if not MIN_LON <= lon <= MAX_LON:
                msg = f"Longitude must be between {MIN_LON} and {MAX_LON}, got {lon}"
                raise ValueError(msg)
        return v


class CylinderBuilding(BaseModel):
    """A cylindrical building defined by center and radius."""

    shape: Literal["cylinder"]
    lat: float = Field(..., ge=MIN_LAT, le=MAX_LAT, description="Center latitude")
    lon: float = Field(..., ge=MIN_LON, le=MAX_LON, description="Center longitude")
    radius: float = Field(..., gt=0, description="Radius in meters")
    height: float = Field(..., gt=0, description="Building height in meters")


CustomBuilding = Annotated[
    PolygonBuilding | CylinderBuilding,
    Field(discriminator="shape"),
]


def parse_custom_buildings(json_path: Path) -> list[PolygonBuilding | CylinderBuilding]:
    """Parse custom buildings from a JSON file.

    Args:
        json_path: Path to JSON file containing building definitions.

    Returns:
        List of validated custom building objects.

    Raises:
        ValueError: If JSON is invalid or buildings fail validation.
        FileNotFoundError: If the JSON file doesn't exist.
    """
    with json_path.open() as f:
        data = json.load(f)

    adapter: TypeAdapter[list[PolygonBuilding | CylinderBuilding]] = TypeAdapter(
        list[CustomBuilding],
    )
    return adapter.validate_python(data)


def normalize_buildings(
    gdf: gpd.GeoDataFrame,
    default_height: float = DEFAULT_BUILDING_HEIGHT,
) -> gpd.GeoDataFrame:
    """Normalize a GeoDataFrame to the standard building format.

    Ensures the GeoDataFrame has the required columns:
    - geometry: Polygon or MultiPolygon
    - building_id: Unique identifier
    - height: Building height in meters

    Args:
        gdf: Input GeoDataFrame with building geometries.
        default_height: Default height when not available.

    Returns:
        Normalized GeoDataFrame with standard columns.
    """
    result = gdf[["geometry"]].copy()
    result["building_id"] = range(len(result))

    if "height" in gdf.columns:
        import pandas as pd  # noqa: PLC0415

        result["height"] = pd.to_numeric(
            gdf["height"],
            errors="coerce",
        ).fillna(default_height)
    elif "building:levels" in gdf.columns or "num_floors" in gdf.columns:
        import pandas as pd  # noqa: PLC0415

        levels_col = (
            "building:levels" if "building:levels" in gdf.columns else "num_floors"
        )
        levels = pd.to_numeric(gdf[levels_col], errors="coerce").fillna(1)
        result["height"] = levels * METERS_PER_FLOOR
    else:
        result["height"] = default_height

    if result.crs is None:
        result = result.set_crs(epsg=WGS84_EPSG)
    elif result.crs.to_epsg() != WGS84_EPSG:
        result = result.to_crs(epsg=WGS84_EPSG)

    return gpd.GeoDataFrame(result, crs=WGS84_EPSG)

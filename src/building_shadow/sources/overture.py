"""Overture Maps building data source."""

from __future__ import annotations

from typing import Any

import geopandas as gpd
from shapely import wkb

from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    WGS84_EPSG,
    BuildingData,
    DataSource,
    normalize_buildings,
)
from building_shadow.sources.base import BuildingDataSource


# Overture Maps S3 bucket URL (using wildcard for latest release)
OVERTURE_S3_BASE = "s3://overturemaps-us-west-2/release"
OVERTURE_RELEASE = "*"  # Use wildcard to match any available release


class OvertureBuildingSource(BuildingDataSource):
    """Fetch building data from Overture Maps.

    Uses DuckDB to query Overture Maps GeoParquet files directly from S3.
    Requires the 'duckdb' package to be installed.
    """

    source_type = DataSource.OVERTURE

    def __init__(self, release: str = OVERTURE_RELEASE) -> None:
        """Initialize the Overture Maps data source.

        Args:
            release: Overture Maps release version to use.
        """
        self.release = release
        self._duckdb_available: bool | None = None

    def fetch(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        default_height: float = DEFAULT_BUILDING_HEIGHT,
    ) -> BuildingData:
        """Fetch building footprints from Overture Maps.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_meters: Search radius in meters.
            default_height: Default building height when not available.

        Returns:
            BuildingData containing the fetched buildings.

        Raises:
            ValueError: If no buildings are found.
            ImportError: If duckdb is not installed.
            ConnectionError: If unable to connect to S3.
        """
        if not self.is_available():
            msg = "DuckDB is required for Overture Maps. Install with: uv add duckdb"
            raise ImportError(msg)

        bbox = self._calculate_bbox(latitude, longitude, radius_meters)
        raw_data = self._query_overture(bbox)

        if raw_data.empty:
            msg = (
                f"No buildings found within {radius_meters}m "
                f"of ({latitude}, {longitude})"
            )
            raise ValueError(msg)

        gdf = self._convert_to_geodataframe(raw_data)
        polygons = self.filter_polygons(gdf)

        if polygons.empty:
            msg = f"No building footprints within {radius_meters}m of given location"
            raise ValueError(msg)

        normalized = normalize_buildings(polygons, default_height)

        return BuildingData(
            buildings=normalized,
            source=self.source_type,
            center_lat=latitude,
            center_lon=longitude,
            radius_meters=radius_meters,
        )

    def is_available(self) -> bool:
        """Check if DuckDB is available.

        Returns:
            True if duckdb can be imported.
        """
        if self._duckdb_available is None:
            try:
                import duckdb  # noqa: F401, PLC0415

                self._duckdb_available = True
            except ImportError:
                self._duckdb_available = False
        return self._duckdb_available

    def _calculate_bbox(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
    ) -> tuple[float, float, float, float]:
        """Calculate bounding box from center point and radius.

        Args:
            latitude: Center latitude.
            longitude: Center longitude.
            radius_meters: Radius in meters.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat).
        """
        # Approximate degrees per meter (varies with latitude)
        lat_deg_per_m = 1 / 111320
        lon_deg_per_m = 1 / (111320 * abs(cos_deg(latitude)))

        lat_delta = radius_meters * lat_deg_per_m
        lon_delta = radius_meters * lon_deg_per_m

        return (
            longitude - lon_delta,  # min_lon
            latitude - lat_delta,  # min_lat
            longitude + lon_delta,  # max_lon
            latitude + lat_delta,  # max_lat
        )

    def _query_overture(
        self,
        bbox: tuple[float, float, float, float],
    ) -> Any:  # noqa: ANN401
        """Query Overture Maps for buildings in bounding box.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat).

        Returns:
            DataFrame with building data.
        """
        import duckdb  # noqa: PLC0415

        min_lon, min_lat, max_lon, max_lat = bbox

        conn = duckdb.connect()
        conn.execute("INSTALL spatial; LOAD spatial;")
        conn.execute("INSTALL httpfs; LOAD httpfs;")
        conn.execute("SET s3_region='us-west-2';")

        parquet_path = (
            f"{OVERTURE_S3_BASE}/{self.release}/theme=buildings/type=building/*"
        )

        query = f"""
        SELECT
            id,
            ST_AsWKB(geometry) as geometry,
            height,
            num_floors,
            class
        FROM read_parquet('{parquet_path}', filename=true, hive_partitioning=true)
        WHERE bbox.xmin >= {min_lon}
          AND bbox.xmax <= {max_lon}
          AND bbox.ymin >= {min_lat}
          AND bbox.ymax <= {max_lat}
        """  # noqa: S608

        return conn.execute(query).fetchdf()

    def _convert_to_geodataframe(
        self,
        df: Any,  # noqa: ANN401
    ) -> gpd.GeoDataFrame:
        """Convert DataFrame with WKB geometry to GeoDataFrame.

        Args:
            df: DataFrame with 'geometry' column containing WKB bytes.

        Returns:
            GeoDataFrame with parsed geometries.
        """

        def parse_geometry(x: Any) -> Any:  # noqa: ANN401
            if x is None:
                return None
            # Handle bytearray from DuckDB
            if isinstance(x, bytearray):
                x = bytes(x)
            return wkb.loads(x)

        geometries = df["geometry"].apply(parse_geometry)

        gdf = gpd.GeoDataFrame(
            df.drop(columns=["geometry"]),
            geometry=geometries,
            crs=WGS84_EPSG,
        )

        # Rename num_floors to match our normalization
        if "num_floors" in gdf.columns:
            gdf = gdf.rename(columns={"num_floors": "building:levels"})

        return gdf


def cos_deg(degrees: float) -> float:
    """Calculate cosine of angle in degrees.

    Args:
        degrees: Angle in degrees.

    Returns:
        Cosine of the angle.
    """
    import math  # noqa: PLC0415

    return math.cos(math.radians(degrees))

"""Base class for building data sources."""

from abc import ABC, abstractmethod

import geopandas as gpd

from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    BuildingData,
    DataSource,
)


class BuildingDataSource(ABC):
    """Abstract base class for building data sources.

    All data sources must implement the fetch method to retrieve
    building footprints for a given location.
    """

    source_type: DataSource

    @abstractmethod
    def fetch(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        default_height: float = DEFAULT_BUILDING_HEIGHT,
    ) -> BuildingData:
        """Fetch building footprints for the given location.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_meters: Search radius in meters.
            default_height: Default building height when not available.

        Returns:
            BuildingData containing the fetched buildings.

        Raises:
            ValueError: If no buildings are found.
            ConnectionError: If the data source is unavailable.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this data source is available.

        Returns:
            True if the source can be used, False otherwise.
        """

    @staticmethod
    def filter_polygons(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Filter GeoDataFrame to only include polygon geometries.

        Args:
            gdf: Input GeoDataFrame.

        Returns:
            GeoDataFrame with only Polygon and MultiPolygon geometries.
        """
        return gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()

    @staticmethod
    def points_to_polygons(
        gdf: gpd.GeoDataFrame,
        buffer_meters: float = 5.0,
    ) -> gpd.GeoDataFrame:
        """Convert Point geometries to circular polygons.

        Args:
            gdf: GeoDataFrame with Point geometries.
            buffer_meters: Radius of the circular buffer in meters.

        Returns:
            GeoDataFrame with polygon geometries.
        """
        from building_shadow.models import (  # noqa: PLC0415
            WEB_MERCATOR_EPSG,
            WGS84_EPSG,
        )

        points = gdf[gdf.geometry.geom_type == "Point"].copy()
        if points.empty:
            return gpd.GeoDataFrame()

        points_projected = points.to_crs(epsg=WEB_MERCATOR_EPSG)
        points_projected["geometry"] = points_projected.geometry.buffer(buffer_meters)
        return points_projected.to_crs(epsg=WGS84_EPSG)

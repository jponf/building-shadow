"""OpenStreetMap building data source."""

import geopandas as gpd
import osmnx as ox
import pandas as pd

from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    WGS84_EPSG,
    BuildingData,
    DataSource,
    normalize_buildings,
)
from building_shadow.sources.base import BuildingDataSource


class OSMBuildingSource(BuildingDataSource):
    """Fetch building data from OpenStreetMap via Overpass API.

    Uses OSMnx to query OpenStreetMap for building footprints.
    Supports both building and building:part tags, and can convert
    Point features (POIs) to approximate polygons.
    """

    source_type = DataSource.OSM

    def __init__(
        self,
        *,
        include_points: bool = True,
        point_radius_meters: float = 5.0,
    ) -> None:
        """Initialize the OSM data source.

        Args:
            include_points: Convert Point features to circular polygons.
            point_radius_meters: Radius for Point-to-polygon conversion.
        """
        self.include_points = include_points
        self.point_radius_meters = point_radius_meters

    def fetch(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        default_height: float = DEFAULT_BUILDING_HEIGHT,
    ) -> BuildingData:
        """Fetch building footprints from OpenStreetMap.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_meters: Search radius in meters.
            default_height: Default building height when not available.

        Returns:
            BuildingData containing the fetched buildings.

        Raises:
            ValueError: If no buildings are found.
        """
        all_buildings = self._fetch_raw_buildings(latitude, longitude, radius_meters)

        if not all_buildings:
            msg = (
                f"No buildings found within {radius_meters}m "
                f"of ({latitude}, {longitude})"
            )
            raise ValueError(msg)

        buildings_gdf = self._merge_and_deduplicate(all_buildings)
        polygons = self._process_geometries(buildings_gdf)

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
        """Check if OSM/Overpass API is available.

        Returns:
            True (OSM is always assumed to be available).
        """
        return True

    def _fetch_raw_buildings(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
    ) -> list[gpd.GeoDataFrame]:
        """Fetch raw building data from OSM.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_meters: Search radius in meters.

        Returns:
            List of GeoDataFrames with building features.
        """
        tags_to_try: list[dict[str, bool | str | list[str]]] = [
            {"building": True},
            {"building:part": True},
        ]

        all_buildings: list[gpd.GeoDataFrame] = []

        for tags in tags_to_try:
            try:
                gdf = ox.features_from_point(
                    (latitude, longitude),
                    tags=tags,
                    dist=radius_meters,
                )
                if not gdf.empty:
                    all_buildings.append(gdf)
            except Exception:  # noqa: BLE001, S110
                pass

        return all_buildings

    def _merge_and_deduplicate(
        self,
        gdfs: list[gpd.GeoDataFrame],
    ) -> gpd.GeoDataFrame:
        """Merge multiple GeoDataFrames and remove duplicates.

        Args:
            gdfs: List of GeoDataFrames to merge.

        Returns:
            Merged and deduplicated GeoDataFrame.
        """
        merged = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        return merged.drop_duplicates(subset=["geometry"])

    def _process_geometries(
        self,
        gdf: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """Process geometries, converting points to polygons if enabled.

        Args:
            gdf: Input GeoDataFrame with mixed geometry types.

        Returns:
            GeoDataFrame with only polygon geometries.
        """
        polygons = self.filter_polygons(gdf)

        if self.include_points:
            point_polygons = self.points_to_polygons(gdf, self.point_radius_meters)
            if not point_polygons.empty:
                polygons = gpd.GeoDataFrame(
                    pd.concat([polygons, point_polygons], ignore_index=True),
                )

        if polygons.crs is None:
            polygons = polygons.set_crs(epsg=WGS84_EPSG)

        return polygons

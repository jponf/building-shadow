"""Spanish Cadastre (Catastro) building data source."""

from __future__ import annotations

import geopandas as gpd

from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    METERS_PER_FLOOR,
    WGS84_EPSG,
    BuildingData,
    DataSource,
    normalize_buildings,
)
from building_shadow.sources.base import BuildingDataSource


# Spanish Cadastre INSPIRE WFS endpoint
CATASTRO_WFS_URL = "http://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwfs.aspx"
CATASTRO_LAYER = "BU.Building"

# Spain bounding box (including Canary Islands)
SPAIN_LAT_MIN = 27.5
SPAIN_LAT_MAX = 43.8
SPAIN_LON_MIN = -18.2
SPAIN_LON_MAX = 4.4


class CatastroBuildingSource(BuildingDataSource):
    """Fetch building data from Spanish Cadastre (Catastro).

    Uses the INSPIRE WFS service provided by the Dirección General del Catastro.
    Only available for locations within Spain.
    """

    source_type = DataSource.CATASTRO

    def __init__(
        self,
        wfs_url: str = CATASTRO_WFS_URL,
        layer: str = CATASTRO_LAYER,
        timeout: int = 30,
    ) -> None:
        """Initialize the Catastro data source.

        Args:
            wfs_url: WFS service URL.
            layer: Layer name to query.
            timeout: Request timeout in seconds.
        """
        self.wfs_url = wfs_url
        self.layer = layer
        self.timeout = timeout

    def fetch(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        default_height: float = DEFAULT_BUILDING_HEIGHT,
    ) -> BuildingData:
        """Fetch building footprints from Spanish Cadastre.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_meters: Search radius in meters.
            default_height: Default building height when not available.

        Returns:
            BuildingData containing the fetched buildings.

        Raises:
            ValueError: If no buildings are found or location is outside Spain.
            ConnectionError: If unable to connect to WFS service.
        """
        if not self._is_in_spain(latitude, longitude):
            msg = (
                f"Location ({latitude}, {longitude}) is outside Spain. "
                "Catastro only covers Spanish territory."
            )
            raise ValueError(msg)

        bbox = self._calculate_bbox(latitude, longitude, radius_meters)
        gdf = self._query_wfs(bbox)

        if gdf.empty:
            msg = (
                f"No buildings found within {radius_meters}m "
                f"of ({latitude}, {longitude})"
            )
            raise ValueError(msg)

        polygons = self.filter_polygons(gdf)

        if polygons.empty:
            msg = f"No building footprints within {radius_meters}m of given location"
            raise ValueError(msg)

        # Process Catastro-specific fields
        processed = self._process_catastro_fields(polygons, default_height)
        normalized = normalize_buildings(processed, default_height)

        return BuildingData(
            buildings=normalized,
            source=self.source_type,
            center_lat=latitude,
            center_lon=longitude,
            radius_meters=radius_meters,
        )

    def is_available(self) -> bool:
        """Check if Catastro WFS service is reachable.

        Returns:
            True if the service responds.
        """
        import requests  # noqa: PLC0415

        try:
            response = requests.get(
                self.wfs_url,
                params={"service": "WFS", "request": "GetCapabilities"},
                timeout=5,
            )
            return response.ok  # noqa: TRY300
        except Exception:  # noqa: BLE001
            return False

    def _is_in_spain(self, latitude: float, longitude: float) -> bool:
        """Check if coordinates are within Spain's bounding box.

        Args:
            latitude: Latitude to check.
            longitude: Longitude to check.

        Returns:
            True if within Spain's approximate bounds.
        """
        return (
            SPAIN_LAT_MIN <= latitude <= SPAIN_LAT_MAX
            and SPAIN_LON_MIN <= longitude <= SPAIN_LON_MAX
        )

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
        import math  # noqa: PLC0415

        lat_deg_per_m = 1 / 111320
        lon_deg_per_m = 1 / (111320 * abs(math.cos(math.radians(latitude))))

        lat_delta = radius_meters * lat_deg_per_m
        lon_delta = radius_meters * lon_deg_per_m

        return (
            longitude - lon_delta,
            latitude - lat_delta,
            longitude + lon_delta,
            latitude + lat_delta,
        )

    def _query_wfs(
        self,
        bbox: tuple[float, float, float, float],
    ) -> gpd.GeoDataFrame:
        """Query Catastro WFS service for buildings.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat).

        Returns:
            GeoDataFrame with building features.

        Raises:
            ConnectionError: If WFS request fails.
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        wfs_request = (
            f"{self.wfs_url}?"
            f"service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={self.layer}"
            f"&bbox={bbox_str},EPSG:4326"
            f"&outputFormat=application/json"
            f"&srsName=EPSG:4326"
        )

        try:
            gdf = gpd.read_file(wfs_request)
            if gdf.crs is None:
                gdf = gdf.set_crs(epsg=WGS84_EPSG)
        except Exception as e:
            msg = f"Failed to fetch data from Catastro WFS: {e}"
            raise ConnectionError(msg) from e
        else:
            return gdf

    def _process_catastro_fields(
        self,
        gdf: gpd.GeoDataFrame,
        default_height: float,
    ) -> gpd.GeoDataFrame:
        """Process Catastro-specific fields for height estimation.

        Catastro provides:
        - numberOfFloorsAboveGround: Floors above ground
        - numberOfFloorsBelowGround: Basement floors
        - value: Building area or other measurements

        Args:
            gdf: GeoDataFrame with Catastro data.
            default_height: Default height when floors not available.

        Returns:
            GeoDataFrame with standardized height column.
        """
        import pandas as pd  # noqa: PLC0415

        result = gdf.copy()

        # Try to get floor count from Catastro fields
        floors_col = None
        for col in ["numberOfFloorsAboveGround", "numberOfFloors", "floors"]:
            if col in result.columns:
                floors_col = col
                break

        if floors_col is not None:
            floors = pd.to_numeric(result[floors_col], errors="coerce").fillna(1)
            result["height"] = floors * METERS_PER_FLOOR
        else:
            result["height"] = default_height

        return result

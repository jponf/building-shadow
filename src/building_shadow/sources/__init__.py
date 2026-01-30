"""Building data sources package.

Provides unified access to various building footprint data sources:
- OpenStreetMap (OSM) - Default, worldwide coverage
- Overture Maps - High-quality ML-generated footprints
- Spanish Cadastre (Catastro) - Official Spanish building data
"""

from building_shadow.models import DataSource
from building_shadow.sources.base import BuildingDataSource
from building_shadow.sources.catastro import CatastroBuildingSource
from building_shadow.sources.osm import OSMBuildingSource
from building_shadow.sources.overture import OvertureBuildingSource


__all__ = [
    "BuildingDataSource",
    "CatastroBuildingSource",
    "DataSource",
    "OSMBuildingSource",
    "OvertureBuildingSource",
    "create_source",
    "get_available_sources",
]


def create_source(
    source_type: DataSource,
    **kwargs: object,
) -> BuildingDataSource:
    """Factory function to create a building data source.

    Args:
        source_type: Type of data source to create.
        **kwargs: Additional arguments passed to the source constructor.

    Returns:
        Instance of the requested data source.

    Raises:
        ValueError: If the source type is not recognized.

    Examples:
        >>> source = create_source(DataSource.OSM)
        >>> source = create_source(DataSource.CATASTRO)
        >>> source = create_source(DataSource.OVERTURE, release="2024-11-13.0")
    """
    source_map: dict[DataSource, type[BuildingDataSource]] = {
        DataSource.OSM: OSMBuildingSource,
        DataSource.OVERTURE: OvertureBuildingSource,
        DataSource.CATASTRO: CatastroBuildingSource,
    }

    if source_type not in source_map:
        available = ", ".join(s.value for s in DataSource)
        msg = f"Unknown source type: {source_type}. Available: {available}"
        raise ValueError(msg)

    return source_map[source_type](**kwargs)


def get_available_sources() -> list[DataSource]:
    """Get list of data sources that are currently available.

    Checks each source's availability (e.g., required packages installed,
    services reachable).

    Returns:
        List of available DataSource values.

    Examples:
        >>> available = get_available_sources()
        >>> DataSource.OSM in available
        True
    """
    available: list[DataSource] = []

    for source_type in DataSource:
        try:
            source = create_source(source_type)
            if source.is_available():
                available.append(source_type)
        except Exception:  # noqa: BLE001, S110
            pass

    return available

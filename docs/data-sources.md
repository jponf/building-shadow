# Data Sources

Building Shadow supports multiple data sources for building footprints. Each source has different coverage, accuracy, and requirements.

## Available Sources

| Source | Coverage | Requirements | Best For |
|--------|----------|--------------|----------|
| `osm` | Worldwide | None (default) | General use, worldwide locations |
| `overture` | Worldwide | DuckDB package | ML-enhanced footprints |
| `catastro` | Spain only | None | Official Spanish building data |
| Custom JSON | User-defined | `--buildings` flag | Planning, simulation, custom shapes |

### Checking availability

Use the `sources` command to see which sources are available on your system:

```bash
building-shadow sources
```

Output:
```
Available data sources:

  ✓ osm        - OpenStreetMap
              Worldwide, community-maintained

  ✗ overture   - Overture Maps
              ML-generated footprints (duckdb)

  ✓ catastro   - Spanish Cadastre
              Official Spanish building data
```

## OpenStreetMap (OSM)

**Default source** - Works anywhere in the world.

[OpenStreetMap](https://www.openstreetmap.org/) is a collaborative, open-source mapping project. Contributors worldwide map buildings, roads, and other features, making it the largest open geographic database.

### Usage

```bash
# Explicit (default)
building-shadow visualize -a "Times Square, NY" --source osm

# Implicit (osm is the default)
building-shadow visualize -a "Times Square, NY"
```

### How it works

The tool uses [OSMnx](https://osmnx.readthedocs.io/) to query the Overpass API:

1. **`building=*`** - Any feature tagged as a building
2. **`building:part=*`** - Building parts (for complex structures with multiple heights)

Point features (POIs tagged as buildings) are converted to circular polygons (5m radius) when polygon data is unavailable.

### Height determination

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `height` tag | `height=25` → 25m |
| 2 | `building:levels` | `building:levels=8` → 24m (8×3m) |
| 3 | Default | `--default-height 15` → 15m |

### Coverage quality

**Well-mapped**: Major cities in Europe, North America, Japan, tourist destinations

**Sparsely mapped**: Rural areas, developing countries, industrial zones

### Contributing

Help improve OSM data quality:
1. Create an account at [openstreetmap.org](https://www.openstreetmap.org/)
2. Add building footprints from aerial imagery
3. Include height information if known

## Overture Maps

High-quality ML-generated building footprints from the [Overture Maps Foundation](https://overturemaps.org/).

### Requirements

```bash
# Install DuckDB (optional dependency)
uv add duckdb
```

### Usage

```bash
building-shadow visualize -a "San Francisco, CA" --source overture
```

### How it works

Overture Maps provides building data as GeoParquet files on S3. The tool uses DuckDB to:

1. Query the S3 bucket directly (no download required)
2. Filter by bounding box efficiently
3. Extract geometry and height information

### Data quality

Overture combines data from multiple sources using ML techniques:
- OpenStreetMap contributions
- Microsoft ML-generated footprints
- Other commercial and open datasets

This often results in more complete coverage than OSM alone, especially for:
- Suburban areas
- Recently developed regions
- Areas with sparse OSM coverage

### Height data

Overture provides `height` and `num_floors` fields when available from source data.

### Release versions

The tool automatically uses the latest available Overture release by default. To use a specific release version, you can initialize the source with a specific release string via the Python API.

## Spanish Cadastre (Catastro)

Official building data from Spain's [Dirección General del Catastro](https://www.catastro.meh.es/).

### Coverage

Only available for locations within Spain (including Canary Islands):
- Latitude: 27.5° to 43.8°
- Longitude: -18.2° to 4.4°

### Usage

```bash
building-shadow visualize -a "Puerta del Sol, Madrid" --source catastro
building-shadow visualize --lat 41.3851 --lon 2.1734 --source catastro
```

### How it works

Queries the INSPIRE WFS (Web Feature Service):
- Endpoint: `http://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwfs.aspx`
- Layer: `BU.Building`

### Data quality

As official government data, Catastro provides:
- **High accuracy**: Surveyed footprints
- **Floor counts**: `numberOfFloorsAboveGround` field
- **Complete coverage**: All registered buildings in Spain

### Height determination

| Priority | Source | Calculation |
|----------|--------|-------------|
| 1 | `numberOfFloorsAboveGround` | floors × 3m |
| 2 | `numberOfFloors` | floors × 3m |
| 3 | Default | `--default-height` value |

## Custom Buildings (JSON)

User-defined buildings for planning, simulation, or adding shapes not in existing data sources.

### Usage

```bash
building-shadow visualize -a "Location" --buildings custom.json
building-shadow visualize --lat 40.4168 --lon -3.7038 -b planned_buildings.json
```

Custom buildings are **merged** with buildings from the selected data source (OSM, Overture, or Catastro).

### JSON format

The JSON file should contain an array of building definitions. Two shape types are supported:

#### Polygon buildings

Define any shape using corner coordinates:

```json
{
  "shape": "polygon",
  "corners": [
    [40.4168, -3.7038],
    [40.4168, -3.7035],
    [40.4165, -3.7035],
    [40.4165, -3.7038]
  ],
  "height": 25
}
```

| Field | Type | Description |
|-------|------|-------------|
| `shape` | string | Must be `"polygon"` |
| `corners` | array | List of `[latitude, longitude]` pairs (min 3 points) |
| `height` | number | Building height in meters (> 0) |

#### Cylinder buildings

Define circular buildings (towers, silos, etc.):

```json
{
  "shape": "cylinder",
  "lat": 40.417,
  "lon": -3.703,
  "radius": 10,
  "height": 50
}
```

| Field | Type | Description |
|-------|------|-------------|
| `shape` | string | Must be `"cylinder"` |
| `lat` | number | Center latitude (-90 to 90) |
| `lon` | number | Center longitude (-180 to 180) |
| `radius` | number | Radius in meters (> 0) |
| `height` | number | Building height in meters (> 0) |

### Complete example

```json
[
  {
    "shape": "polygon",
    "corners": [
      [40.4168, -3.7038],
      [40.4168, -3.7032],
      [40.4162, -3.7032],
      [40.4162, -3.7038]
    ],
    "height": 45
  },
  {
    "shape": "cylinder",
    "lat": 40.4175,
    "lon": -3.7025,
    "radius": 8,
    "height": 60
  },
  {
    "shape": "polygon",
    "corners": [
      [40.4155, -3.7040],
      [40.4155, -3.7035],
      [40.4150, -3.7037]
    ],
    "height": 20
  }
]
```

### Use cases

- **Urban planning**: Visualize shadow impact of proposed developments
- **Architecture**: Study how a new building affects surrounding areas
- **Solar analysis**: Identify areas that would lose sunlight
- **Simulation**: Model hypothetical building scenarios
- **Missing data**: Add buildings not present in OSM/Overture/Catastro

### Validation

The JSON is validated using [Pydantic](https://docs.pydantic.dev/). Invalid files will produce clear error messages:

```
Error parsing custom buildings: 1 validation error for list[...]
0.corners
  List should have at least 3 items after validation, not 2
```

## Comparison

| Aspect | OSM | Overture | Catastro | Custom JSON |
|--------|-----|----------|----------|-------------|
| Coverage | Worldwide | Worldwide | Spain only | User-defined |
| Updates | Continuous | Periodic releases | Official updates | Manual |
| Height data | Variable | ML-enhanced | Floor counts | User-specified |
| Accuracy | Community-dependent | ML-processed | Surveyed | User-controlled |
| Dependencies | osmnx | duckdb | requests | pydantic |
| Speed | Fast | Slower (S3 query) | Medium | Instant |

## Choosing a source

### For Spain
Use **catastro** for the most accurate, official data:
```bash
building-shadow visualize -a "Barcelona" --source catastro
```

### For other locations
Start with **osm** (default), try **overture** if coverage is sparse:
```bash
# Try OSM first
building-shadow visualize -a "Tokyo, Japan"

# If results are sparse, try Overture
building-shadow visualize -a "Tokyo, Japan" --source overture
```

### For ML-enhanced data
Use **overture** for potentially more complete footprints:
```bash
building-shadow visualize -a "Suburban area" --source overture
```

## Technical details

### Coordinate reference system

All sources use WGS84 (EPSG:4326):
- Latitude: -90 to 90 (negative = south)
- Longitude: -180 to 180 (negative = west)

### Normalization

All sources normalize data to a common format:

```python
GeoDataFrame:
    - geometry: Polygon/MultiPolygon (building footprint)
    - building_id: int (unique identifier)
    - height: float (meters)
```

### Architecture

The source system uses an abstract base class pattern:

```
sources/
├── base.py        # BuildingDataSource ABC
├── osm.py         # OSMBuildingSource
├── overture.py    # OvertureBuildingSource
├── catastro.py    # CatastroBuildingSource
└── __init__.py    # Factory functions
```

Adding a new source requires implementing:
- `fetch(latitude, longitude, radius_meters, default_height) -> BuildingData`
- `is_available() -> bool`

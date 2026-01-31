# CLI Reference

Complete reference for the `building-shadow` command-line interface.

## Commands

### `visualize`

Generate a building shadow visualization.

```bash
building-shadow visualize [OPTIONS]
```

### `sources`

List available data sources and their status.

```bash
building-shadow sources
```

Output shows which sources are available (✓) or unavailable (✗):
```
Available data sources:

  ✓ osm        - OpenStreetMap
              Worldwide, community-maintained

  ✗ overture   - Overture Maps
              ML-generated footprints (duckdb)

  ✓ catastro   - Spanish Cadastre
              Official Spanish building data
```

### `info`

Display information about the tool.

```bash
building-shadow info
```

## Options for `visualize`

### Location (required - choose one)

#### `--address`, `-a`

Street address to center the visualization on. Will be geocoded to coordinates.

```bash
building-shadow visualize --address "Eiffel Tower, Paris, France"
building-shadow visualize -a "1600 Pennsylvania Ave, Washington DC"
```

#### `--latitude`, `--lat`

Latitude coordinate (decimal degrees). Must be used with `--longitude`.

```bash
building-shadow visualize --lat 51.5074 --lon -0.1278
```

#### `--longitude`, `--lon`

Longitude coordinate (decimal degrees). Must be used with `--latitude`.

```bash
building-shadow visualize --lat 35.6762 --lon 139.6503
```

### Area options

#### `--radius`, `-r`

Search radius in meters around the center point. Default: `300`

```bash
# Small area (fast)
building-shadow visualize -a "Location" -r 100

# Large area (slow, more buildings)
building-shadow visualize -a "Location" -r 1000
```

### Data source options

#### `--source`, `-src`

Data source for building footprints. Default: `osm`

Values: `osm`, `overture`, `catastro`

```bash
# Use OpenStreetMap (default)
building-shadow visualize -a "Tokyo, Japan" --source osm

# Use Overture Maps (requires duckdb)
building-shadow visualize -a "San Francisco" --source overture

# Use Spanish Cadastre (Spain only)
building-shadow visualize -a "Madrid" --source catastro
building-shadow visualize -a "Madrid" -src catastro
```

See [Data Sources](data-sources.md) for detailed information about each source.

### Time options

#### `--season`, `-s`

Season for sun trajectory calculation. Default: `summer`

Values: `spring`, `summer`, `autumn`, `winter`

```bash
building-shadow visualize -a "Location" --season winter
building-shadow visualize -a "Location" -s autumn
```

#### `--start-hour`

Start hour for shadow computation (0-23). Default: `9`

```bash
building-shadow visualize -a "Location" --start-hour 6
```

#### `--end-hour`

End hour for shadow computation (0-23). Default: `21`

```bash
building-shadow visualize -a "Location" --end-hour 18
```

#### `--timezone`, `-tz`

Local timezone for the location. Default: `Europe/Madrid`

Use [IANA timezone names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

```bash
# European timezones
building-shadow visualize -a "Berlin" -tz Europe/Berlin
building-shadow visualize -a "London" -tz Europe/London

# American timezones
building-shadow visualize -a "New York" -tz America/New_York
building-shadow visualize -a "Los Angeles" -tz America/Los_Angeles

# Asian timezones
building-shadow visualize -a "Tokyo" -tz Asia/Tokyo
building-shadow visualize -a "Singapore" -tz Asia/Singapore
```

### Building options

#### `--buildings`, `-b`

Path to a JSON file containing custom building definitions. Custom buildings are merged with buildings from the selected data source.

```bash
# Add custom buildings to OSM data
building-shadow visualize -a "Location" --buildings custom.json

# Use with coordinates
building-shadow visualize --lat 40.4168 --lon -3.7038 -b my_buildings.json
```

The JSON file should contain an array of building definitions:

```json
[
  {
    "shape": "polygon",
    "corners": [[lat1, lon1], [lat2, lon2], [lat3, lon3], [lat4, lon4]],
    "height": 25
  },
  {
    "shape": "cylinder",
    "lat": 40.417,
    "lon": -3.703,
    "radius": 10,
    "height": 20
  }
]
```

**Polygon buildings:**
- `shape`: Must be `"polygon"`
- `corners`: Array of `[latitude, longitude]` pairs (minimum 3 points)
- `height`: Building height in meters

**Cylinder buildings:**
- `shape`: Must be `"cylinder"`
- `lat`, `lon`: Center coordinates
- `radius`: Radius in meters
- `height`: Building height in meters

#### `--default-height`

Default building height in meters when not available from data source. Default: `15`

```bash
# Assume taller buildings
building-shadow visualize -a "Manhattan, NY" --default-height 50

# Assume shorter buildings
building-shadow visualize -a "Suburbs" --default-height 8
```

### Output options

#### `--output`, `-o`

Output HTML file path. Default: `building_shadows.html`

```bash
building-shadow visualize -a "Location" -o my_analysis.html
building-shadow visualize -a "Location" -o /path/to/output/shadows.html
```

## Examples

### Basic usage

```bash
# By address
building-shadow visualize -a "Times Square, New York"

# By coordinates
building-shadow visualize --lat 40.7580 --lon -73.9855
```

### Full configuration

```bash
building-shadow visualize \
    --address "Sagrada Familia, Barcelona" \
    --source catastro \
    --radius 400 \
    --season summer \
    --start-hour 8 \
    --end-hour 20 \
    --timezone Europe/Madrid \
    --default-height 20 \
    --output sagrada_shadows.html
```

### Using different data sources

```bash
# Compare OSM vs Catastro for Spanish locations
building-shadow visualize -a "Plaza Mayor, Madrid" -o madrid_osm.html
building-shadow visualize -a "Plaza Mayor, Madrid" --source catastro -o madrid_catastro.html

# Use Overture for areas with sparse OSM coverage
building-shadow visualize -a "Suburban Phoenix, AZ" --source overture -tz America/Phoenix
```

### Adding custom buildings

```bash
# Add planned buildings to existing area
building-shadow visualize -a "Empty lot, City" --buildings planned_development.json

# Simulate a new building's shadow impact
building-shadow visualize --lat 40.4168 --lon -3.7038 -r 200 -b new_tower.json -o impact_study.html
```

Example `planned_development.json`:
```json
[
  {
    "shape": "polygon",
    "corners": [[40.4168, -3.7038], [40.4168, -3.7035], [40.4165, -3.7035], [40.4165, -3.7038]],
    "height": 50
  }
]
```

### Different seasons comparison

```bash
# Generate shadows for each season
for season in spring summer autumn winter; do
    building-shadow visualize \
        -a "Central Park, NY" \
        -s $season \
        -tz America/New_York \
        -o shadows_${season}.html
done
```

### Batch processing locations

```bash
# Process multiple locations
locations=(
    "Colosseum, Rome|Europe/Rome"
    "Big Ben, London|Europe/London"
    "Brandenburg Gate, Berlin|Europe/Berlin"
)

for loc in "${locations[@]}"; do
    IFS='|' read -r address tz <<< "$loc"
    name=$(echo "$address" | cut -d',' -f1 | tr ' ' '_')
    building-shadow visualize -a "$address" -tz "$tz" -o "${name}.html"
done
```

## Running as Python module

```bash
python -m building_shadow visualize [OPTIONS]
python -m building_shadow sources
python -m building_shadow info
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, no buildings found, etc.) |

## Environment variables

The tool respects standard environment variables:

- `HTTP_PROXY` / `HTTPS_PROXY`: For network requests through a proxy
- `NO_PROXY`: Hosts to exclude from proxy

## Troubleshooting

### "No buildings found"

The area may have sparse coverage for the selected source. Try:
1. Increasing `--radius`
2. Using a different `--source` (e.g., `--source overture`)
3. Using a nearby major landmark
4. Checking the source's coverage for your area

### "Could not geocode address"

The address wasn't recognized. Try:
1. Adding city and country
2. Using a well-known landmark nearby
3. Using `--lat` and `--lon` directly

### Slow computation

For large areas with many buildings:
1. Reduce `--radius`
2. Narrow the time range (`--start-hour`, `--end-hour`)
3. Be patient - 1000+ buildings takes time

### Missing shadows at certain hours

The sun may be below the horizon. This happens:
- Very early morning or late evening
- In winter at high latitudes
- The tool silently skips hours when no shadow can be computed

### "DuckDB is required for Overture Maps"

Install the optional DuckDB dependency:
```bash
uv add duckdb
```

### "Location is outside Spain" (Catastro)

The Spanish Cadastre only covers Spain. Use `--source osm` or `--source overture` for other locations.

# Building Shadow Documentation

Building Shadow is a tool that visualizes how buildings cast shadows throughout the day, using real building data from multiple sources and sun position calculations.

## Overview

Given a location (address or coordinates), this tool:

1. **Fetches building footprints** from multiple data sources (OSM, Overture Maps, Spanish Cadastre)
2. **Computes shadows** for each hour using the sun's position
3. **Generates an interactive map** showing shadow patterns

## Use Cases

- **Urban planning**: Understand how new buildings will affect sunlight in public spaces
- **Real estate**: Analyze sunlight exposure for properties
- **Architecture**: Study shadow patterns for building design
- **Solar energy**: Identify areas with consistent sunlight for solar panels
- **Photography**: Plan outdoor shoots based on shadow patterns

## Features

- **Multiple data sources**: OpenStreetMap (worldwide), Overture Maps (ML-generated), Spanish Cadastre (Spain)
- Support for any location worldwide via address or coordinates
- Seasonal sun trajectory (spring, summer, autumn, winter)
- Configurable time range (default 9:00-21:00)
- Interactive HTML visualization with layer controls
- Automatic height extraction from source data

## Documentation Contents

- [Getting Started](getting-started.md) - Installation and quick start guide
- [Data Sources](data-sources.md) - How building data is obtained
- [Shadow Computation](shadow-computation.md) - How shadows are calculated
- [Visualization](visualization.md) - Understanding the output
- [CLI Reference](cli-reference.md) - Command-line options

## Quick Example

```bash
# Visualize shadows around Madrid's Plaza Mayor in summer (using OSM - default)
building-shadow visualize --address "Plaza Mayor, Madrid, Spain" --season summer

# Use Spanish Cadastre for official building data in Spain
building-shadow visualize --address "Plaza Mayor, Madrid" --source catastro

# Use Overture Maps for ML-generated footprints (requires duckdb)
building-shadow visualize --lat 40.4168 --lon -3.7038 --source overture

# List available data sources
building-shadow sources
```

## Technology Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| OSM data | [OSMnx](https://osmnx.readthedocs.io/) | Fetch OpenStreetMap features |
| Overture data | [DuckDB](https://duckdb.org/) | Query Overture Maps GeoParquet |
| Catastro data | [GeoPandas](https://geopandas.org/) | Query Spanish Cadastre WFS |
| Geocoding | [GeoPy](https://geopy.readthedocs.io/) | Convert addresses to coordinates |
| Shadow calculation | [pybdshadow](https://github.com/ni1o1/pybdshadow) | Sun position and shadow geometry |
| Visualization | [Folium](https://python-visualization.github.io/folium/) | Interactive web maps |
| CLI | [Typer](https://typer.tiangolo.com/) | Command-line interface |

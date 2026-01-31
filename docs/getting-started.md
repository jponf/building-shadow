# Getting Started

## Prerequisites

- Python 3.12 or higher
- [mise](https://mise.jdx.dev/) (recommended) or manual Python environment
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

### Using mise (recommended)

```bash
# Clone or navigate to the project
cd building-shadow

# Trust and install the environment
mise trust
mise install

# Install dependencies
uv sync

# Optional: Install DuckDB for Overture Maps support
uv add duckdb
```

### Manual installation

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Quick Start

### Using an address

The simplest way to use the tool is with a street address:

```bash
building-shadow visualize --address "Empire State Building, New York"
```

This will:
1. Geocode the address to coordinates
2. Fetch buildings within 300m (default radius)
3. Compute shadows for summer (default) from 9:00-21:00
4. Save `building_shadows.html` in the current directory

### Using coordinates

For precise control, use latitude and longitude:

```bash
building-shadow visualize --lat 48.8584 --lon 2.2945 --radius 200
```

### Viewing the result

Open the generated `building_shadows.html` in a web browser. You'll see:
- An interactive map centered on your location
- Building footprints in blue
- Shadow layers for each hour (toggle in the layer control)
- A legend showing the time-to-color mapping

## Configuration Options

### Season

The sun's path varies by season. Choose the appropriate one:

```bash
# Summer solstice (June 21) - highest sun, shortest shadows
building-shadow visualize -a "Central Park, NY" --season summer

# Winter solstice (December 21) - lowest sun, longest shadows
building-shadow visualize -a "Central Park, NY" --season winter

# Spring/Autumn equinox - moderate shadows
building-shadow visualize -a "Central Park, NY" --season spring
```

### Time range

Customize the hours to compute:

```bash
# Morning shadows only
building-shadow visualize -a "Location" --start-hour 6 --end-hour 12

# Afternoon shadows
building-shadow visualize -a "Location" --start-hour 12 --end-hour 20
```

### Timezone

Specify the local timezone for accurate sun position:

```bash
# European locations
building-shadow visualize -a "Paris, France" --timezone Europe/Paris

# US locations
building-shadow visualize -a "Los Angeles, CA" --timezone America/Los_Angeles
```

### Search radius

Control how far from the center point to search for buildings:

```bash
# Small area (faster, fewer buildings)
building-shadow visualize -a "Location" --radius 100

# Large area (slower, more buildings)
building-shadow visualize -a "Location" --radius 1000
```

### Data source

Choose where to get building data:

```bash
# OpenStreetMap (default, worldwide)
building-shadow visualize -a "Tokyo, Japan" --source osm

# Overture Maps (ML-enhanced, requires duckdb)
building-shadow visualize -a "San Francisco" --source overture

# Spanish Cadastre (Spain only, official data)
building-shadow visualize -a "Madrid, Spain" --source catastro
```

Check available sources on your system:

```bash
building-shadow sources
```

### Custom buildings

Add user-defined buildings for planning or simulation:

```bash
building-shadow visualize -a "Location" --buildings custom.json
```

Create a JSON file with building definitions:

```json
[
  {
    "shape": "polygon",
    "corners": [[40.4168, -3.7038], [40.4168, -3.7035], [40.4165, -3.7035], [40.4165, -3.7038]],
    "height": 30
  },
  {
    "shape": "cylinder",
    "lat": 40.417,
    "lon": -3.703,
    "radius": 10,
    "height": 25
  }
]
```

Custom buildings are merged with buildings from the selected data source, making it easy to see how a proposed building might affect shadows in an existing area.

## Running as a Python module

You can also run the tool as a Python module:

```bash
python -m building_shadow visualize --address "Your Location"
```

## Next Steps

- Learn about [data sources](data-sources.md) to understand where building data comes from
- Understand [shadow computation](shadow-computation.md) for technical details
- See the full [CLI reference](cli-reference.md) for all options

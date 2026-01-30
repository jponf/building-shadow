# Shadow Computation

This document explains how Building Shadow calculates shadows using sun position and building geometry.

## Overview

Shadow computation involves two main steps:

1. **Calculate sun position** for the given time and location
2. **Project building footprints** based on sun angle and building height

## Sun Position

The sun's position in the sky is described by two angles:

### Solar Altitude (Elevation)

The angle between the sun and the horizon:
- 0° = sun at horizon (sunrise/sunset)
- 90° = sun directly overhead (only possible near equator)

Higher altitude → shorter shadows

### Solar Azimuth

The compass direction of the sun:
- 0° / 360° = North
- 90° = East
- 180° = South
- 270° = West

Azimuth determines shadow direction (opposite to sun direction).

## pybdshadow Library

The tool uses [pybdshadow](https://github.com/ni1o1/pybdshadow) for shadow calculations. This library:

1. Uses [suncalc-py](https://github.com/kylebarron/suncalc-py) for sun position
2. Computes shadow geometry using vector projection
3. Returns shadow polygons as a GeoDataFrame

### Function signature

```python
import pybdshadow

shadows = pybdshadow.bdshadow_sunlight(
    buildings,  # GeoDataFrame with geometry and height columns
    date,       # UTC datetime for sun position
)
```

### Required columns

The buildings GeoDataFrame must have:
- `geometry`: Polygon or MultiPolygon footprint
- `height`: Building height in meters
- `building_id`: Unique identifier for each building

## Shadow geometry

For each building, pybdshadow:

1. **Calculates sun vector** from altitude and azimuth
2. **Projects each vertex** of the building footprint along the shadow direction
3. **Creates shadow polygon** from original footprint to projected vertices
4. **Handles self-intersection** and overlapping shadows

### Shadow length formula

```
shadow_length = building_height / tan(solar_altitude)
```

Example at 45° altitude with 20m building:
```
shadow_length = 20 / tan(45°) = 20 / 1 = 20 meters
```

Example at 30° altitude with 20m building:
```
shadow_length = 20 / tan(30°) = 20 / 0.577 ≈ 34.6 meters
```

## Seasonal variation

The sun's path varies dramatically by season and latitude:

### Summer (June 21 - Northern Hemisphere)
- Highest sun altitude
- Longest day
- Shortest shadows
- Sun rises in northeast, sets in northwest

### Winter (December 21 - Northern Hemisphere)
- Lowest sun altitude
- Shortest day
- Longest shadows
- Sun rises in southeast, sets in southwest

### Equinoxes (March 21, September 21)
- Sun rises due east, sets due west
- Day and night approximately equal
- Moderate shadows

## Representative dates

The tool uses solstice/equinox dates to represent each season:

| Season | Date | Significance |
|--------|------|--------------|
| Spring | March 21 | Vernal equinox |
| Summer | June 21 | Summer solstice |
| Autumn | September 21 | Autumnal equinox |
| Winter | December 21 | Winter solstice |

## Timezone handling

Sun position depends on:
- **Local time** at the location (what hour the user specifies)
- **UTC time** for astronomical calculations

The tool:
1. Takes user input in local timezone (e.g., `Europe/Madrid`)
2. Converts to UTC for pybdshadow
3. Computes sun position for that UTC instant

### Example

User requests shadow at 12:00 in Madrid (UTC+2 in summer):
```
Local: 2024-06-21 12:00 Europe/Madrid
UTC:   2024-06-21 10:00 UTC
```

pybdshadow calculates sun position for 10:00 UTC at Madrid's coordinates.

## Computation performance

Shadow calculation time depends on:
- **Number of buildings**: Linear scaling
- **Number of hours**: Linear scaling
- **Building complexity**: More vertices = slower

Typical performance:
- 100 buildings × 13 hours ≈ 5 seconds
- 500 buildings × 13 hours ≈ 20 seconds
- 1000 buildings × 13 hours ≈ 45 seconds

## Limitations

### No terrain modeling
The tool assumes flat terrain. Hills, valleys, and slopes are not considered.

### No vegetation
Trees and other vegetation that might cast shadows are not included.

### Simplified building models
Buildings are extruded footprints (flat roofs). Complex roof shapes are not modeled.

### No atmospheric effects
Shadows are computed as if the sun is a point source with no atmosphere scattering.

## Advanced usage

### Accessing raw shadow data

For programmatic use, import the core functions:

```python
from building_shadow import fetch_buildings, compute_shadows
from building_shadow.core import Season

# Fetch buildings
buildings = fetch_buildings(
    latitude=40.4168,
    longitude=-3.7038,
    radius_meters=300
)

# Compute shadows for each hour
shadows_by_hour = compute_shadows(
    buildings=buildings,
    season=Season.SUMMER,
    start_hour=9,
    end_hour=18,
    timezone="Europe/Madrid"
)

# shadows_by_hour is a dict: {hour: GeoDataFrame}
for hour, shadow_gdf in shadows_by_hour.items():
    print(f"{hour}:00 - {len(shadow_gdf)} shadow polygons")
```

### Custom visualization

You can use the shadow data with any GIS tool:

```python
# Export to GeoJSON
shadows_by_hour[12].to_file("noon_shadows.geojson", driver="GeoJSON")

# Export to Shapefile
shadows_by_hour[12].to_file("noon_shadows.shp")
```

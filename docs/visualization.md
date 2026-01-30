# Visualization

Building Shadow generates interactive HTML maps using [Folium](https://python-visualization.github.io/folium/). This document explains the visualization features and how to interpret the output.

## Output file

The tool generates a single HTML file (default: `building_shadows.html`) that:
- Works in any modern web browser
- Requires no server or installation
- Can be shared as a standalone file
- Includes all data embedded inline

## Map components

### Base map

The visualization uses **CartoDB Positron** tiles - a light, minimalist basemap that:
- Provides geographic context without distraction
- Makes building and shadow colors stand out
- Loads quickly and works worldwide

### Buildings layer

Buildings are displayed as blue polygons:
- **Fill color**: `#3388ff` (bright blue)
- **Border**: `#0055aa` (darker blue), 2px weight
- **Opacity**: 60%

Hover over a building to see its height in the tooltip.

### Shadow layers

Each hour has its own shadow layer with a unique color:

| Time | Color | Description |
|------|-------|-------------|
| Morning (9:00) | Yellow/Orange | `#ffc864` |
| Midday (12:00-14:00) | Orange/Brown | `#d4a050` |
| Afternoon (15:00-18:00) | Brown/Purple | `#a07850` |
| Evening (19:00-21:00) | Dark blue | `#6050ff` |

The color gradient helps distinguish different times at a glance.

### Layer control

The layer control panel (top-right corner) allows you to:
- Toggle individual hour layers on/off
- Show/hide the buildings layer
- Compare shadows at different times

By default, only the midday shadow layer is visible. Check/uncheck layers to explore different hours.

### Legend

The legend (bottom-left corner) shows:
- Color-to-time mapping for all computed hours
- Instructions to use the layer control

## Interpreting shadows

### Shadow direction

Shadows point **away** from the sun:
- Morning: Shadows point west
- Noon: Shadows point north (in Northern Hemisphere)
- Afternoon: Shadows point east

### Shadow length

Longer shadows indicate:
- Lower sun (early morning, late evening)
- Winter season
- Taller buildings

### Overlapping shadows

Dark areas where multiple shadows overlap indicate:
- Consistently shaded areas throughout the day
- Potential issues for solar panels or gardens
- Good locations for shade-seeking activities

## Interactive features

### Pan and zoom

- **Mouse drag**: Pan the map
- **Scroll wheel**: Zoom in/out
- **Double-click**: Zoom in
- **Shift + drag**: Zoom to selection rectangle

### Layer toggling

Click checkboxes in the layer control to:
- Compare specific hours
- See cumulative shadow coverage
- Identify areas that are always sunny/shady

### Tooltips

Hover over buildings to see:
- Building height (from data source or default value)

## Customizing the output

### Output path

Specify a custom output filename:

```bash
building-shadow visualize -a "Location" -o my_shadows.html
```

### Opening automatically

The tool doesn't automatically open the browser. Use your OS command:

```bash
# macOS
open building_shadows.html

# Linux
xdg-open building_shadows.html

# Windows
start building_shadows.html
```

## Technical details

### File size

The HTML file size depends on:
- Number of buildings (geometry complexity)
- Number of hours computed
- Shadow complexity

Typical sizes:
- 100 buildings, 13 hours: ~500 KB
- 500 buildings, 13 hours: ~2 MB
- 1000 buildings, 13 hours: ~5 MB

### Browser compatibility

The visualization works in:
- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

### Mobile support

The map is touch-friendly:
- Pinch to zoom
- Swipe to pan
- Tap layer control to expand

## Alternative visualizations

For advanced analysis, export the data and use specialized GIS tools:

### QGIS

```python
# Export shadows for use in QGIS
from building_shadow.core import compute_shadow_animation_data

shadows = compute_shadow_animation_data(buildings, season, 9, 21, "UTC")
shadows.to_file("shadows.gpkg", driver="GPKG")
```

### Kepler.gl

The project includes keplergl as a dependency. For time-animated 3D visualization:

```python
from keplergl import KeplerGl

map = KeplerGl(height=600)
map.add_data(data=buildings, name="buildings")
map.add_data(data=shadows, name="shadows")
map.save_to_html(file_name="kepler_shadows.html")
```

### Matplotlib

For static publication-quality images:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 10))
buildings.plot(ax=ax, color="blue", alpha=0.6)
shadows_noon.plot(ax=ax, color="gray", alpha=0.4)
plt.savefig("shadows.png", dpi=300)
```

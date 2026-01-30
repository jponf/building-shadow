"""Visualization module for building shadows."""

from typing import Any

import geopandas as gpd


def save_visualization_html(
    buildings: gpd.GeoDataFrame,
    shadows: gpd.GeoDataFrame,
    center_lat: float,
    center_lon: float,
    output_path: str = "building_shadows.html",
) -> str:
    """Create and save an interactive visualization to an HTML file.

    Uses folium to create a clean interactive map with layer controls
    for each hour's shadows.

    Args:
        buildings: GeoDataFrame with building geometries.
        shadows: GeoDataFrame with shadow geometries and hour column.
        center_lat: Center latitude for map view.
        center_lon: Center longitude for map view.
        output_path: Path to save the HTML file.

    Returns:
        Path to the saved HTML file.
    """
    import folium  # noqa: PLC0415

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles="CartoDB positron",
    )

    _add_buildings_layer(m, buildings)
    _add_shadow_layers(m, shadows)

    folium.LayerControl(collapsed=False).add_to(m)

    hours = sorted(shadows["hour"].unique())
    colors = _get_shadow_color_gradient(len(hours))
    legend_html = _create_legend_html(list(hours), colors)
    m.get_root().html.add_child(folium.Element(legend_html))  # type: ignore[attr-defined]

    m.save(output_path)
    return output_path


def _add_buildings_layer(m: Any, buildings: gpd.GeoDataFrame) -> None:  # noqa: ANN401
    """Add buildings layer to the map.

    Args:
        m: Folium map object.
        buildings: GeoDataFrame with building geometries.
    """
    import folium  # noqa: PLC0415

    building_style = {
        "fillColor": "#3388ff",
        "color": "#0055aa",
        "weight": 2,
        "fillOpacity": 0.6,
    }

    buildings_layer = folium.GeoJson(
        buildings,
        name="Buildings",
        style_function=lambda _: building_style,
        tooltip=folium.GeoJsonTooltip(fields=["height"], aliases=["Height (m):"]),
    )
    buildings_layer.add_to(m)


def _add_shadow_layers(m: Any, shadows: gpd.GeoDataFrame) -> None:  # noqa: ANN401
    """Add shadow layers for each hour to the map.

    Args:
        m: Folium map object.
        shadows: GeoDataFrame with shadow geometries and hour column.
    """
    import folium  # noqa: PLC0415

    hours = sorted(shadows["hour"].unique())
    shadow_colors = _get_shadow_color_gradient(len(hours))
    midday_hour = hours[len(hours) // 2] if hours else None

    for i, hour in enumerate(hours):
        hour_shadows = shadows[shadows["hour"] == hour][["geometry", "hour"]].copy()
        shadow_style = {
            "fillColor": shadow_colors[i],
            "color": "#333333",
            "weight": 1,
            "fillOpacity": 0.5,
        }
        shadow_layer = folium.GeoJson(
            hour_shadows,
            name=f"Shadows {hour:02d}:00",
            style_function=lambda _, style=shadow_style: style,
            show=(hour == midday_hour),
        )
        shadow_layer.add_to(m)


def _get_shadow_color_gradient(n_hours: int) -> list[str]:
    """Generate a color gradient from yellow (morning) to dark blue (evening).

    Args:
        n_hours: Number of hours to generate colors for.

    Returns:
        List of hex color strings.
    """
    colors = []
    for i in range(n_hours):
        ratio = i / max(n_hours - 1, 1)
        r = int(255 * (1 - ratio * 0.7))
        g = int(200 * (1 - ratio * 0.6))
        b = int(100 + 155 * ratio)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors


def _create_legend_html(hours: list[int], colors: list[str]) -> str:
    """Create HTML for the shadow time legend.

    Args:
        hours: List of hours.
        colors: List of corresponding colors.

    Returns:
        HTML string for the legend.
    """
    legend_items = "".join(
        f'<div style="display:flex;align-items:center;margin:2px 0;">'
        f'<span style="background:{colors[i]};width:20px;height:12px;'
        f'margin-right:5px;border:1px solid #333;"></span>'
        f"<span>{hour:02d}:00</span></div>"
        for i, hour in enumerate(hours)
    )

    return f"""
    <div style="position:fixed;bottom:50px;left:50px;z-index:1000;
                background:white;padding:10px;border-radius:5px;
                box-shadow:0 2px 6px rgba(0,0,0,0.3);font-family:Arial,sans-serif;
                font-size:12px;">
        <div style="font-weight:bold;margin-bottom:5px;">Shadow Times</div>
        {legend_items}
        <div style="margin-top:8px;font-size:10px;color:#666;">
            Toggle layers in control panel →
        </div>
    </div>
    """

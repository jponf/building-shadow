"""Command-line interface for building shadow visualization."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer

from building_shadow.core import (
    compute_shadow_animation_data,
    fetch_buildings,
    get_coordinates_from_address,
)
from building_shadow.models import (
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_RADIUS_METERS,
    DataSource,
)
from building_shadow.visualization import save_visualization_html


app = typer.Typer(
    name="building-shadow",
    help="Visualize building shadows using multiple data sources.",
)


@app.command()
def visualize(  # noqa: PLR0913, PLR0912, PLR0915
    address: Annotated[
        str | None,
        typer.Option(
            "--address",
            "-a",
            help="Street address to center the visualization on.",
        ),
    ] = None,
    latitude: Annotated[
        float | None,
        typer.Option(
            "--latitude",
            "--lat",
            help="Latitude coordinate.",
        ),
    ] = None,
    longitude: Annotated[
        float | None,
        typer.Option(
            "--longitude",
            "--lon",
            help="Longitude coordinate.",
        ),
    ] = None,
    radius: Annotated[
        float,
        typer.Option(
            "--radius",
            "-r",
            help="Radius in meters around the location to fetch buildings.",
        ),
    ] = DEFAULT_RADIUS_METERS,
    source: Annotated[
        DataSource,
        typer.Option(
            "--source",
            "-src",
            help="Data source for building footprints.",
            case_sensitive=False,
        ),
    ] = DataSource.OSM,
    target_date: Annotated[
        str | None,
        typer.Option(
            "--date",
            "-d",
            help="Date for sun position (YYYY-MM-DD format, defaults to today).",
        ),
    ] = None,
    start_hour: Annotated[
        int,
        typer.Option(
            "--start-hour",
            help="Start hour for shadow computation (0-23).",
            min=0,
            max=23,
        ),
    ] = 9,
    end_hour: Annotated[
        int,
        typer.Option(
            "--end-hour",
            help="End hour for shadow computation (0-23).",
            min=0,
            max=23,
        ),
    ] = 21,
    timezone: Annotated[
        str,
        typer.Option(
            "--timezone",
            "-tz",
            help="Local timezone (e.g., Europe/Madrid, America/New_York).",
        ),
    ] = "Europe/Madrid",
    default_height: Annotated[
        float,
        typer.Option(
            "--default-height",
            help="Default building height in meters when not available.",
        ),
    ] = DEFAULT_BUILDING_HEIGHT,
    buildings_file: Annotated[
        Path | None,
        typer.Option(
            "--buildings",
            "-b",
            help="JSON file with custom building definitions to add.",
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output HTML file path.",
        ),
    ] = Path("building_shadows.html"),
) -> None:
    """Generate building shadow visualization for a given location.

    You must provide either an address OR latitude/longitude coordinates.

    Data sources:
        osm      - OpenStreetMap (default, worldwide)
        overture - Overture Maps (requires duckdb)
        catastro - Spanish Cadastre (Spain only)

    Custom buildings:
        Use --buildings to add user-defined buildings from a JSON file.
        Custom buildings are merged with data from the selected source.

    Examples:
        building-shadow visualize --address "Plaza Mayor, Madrid, Spain"
        building-shadow visualize --lat 40.4168 --lon -3.7038 --date 2024-12-21
        building-shadow visualize -a "Madrid" --source catastro
        building-shadow visualize --lat 40.4168 --lon -3.7038 -b custom.json
    """
    if address is None and (latitude is None or longitude is None):
        typer.echo(
            "Error: Provide --address or both --latitude and --longitude",
            err=True,
        )
        raise typer.Exit(code=1)

    if address is not None and (latitude is not None or longitude is not None):
        typer.echo(
            "Error: Provide either --address or --latitude/--longitude, not both",
            err=True,
        )
        raise typer.Exit(code=1)

    if start_hour >= end_hour:
        typer.echo("Error: --start-hour must be less than --end-hour", err=True)
        raise typer.Exit(code=1)

    if address is not None:
        typer.echo(f"Geocoding address: {address}")
        try:
            lat, lon = get_coordinates_from_address(address)
            typer.echo(f"Found coordinates: ({lat:.6f}, {lon:.6f})")
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from e
    else:
        lat = latitude  # type: ignore[assignment]
        lon = longitude  # type: ignore[assignment]
        typer.echo(f"Using coordinates: ({lat:.6f}, {lon:.6f})")

    typer.echo(f"Fetching buildings from {source.value} within {radius}m radius...")
    try:
        buildings = fetch_buildings(
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            default_height=default_height,
            source=source,
        )
        typer.echo(f"Found {len(buildings)} buildings from {source.value}")
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ConnectionError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e

    # Merge custom buildings if provided
    if buildings_file is not None:
        typer.echo(f"Loading custom buildings from {buildings_file}...")
        try:
            import geopandas as gpd  # noqa: PLC0415
            import pandas as pd  # noqa: PLC0415

            from building_shadow.custom_buildings import (  # noqa: PLC0415
                load_custom_buildings,
            )

            custom_gdf = load_custom_buildings(buildings_file)
            typer.echo(f"Loaded {len(custom_gdf)} custom buildings")

            # Merge with existing buildings
            buildings = gpd.GeoDataFrame(
                pd.concat([buildings, custom_gdf], ignore_index=True),
                crs="EPSG:4326",
            )
            buildings["building_id"] = range(len(buildings))
            typer.echo(f"Total buildings after merge: {len(buildings)}")
        except FileNotFoundError:
            typer.echo(f"Error: Buildings file not found: {buildings_file}", err=True)
            raise typer.Exit(code=1) from None
        except ValueError as e:
            typer.echo(f"Error parsing custom buildings: {e}", err=True)
            raise typer.Exit(code=1) from e

    # Parse the target date
    parsed_date: date | None = None
    if target_date is not None:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            typer.echo(
                "Error: Invalid date format. Use YYYY-MM-DD (e.g., 2024-06-21).",
                err=True,
            )
            raise typer.Exit(code=1) from None

    date_display = parsed_date.isoformat() if parsed_date else "today"
    typer.echo(f"Computing shadows ({date_display}, {start_hour}:00-{end_hour}:00)...")
    try:
        shadows = compute_shadow_animation_data(
            buildings=buildings,
            target_date=parsed_date,
            start_hour=start_hour,
            end_hour=end_hour,
            timezone=timezone,
        )
        typer.echo(f"Computed shadows for {len(shadows)} time points")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e

    typer.echo("Generating visualization...")
    output_path = save_visualization_html(
        buildings=buildings,
        shadows=shadows,
        center_lat=lat,
        center_lon=lon,
        output_path=str(output),
    )

    typer.echo(f"Visualization saved to: {output_path}")
    typer.echo("Open the HTML file in a web browser to view the interactive map.")


@app.command()
def sources() -> None:
    """List available data sources and their status."""
    from building_shadow.sources import get_available_sources  # noqa: PLC0415

    typer.echo("Available data sources:")
    typer.echo("")

    all_sources = [
        (DataSource.OSM, "OpenStreetMap", "Worldwide, community-maintained"),
        (DataSource.OVERTURE, "Overture Maps", "ML-generated footprints (duckdb)"),
        (DataSource.CATASTRO, "Spanish Cadastre", "Official Spanish building data"),
    ]

    available = get_available_sources()

    for src, name, desc in all_sources:
        status = "✓" if src in available else "✗"
        typer.echo(f"  {status} {src.value:10} - {name}")
        typer.echo(f"              {desc}")
        typer.echo("")


@app.command()
def info() -> None:
    """Display information about the building-shadow tool."""
    from building_shadow import __version__  # noqa: PLC0415

    typer.echo(f"building-shadow v{__version__}")
    typer.echo("")
    typer.echo("A tool to visualize building shadows using multiple data sources.")
    typer.echo("")
    typer.echo("Features:")
    typer.echo("  - Multiple data sources (OSM, Overture Maps, Spanish Cadastre)")
    typer.echo("  - Compute shadows using pybdshadow (sun position based)")
    typer.echo("  - Interactive visualization with Folium")
    typer.echo("  - Support for any specific date and time range")
    typer.echo("")
    typer.echo("Run 'building-shadow sources' to see available data sources.")
    typer.echo("Run 'building-shadow visualize --help' for usage details.")


if __name__ == "__main__":
    app()

from typing import Optional
import typer
from rich.console import Console
from raster2sensor import config
from raster2sensor import __app_name__, __version__
from raster2sensor.logging import configure_logging
from raster2sensor.utils import clear
from raster2sensor.plots import Plots
from raster2sensor.ogcapiprocesses import OGCAPIProcesses

app = typer.Typer()
console = Console()
ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)

configure_logging(
    level="DEBUG",
    log_dir="./logs",
    enable_file_logging=True,
    enable_console_logging=True,
    use_rich=True,  # Use rich formatting if available
    suppress_third_party_debug=True  # Suppress third-party debug logs
)

# Main


def _version_callback(value: bool) -> None:
    clear()
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return


# OGC Processes
@app.command()
def get_ogc_processes():
    """
    Fetch OGC Processes.
    """
    clear()
    ogc_api_processes.get_processes()


@app.command()
def describe_ogc_process(process_id: str):
    """
    Describe OGC Process.
    Args:
        process_id (str): Process ID
    """
    clear()
    ogc_api_processes.describe_process(process_id)


# Raster Images Processing
@app.command()
def create_plots():
    # TODO: Complete the create_plots() function
    """
    Create plots in SensorThingsAPI.
    """
    clear()
    console.print('[cyan]Creating SensorThingsAPI Things Entities...')


@app.command()
def fetch_plots(trial_id: str):
    """
    Fetch plots GeoJSON for a given trial ID.
    Args:
        trial_id (str): Trial ID
    """
    clear()
    Plots.fetch_plots_geojson(trial_id)
    # typer.echo(parcels_geojson)
    # console.print(plots_geojson)


if __name__ == "__main__":
    app()

from typing import Optional
import typer
from rich.console import Console
from uavstats import config
from uavstats import __app_name__, __version__
from uavstats.utils import clear, timeit
from uavstats.plots import Plots
from uavstats.ogcapiprocesses import OGCAPIProcesses

app = typer.Typer()
console = Console()
ogc_api_processes = OGCAPIProcesses(config.PYGEOAPI_URL)


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
def fetch_ogc_processes():
    """
    Fetch OGC Processes.
    """
    clear()
    ogc_api_processes.fetch_processes()


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
def create_parcels():
    # TODO: Complete the create_parcels() function
    """
    Create parcels in SensorThingsAPI.
    """
    clear()
    console.print('[cyan]Creating SensorThingsAPI Things Entities...')


@app.command()
def fetch_parcels(project_id: str):
    """
    Fetch parcels GeoJSON for a given project ID.
    Args:
        project_id (str): Project ID
    """
    clear()
    plots_geojson = Plots.fetch_parcels_geojson(project_id)
    # typer.echo(parcels_geojson)
    console.print(plots_geojson)

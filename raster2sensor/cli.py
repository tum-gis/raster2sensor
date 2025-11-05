import typer
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from raster2sensor import config
from raster2sensor import __app_name__, __version__
from raster2sensor.logging import configure_logging, get_logger
from raster2sensor.utils import clear
from raster2sensor.plots import Plots
from raster2sensor.ogcapiprocesses import OGCAPIProcesses
from raster2sensor.sensorthingsapi import Datastream

# Logger
logger = get_logger(__name__)
configure_logging(
    level="DEBUG",
    log_dir="./logs",
    enable_file_logging=True,
    enable_console_logging=True,
    use_rich=True,  # Use rich formatting if available
    suppress_third_party_debug=True  # Suppress third-party debug logs
)
# Main app
app = typer.Typer()
console = Console()

# Sub-command groups
plots_app = typer.Typer()
processes_app = typer.Typer()

# Add sub-command groups to main app
app.add_typer(plots_app, name="plots",
              help="Trial plots management in OGC SensorThings API commands")
app.add_typer(processes_app, name="processes",
              help="OGC API - Processes commands")

# Initialize OGC API Processes
ogc_api_processes = OGCAPIProcesses(
    config.PYGEOAPI_URL or "http://localhost:5000")


# Main callback


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
    """
    Raster2Sensor - A tool for raster data processing and OGC SensorThings API integration.
    """
    return


# =============================================================================
# PLOTS COMMANDS
# =============================================================================

@plots_app.command("fetch")
def fetch_plots(trial_id: str):
    """
    Fetch plots GeoJSON for a given trial ID.

    Args:
        trial_id: The trial identifier to fetch plots for
    """
    clear()
    logger.info(f"Fetching plots for trial ID: {trial_id}")
    Plots.fetch_plots_geojson(trial_id)


@plots_app.command("create")
def create_plots(
    file_path: str = typer.Option(..., help="Path to plots GeoJSON/Shapefile"),
    trial_id: str = typer.Option(...,
                                 help="Trial identifier (e.g., 'Goetheweg-2024')"),
    plot_id_field: str = typer.Option(...,
                                      help="Field name containing plot IDs"),
    treatment_id_field: str = typer.Option(
        "", help="Field name containing treatment IDs (optional)"),
    year: int = typer.Option(
        None, help="Year of the trial (defaults to current year)")
):
    """
    Create plots in SensorThingsAPI.

    This command creates SensorThings API Things entities for each plot in the provided
    GeoJSON or Shapefile, along with their associated Locations and Datastreams.
    """
    clear()
    logger.info("Creating SensorThingsAPI Things Entities...")

    try:
        # Use current year if not provided
        if year is None:
            year = datetime.now().year

        # Create Plots instance
        plots = Plots(
            file_path=Path(file_path),
            trial_id=trial_id,
            plot_id_field=plot_id_field,
            treatment_id_field=treatment_id_field,
            year=year
        )

        # Create SensorThings API Things
        plots.create_sensorthings_things()

        logger.info(
            f"[green]Successfully created SensorThings API entities for trial: {trial_id}[/green]")

    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        raise typer.Exit(1)
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Error creating plots: {e}")
        raise typer.Exit(1)

# TODO: Provide a template example for defining datastream objects


@plots_app.command("add-datastreams")
def add_datastreams(
    trial_id: str = typer.Option(...,
                                 help="Trial identifier to add datastreams to"),
    datastreams_file: str = typer.Option(
        ..., help="Path to JSON file containing additional datastreams")
):
    """
    Add datastreams to existing plots.

    This command adds additional datastreams to existing SensorThings API Things
    for the specified trial. Provide a custom JSON file with a list of datastream definitions.
    """
    clear()
    logger.info(f"Adding datastreams for trial ID: {trial_id}")

    try:
        # Determine which datastreams to use
        if datastreams_file:
            # Load datastreams from JSON file
            logger.info(f"Loading datastreams from file: {datastreams_file}")

            if not Path(datastreams_file).exists():
                console.print(
                    f"[red]Error: Datastreams file not found: {datastreams_file}[/red]")
                raise typer.Exit(1)

            with open(datastreams_file, 'r') as f:
                datastreams_data = json.load(f)

            # Convert JSON data to Datastream objects
            datastreams = [Datastream(**ds) for ds in datastreams_data]
            console.print(
                f"[cyan]Loaded {len(datastreams)} datastreams from {datastreams_file}[/cyan]")
        else:
            # Use the default datastreams from config
            datastreams = config.DATASTREAMS
            console.print(
                f"[cyan]Using {len(datastreams)} default datastreams from config[/cyan]")

        # Call the static method directly
        Plots.add_datastreams(trial_id, datastreams)

        console.print(
            f"[green]Successfully added datastreams for trial: {trial_id}[/green]")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON file: {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]File not found: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error adding datastreams: {e}[/red]")
        logger.error(f"Error adding datastreams for trial {trial_id}: {e}")
        raise typer.Exit(1)


# =============================================================================
# PROCESSES COMMANDS
# =============================================================================

@processes_app.command("fetch")
def fetch_processes():
    """
    Fetch available OGC API Processes.
    """
    clear()
    ogc_api_processes.get_processes()


@processes_app.command("describe")
def describe_process(process_id: str):
    """
    Describe a specific OGC API Process.

    Args:
        process_id (str) : The ID of the process to describe
    """
    clear()
    ogc_api_processes.describe_process(process_id)


@processes_app.command("execute")
def execute_process(
    process_id: str,
    input_file: Optional[str] = typer.Option(None, help="Input file path"),
    output_file: Optional[str] = typer.Option(None, help="Output file path"),
    sync: bool = typer.Option(True, help="Execute synchronously")
):
    """
    Execute a specific OGC API Process.

    Args:
        process_id: The ID of the process to execute
        input_file: Path to input file (optional)
        output_file: Path to output file (optional)
        sync: Whether to execute synchronously (default: True)
    """
    clear()
    console.print(f"[cyan]Executing process: {process_id}[/cyan]")

    if input_file:
        console.print(f"[dim]Input file: {input_file}[/dim]")
    if output_file:
        console.print(f"[dim]Output file: {output_file}[/dim]")

    execution_mode = "synchronous" if sync else "asynchronous"
    console.print(f"[dim]Execution mode: {execution_mode}[/dim]")

    # TODO: Implement process execution functionality
    console.print(
        '[yellow]Note: execute_process() function needs implementation[/yellow]')


if __name__ == "__main__":
    app()

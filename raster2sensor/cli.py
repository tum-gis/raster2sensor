import typer
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
from raster2sensor.config_parser import load_datastreams_from_config, ConfigParser
from raster2sensor.image_processor import ImageProcessor

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
    trial_id: str = typer.Option(None,
                                 help="Trial identifier (e.g., 'MyTrial-2025'). Can be overridden if using unified config."),
    plot_id_field: str = typer.Option(None,
                                      help="Field name containing plot IDs. Can be overridden if using unified config."),
    treatment_id_field: str = typer.Option(
        "", help="Field name containing treatment IDs (optional)"),
    year: int = typer.Option(
        None, help="Year of the trial (defaults to current year). Can be overridden if using unified config."),
    datastreams_config: str = typer.Option(
        None, help="Path to YAML/JSON file containing datastream configurations"),
    config: str = typer.Option(
        None, help="Path to unified configuration file (YAML/JSON) containing datastreams, trial metadata, etc.")
):
    """
    Create plots in SensorThingsAPI.

    This command creates SensorThings API Things entities for each plot in the provided
    GeoJSON or Shapefile, along with their associated Locations and Datastreams.

    You can provide either:
    - A datastreams configuration file (--datastreams-config) with explicit parameters
    - A unified configuration file (--config) that contains all parameters including datastreams
    
    If using unified config, parameters from the config file will be used unless explicitly overridden.
    """
    clear()
    logger.info("Creating SensorThingsAPI Things Entities...")

    try:
        # Determine which configuration approach to use
        if config and datastreams_config:
            logger.error("Cannot specify both --config and --datastreams-config. Choose one.")
            raise typer.Exit(1)
        
        if not config and not datastreams_config:
            logger.error("Must specify either --config or --datastreams-config")
            raise typer.Exit(1)
        
        if config:
            # Load from unified configuration
            logger.info(f"Loading unified configuration from: {config}")
            unified_config = ConfigParser.load_config(config)
            
            # Use config values or CLI overrides
            effective_trial_id = trial_id or unified_config.trial_id
            effective_plot_id_field = plot_id_field or unified_config.plot_id_field
            effective_year = year or unified_config.year or datetime.now().year
            
            if not effective_trial_id:
                logger.error("trial_id must be specified in config file or via --trial-id parameter")
                raise typer.Exit(1)
            if not effective_plot_id_field:
                logger.error("plot_id_field must be specified in config file or via --plot-id-field parameter")
                raise typer.Exit(1)
            
            # Load datastreams from unified config
            datastreams = load_datastreams_from_config(config)
            logger.debug(f"Loaded {len(datastreams)} datastreams from unified config")
            
        else:
            # Load from separate datastreams config (legacy approach)
            if not trial_id or not plot_id_field:
                logger.error("trial_id and plot_id_field are required when using --datastreams-config")
                raise typer.Exit(1)
            
            effective_trial_id = trial_id
            effective_plot_id_field = plot_id_field
            effective_year = year or datetime.now().year
            
            logger.info(f"Loading datastreams from config file: {datastreams_config}")
            datastreams = load_datastreams_from_config(datastreams_config)
            logger.debug(f"Loaded {len(datastreams)} datastreams from {datastreams_config}")

        logger.info(f"Using trial_id: {effective_trial_id}, plot_id_field: {effective_plot_id_field}, year: {effective_year}")

        # Create Plots instance with datastreams
        plots = Plots(
            file_path=Path(file_path),
            trial_id=effective_trial_id,
            plot_id_field=effective_plot_id_field,
            treatment_id_field=treatment_id_field,
            year=effective_year,
            datastreams=datastreams
        )        # Create SensorThings API Things
        plots.create_sensorthings_things()

        logger.info(
            f"Successfully created SensorThings API entities for trial: {trial_id}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error creating plots: {e}")
        raise typer.Exit(1)


@plots_app.command("add-datastreams")
def add_datastreams(
    trial_id: str = typer.Option(...,
                                 help="Trial identifier to add datastreams to"),
    datastreams_file: str = typer.Option(
        ..., help="Path to YAML/JSON file containing datastream configurations")
):
    """
    Add datastreams to existing plots (SensorThings API Things).

    This command adds additional datastreams to existing SensorThings API Things
    for the specified trial. You must provide a YAML/JSON file with datastream definitions.
    """
    clear()
    logger.info(f"Adding datastreams for trial ID: {trial_id}")

    try:
        # Load datastreams from config file
        logger.info(f"Loading datastreams from file: {datastreams_file}")
        datastreams = load_datastreams_from_config(datastreams_file)
        logger.info(
            f"Loaded {len(datastreams)} datastreams from {datastreams_file}")

        # Call the static method directly
        Plots.add_datastreams(trial_id, datastreams)

        logger.info(f"Successfully added datastreams for trial: {trial_id}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error adding datastreams for trial {trial_id}: {e}")
        raise typer.Exit(1)


@plots_app.command("generate-config")
def generate_config(
    output_path: str = typer.Option(...,
                                    help="Path to save the sample configuration file"),
    format_type: str = typer.Option(
        "yaml", help="Configuration format: 'yaml' or 'json'")
):
    """
    Generate a sample datastreams configuration file.

    This command creates a sample YAML or JSON configuration file that can be used
    as a template for defining custom datastreams for the create and add-datastreams commands.
    """
    clear()
    logger.info(f"Generating sample configuration file: {output_path}")

    from raster2sensor.config_parser import DatastreamConfigParser

    try:
        if format_type.lower() not in ['yaml', 'json']:
            console.print(
                "[red]Error: format_type must be 'yaml' or 'json'[/red]")
            raise typer.Exit(1)

        DatastreamConfigParser.create_sample_config(
            output_path, format_type.lower())
        console.print(
            f"[green]Sample configuration file created: {output_path}[/green]")
        console.print(
            "[cyan]You can now edit this file and use it with the --datastreams-config option[/cyan]")

    except Exception as e:
        console.print(f"[red]Error generating configuration file: {e}[/red]")
        logger.error(f"Error generating config file {output_path}: {e}")
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


@app.command("process-images")
def process_images(
    config_file: str = typer.Option(
        ..., 
        "--config", 
        help="Path to unified configuration file (YAML or JSON) containing datastreams, raster images, and vegetation indices"
    ),
    trial_id: Optional[str] = typer.Option(
        None, 
        "--trial-id", 
        help="Override trial ID from config file"
    ),
    indices: Optional[str] = typer.Option(
        None, 
        "--indices", 
        help="Comma-separated list of vegetation indices to process (e.g., 'ndvi,ndre'). If not specified, processes all indices from config."
    ),
    images: Optional[str] = typer.Option(
        None, 
        "--images", 
        help="Comma-separated list of image paths to process. If not specified, processes all images from config."
    ),
    dry_run: bool = typer.Option(
        False, 
        "--dry-run", 
        help="Show what would be processed without actually executing"
    )
):
    """
    Process raster images to calculate vegetation indices and create observations.
    
    This command replicates the functionality from the demo module, allowing you to:
    - Process multiple raster images with multiple vegetation indices
    - Calculate zonal statistics for trial plots
    - Create observations in the SensorThings API
    
    The configuration file should contain:
    - datastreams: SensorThings API datastream definitions
    - raster_images: List of raster files with timestamps
    - vegetation_indices: List of processes with band configurations
    - trial_id, plot_id_field, year: Trial metadata
    """
    clear()
    console.print(f"[cyan]Processing raster images with vegetation indices[/cyan]")
    
    try:
        # Load unified configuration
        logger.info(f"Loading configuration from: {config_file}")
        unified_config = ConfigParser.load_config(config_file)
        console.print(f"[green]✓[/green] Configuration loaded successfully")
        
        # Override trial_id if provided
        if trial_id:
            unified_config.trial_id = trial_id
            logger.info(f"Override trial_id: {trial_id}")
        
        if not unified_config.trial_id:
            logger.error("trial_id must be specified in config file or via --trial-id parameter")
            raise typer.Exit(1)
        
        # Filter vegetation indices if specified
        if indices:
            requested_indices = [idx.strip() for idx in indices.split(',')]
            filtered_indices = [
                vi for vi in unified_config.vegetation_indices 
                if vi.process in requested_indices
            ]
            if not filtered_indices:
                logger.error(f"No matching vegetation indices found for: {requested_indices}")
                raise typer.Exit(1)
            unified_config.vegetation_indices = filtered_indices
            logger.info(f"Filtering to indices: {[vi.process for vi in filtered_indices]}")
        
        # Filter raster images if specified
        if images:
            requested_images = [img.strip() for img in images.split(',')]
            filtered_images = [
                img for img in unified_config.raster_images 
                if any(req_img in img.path for req_img in requested_images)
            ]
            if not filtered_images:
                logger.error(f"No matching raster images found for: {requested_images}")
                raise typer.Exit(1)
            unified_config.raster_images = filtered_images
            logger.info(f"Filtering to {len(filtered_images)} raster images")
        
        # Display processing plan
        console.print(f"\n[bold]Processing Plan:[/bold]")
        console.print(f"Trial ID: [cyan]{unified_config.trial_id}[/cyan]")
        console.print(f"Raster Images: [yellow]{len(unified_config.raster_images)}[/yellow]")
        console.print(f"Vegetation Indices: [yellow]{len(unified_config.vegetation_indices)}[/yellow]")
        console.print(f"Total Processes: [yellow]{len(unified_config.raster_images) * len(unified_config.vegetation_indices)}[/yellow]")
        
        if dry_run:
            console.print(f"\n[yellow]DRY RUN - Showing what would be processed:[/yellow]")
            
            console.print(f"\n[bold]Raster Images:[/bold]")
            for img in unified_config.raster_images:
                console.print(f"  • {img.path} ({img.timestamp})")
            
            console.print(f"\n[bold]Vegetation Indices:[/bold]")
            for vi in unified_config.vegetation_indices:
                bands_str = ", ".join([f"{k}={v}" for k, v in vi.bands.items()])
                console.print(f"  • {vi.name} ({vi.process}) - Bands: {bands_str}")
            
            console.print(f"\n[yellow]Use --no-dry-run to execute the processing[/yellow]")
            return
        
        # Confirm processing
        if not typer.confirm("\nProceed with processing?"):
            console.print("[yellow]Processing cancelled[/yellow]")
            raise typer.Exit(0)
        
        # Create processor and execute
        logger.info("Initializing image processor")
        processor = ImageProcessor()
        
        # Process images
        logger.info("Starting image processing")
        results = processor.process_from_config(unified_config)
        
        # Print summary
        console.print(f"\n[bold]Processing completed![/bold]")
        ImageProcessor.print_results_summary(results)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        console.print(f"[red]Configuration file not found: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        console.print(f"[red]Error processing images: {e}[/red]")
        raise typer.Exit(1)


@app.command("create-sample-config")
def create_sample_config(
    output_path: str = typer.Option(
        "config.yml", 
        "--output", 
        help="Output path for the sample configuration file"
    ),
    format: str = typer.Option(
        "yaml", 
        "--format", 
        help="Configuration format: 'yaml' or 'json'"
    )
):
    """
    Create a sample unified configuration file with datastreams, raster images, and vegetation indices.
    
    This creates a comprehensive configuration file that can be used with the process-images command.
    """
    clear()
    console.print(f"[cyan]Creating sample unified configuration file[/cyan]")
    
    try:
        ConfigParser.create_sample_config(output_path, format)
        console.print(f"[green]✓[/green] Sample configuration created: [cyan]{output_path}[/cyan]")
        console.print(f"\nYou can now edit this file and use it with:")
        console.print(f"[dim]python -m raster2sensor process-images --config {output_path}[/dim]")
        
    except Exception as e:
        logger.error(f"Error creating sample configuration: {e}")
        console.print(f"[red]Error creating sample configuration: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

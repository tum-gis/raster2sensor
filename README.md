# raster2sensor: FAIRagro UC6 UAV Images Processing Tool

## Installation

### 🚀 **Quick Installation**

The installation process is now platform-specific for the best user experience:

#### **Linux/macOS (Automatic):**

```bash
# One command - GDAL and GeoPandas included automatically!
pip install raster2sensor
```

#### **Windows (Manual Prerequisites):**

```bash
# Step 1: Install geospatial dependencies first
conda install -c conda-forge gdal geopandas

# Step 2: Install raster2sensor
pip install raster2sensor
```

> **Why different approaches?** GDAL installation via pip works reliably on Linux/macOS but can be problematic on Windows due to binary compatibility issues. This approach gives you the smoothest experience on each platform.

### Alternative Installation Methods

#### 🥇 **Method 1: Conda (Works on all platforms)**

```bash
# Create environment with geospatial packages
conda create -n raster2sensor -c conda-forge python=3.11 gdal geopandas
conda activate raster2sensor

# Install raster2sensor 
pip install raster2sensor
```

#### 🥈 **Method 2: System packages (Linux/macOS)**

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get install gdal-bin libgdal-dev
pip install raster2sensor  # GDAL included automatically
```

**macOS (Homebrew):**

```bash
brew install gdal
pip install raster2sensor  # GDAL included automatically
```

**Windows (conda-forge wheels):**

```bash
pip install --find-links https://girder.github.io/large_image_wheels GDAL
pip install geopandas raster2sensor
```

### Development Installation

For development with all optional dependencies:

```bash
git clone https://github.com/FAIRagro/raster2sensor.git
cd raster2sensor
pip install -e .[dev,full]
```

### Verify Installation

Test your installation:

```bash
raster2sensor --version
python -c "import geopandas, rasterio; print('✅ Geospatial dependencies OK')"
```


## Usage

`raster2sensor` - A tool for raster data processing and OGC SensorThings API integration.

```console
raster2sensor [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `-v, --version`: Show the application&#x27;s version and exit.
- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `process-images`: Process raster images to calculate...
- `create-sample-config`: Create a sample configuration file with...
- `plots`: Trial plots management in OGC SensorThings...
- `processes`: OGC API - Processes commands

## `raster2sensor process-images`

Process raster images to calculate vegetation indices and create SensorThingsAPI observations.

This command allows you to:

- Process multiple raster images with multiple vegetation indices
- Calculate zonal statistics for trial plots
- Create observations in the SensorThings API

The configuration file should contain:

- datastreams: SensorThings API datastream definitions
- raster_images: List of raster files with timestamps
- vegetation_indices: List of processes with band configurations
- Trial metadata: trial_id, plot_id_field, year
- sensorthingsapi_url: SensorThings API URL
- pygeoapi_url: PyGeoAPI URL

**Usage**:

```console
raster2sensor process-images [OPTIONS]
```

**Options**:

- `--config TEXT`: Path to unified configuration file (YAML or JSON) containing datastreams, raster images, and vegetation indices [required]
- `--trial-id TEXT`: Override trial ID from config file
- `--indices TEXT`: Comma-separated list of vegetation indices to process (e.g., &#x27;ndvi,ndre&#x27;). If not specified, processes all indices from config.
- `--images TEXT`: Comma-separated list of image paths to process. If not specified, processes all images from config.
- `--dry-run`: Show what would be processed without actually executing
- `--help`: Show this message and exit.

## `raster2sensor create-sample-config`

Create a sample configuration file with all parameters required to run raster2sensor tool.

This creates a comprehensive configuration file, which includes trial metadata, datastreams, raster images, and vegetation indices.

**Usage**:

```console
raster2sensor create-sample-config [OPTIONS]
```

**Options**:

- `--output TEXT`: Output path for the sample configuration file [default: config.yml]
- `--format TEXT`: Configuration format: &#x27;yaml&#x27; or &#x27;json&#x27; [default: yaml]
- `--help`: Show this message and exit.

## `raster2sensor plots`

Trial plots management in OGC SensorThings API commands

**Usage**:

```console
raster2sensor plots [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `fetch`: Fetch plots GeoJSON for a given trial ID.
- `create`: Create plots as Things in SensorThingsAPI.
- `add-datastreams`: Add datastreams to existing plots...

### `raster2sensor plots fetch`

Fetch plots GeoJSON for a given trial ID.

You can provide either:

- Individual parameters: --trial-id and --sensorthingsapi-url
- Configuration file: --config (containing sensorthingsapi_url and trial_id)

Args:
trial_id: The trial identifier to fetch plots for
sensorthingsapi_url: SensorThings API URL
config_file: Path to configuration file

**Usage**:

```console
raster2sensor plots fetch [OPTIONS]
```

**Options**:

- `--trial-id TEXT`: Trial identifier to fetch plots for
- `--sensorthingsapi-url TEXT`: SensorThingsAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing sensorthingsapi_url and trial_id
- `--help`: Show this message and exit.

### `raster2sensor plots create`

Create plots as Things in SensorThingsAPI.

This command creates SensorThings API Things entities for each plot in the provided
GeoJSON or Shapefile, along with the specified parameters.

You can provide either:

- A unified configuration file (--config) that contains all parameters
- Individual parameters

Parameters from the config file will be used unless explicitly overridden via command line options.

**Usage**:

```console
raster2sensor plots create [OPTIONS]
```

**Options**:

- `--file-path TEXT`: Path to plots GeoJSON/Shapefile [required]
- `--config TEXT`: Path to unified configuration file (YAML/JSON) containing datastreams, trial metadata, etc. [required]
- `--sensorthingsapi-url TEXT`: Override SensorThingsAPI URL from config
- `--trial-id TEXT`: Override trial identifier from config
- `--plot-id-field TEXT`: Override field name containing plot IDs from config
- `--treatment-id-field TEXT`: Field name containing treatment IDs (optional)
- `--year INTEGER`: Override year from config (defaults to current year)
- `--help`: Show this message and exit.

### `raster2sensor plots add-datastreams`

Add datastreams to existing plots (SensorThings API Things).

This command adds additional datastreams to existing SensorThings API Things
for the specified trial. You must provide a configuration file with datastream definitions.

**Usage**:

```console
raster2sensor plots add-datastreams [OPTIONS]
```

**Options**:

- `--trial-id TEXT`: Trial identifier to add datastreams to [required]
- `--config TEXT`: Path to configuration file (YAML/JSON) containing datastream configurations and sensorthingsapi_url [required]
- `--sensorthingsapi-url TEXT`: Override SensorThingsAPI URL from config
- `--help`: Show this message and exit.

## `raster2sensor processes`

OGC API - Processes commands

**Usage**:

```console
raster2sensor processes [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `fetch`: Fetch available OGC API Processes.
- `describe`: Describe a specific OGC API Process.
- `execute`: Execute a specific OGC API Process.

### `raster2sensor processes fetch`

Fetch available OGC API Processes.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

**Usage**:

```console
raster2sensor processes fetch [OPTIONS]
```

**Options**:

- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--help`: Show this message and exit.

### `raster2sensor processes describe`

Describe a specific OGC API Process.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

Args:
process_id: The ID of the process to describe
pygeoapi_url: PyGeoAPI URL
config_file: Path to configuration file

**Usage**:

```console
raster2sensor processes describe [OPTIONS]
```

**Options**:

- `--process-id TEXT`: The ID of the process to describe [required]
- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--help`: Show this message and exit.

### `raster2sensor processes execute`

Execute a specific OGC API Process.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

Args:
process_id: The ID of the process to execute
pygeoapi_url: PyGeoAPI URL
config_file: Path to configuration file
input_file: Path to input file (optional)
output_file: Path to output file (optional)
sync: Whether to execute synchronously (default: True)

**Usage**:

```console
raster2sensor processes execute [OPTIONS]
```

**Options**:

- `--process-id TEXT`: The ID of the process to execute [required]
- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--input-file TEXT`: Input file path
- `--output-file TEXT`: Output file path
- `--sync / --no-sync`: Execute synchronously [default: sync]
- `--help`: Show this message and exit.

````

```k# `raster2sensor`

Raster2Sensor - A tool for raster data processing and OGC SensorThings API integration.

**Usage**:

```console
$ raster2sensor [OPTIONS] COMMAND [ARGS]...
````

**Options**:

- `-v, --version`: Show the application&#x27;s version and exit.
- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `process-images`: Process raster images to calculate...
- `create-sample-config`: Create a sample configuration file with...
- `plots`: Trial plots management in OGC SensorThings...
- `processes`: OGC API - Processes commands

## `raster2sensor process-images`

Process raster images to calculate vegetation indices and create SensorThingsAPI observations.

This command allows you to:

- Process multiple raster images with multiple vegetation indices
- Calculate zonal statistics for trial plots
- Create observations in the SensorThings API

The configuration file should contain:

- datastreams: SensorThings API datastream definitions
- raster_images: List of raster files with timestamps
- vegetation_indices: List of processes with band configurations
- Trial metadata: trial_id, plot_id_field, year
- sensorthingsapi_url: SensorThings API URL
- pygeoapi_url: PyGeoAPI URL

**Usage**:

```console
raster2sensor process-images [OPTIONS]
```

**Options**:

- `--config TEXT`: Path to unified configuration file (YAML or JSON) containing datastreams, raster images, and vegetation indices [required]
- `--trial-id TEXT`: Override trial ID from config file
- `--indices TEXT`: Comma-separated list of vegetation indices to process (e.g., &#x27;ndvi,ndre&#x27;). If not specified, processes all indices from config.
- `--images TEXT`: Comma-separated list of image paths to process. If not specified, processes all images from config.
- `--dry-run`: Show what would be processed without actually executing
- `--help`: Show this message and exit.

## `raster2sensor create-sample-config`

Create a sample configuration file with all parameters required to run raster2sensor tool.

This creates a comprehensive configuration file, which includes trial metadata, datastreams, raster images, and vegetation indices.

**Usage**:

```console
raster2sensor create-sample-config [OPTIONS]
```

**Options**:

- `--output TEXT`: Output path for the sample configuration file [default: config.yml]
- `--format TEXT`: Configuration format: &#x27;yaml&#x27; or &#x27;json&#x27; [default: yaml]
- `--help`: Show this message and exit.

## `raster2sensor plots`

Trial plots management in OGC SensorThings API commands

**Usage**:

```console
raster2sensor plots [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `fetch`: Fetch plots GeoJSON for a given trial ID.
- `create`: Create plots as Things in SensorThingsAPI.
- `add-datastreams`: Add datastreams to existing plots...

### `raster2sensor plots fetch`

Fetch plots GeoJSON for a given trial ID.

You can provide either:

- Individual parameters: --trial-id and --sensorthingsapi-url
- Configuration file: --config (containing sensorthingsapi_url and trial_id)

Args:
trial_id: The trial identifier to fetch plots for
sensorthingsapi_url: SensorThings API URL
config_file: Path to configuration file

**Usage**:

```console
raster2sensor plots fetch [OPTIONS]
```

**Options**:

- `--trial-id TEXT`: Trial identifier to fetch plots for
- `--sensorthingsapi-url TEXT`: SensorThingsAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing sensorthingsapi_url and trial_id
- `--help`: Show this message and exit.

### `raster2sensor plots create`

Create plots as Things in SensorThingsAPI.

This command creates SensorThings API Things entities for each plot in the provided
GeoJSON or Shapefile, along with the specified parameters.

You can provide either:

- A unified configuration file (--config) that contains all parameters
- Individual parameters

Parameters from the config file will be used unless explicitly overridden via command line options.

**Usage**:

```console
raster2sensor plots create [OPTIONS]
```

**Options**:

- `--file-path TEXT`: Path to plots GeoJSON/Shapefile [required]
- `--config TEXT`: Path to unified configuration file (YAML/JSON) containing datastreams, trial metadata, etc. [required]
- `--sensorthingsapi-url TEXT`: Override SensorThingsAPI URL from config
- `--trial-id TEXT`: Override trial identifier from config
- `--plot-id-field TEXT`: Override field name containing plot IDs from config
- `--treatment-id-field TEXT`: Field name containing treatment IDs (optional)
- `--year INTEGER`: Override year from config (defaults to current year)
- `--help`: Show this message and exit.

### `raster2sensor plots add-datastreams`

Add datastreams to existing plots (SensorThings API Things).

This command adds additional datastreams to existing SensorThings API Things
for the specified trial. You must provide a configuration file with datastream definitions.

**Usage**:

```console
raster2sensor plots add-datastreams [OPTIONS]
```

**Options**:

- `--trial-id TEXT`: Trial identifier to add datastreams to [required]
- `--config TEXT`: Path to configuration file (YAML/JSON) containing datastream configurations and sensorthingsapi_url [required]
- `--sensorthingsapi-url TEXT`: Override SensorThingsAPI URL from config
- `--help`: Show this message and exit.

## `raster2sensor processes`

OGC API - Processes commands

**Usage**:

```console
raster2sensor processes [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `fetch`: Fetch available OGC API Processes.
- `describe`: Describe a specific OGC API Process.
- `execute`: Execute a specific OGC API Process.

### `raster2sensor processes fetch`

Fetch available OGC API Processes.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

**Usage**:

```console
raster2sensor processes fetch [OPTIONS]
```

**Options**:

- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--help`: Show this message and exit.

### `raster2sensor processes describe`

Describe a specific OGC API Process.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

Args:
process_id: The ID of the process to describe
pygeoapi_url: PyGeoAPI URL
config_file: Path to configuration file

**Usage**:

```console
raster2sensor processes describe [OPTIONS]
```

**Options**:

- `--process-id TEXT`: The ID of the process to describe [required]
- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--help`: Show this message and exit.

### `raster2sensor processes execute`

Execute a specific OGC API Process.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

Args:
process_id: The ID of the process to execute
pygeoapi_url: PyGeoAPI URL
config_file: Path to configuration file
inputs: Dictionary of input parameters for the process
sync: Whether to execute synchronously (default: True)

Returns:
    Result of the process execution

**Usage**:

```console
raster2sensor processes execute [OPTIONS]
```

**Options**:

- `--process-id TEXT`: The ID of the process to execute [required]
- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--inputs TEXT`: Dictionary of input parameters for the process
- `--sync / --no-sync`: Execute synchronously [default: sync]
- `--help`: Show this message and exit.

# raster2sensor: FAIRagro UC6 UAV Images Processing Tool

## Introduction

The `raster2sensor` Python package manages agricultural trial plots and processes vegetation indices extracted from UAV images as sensor data based on the OGC SensorThings API standard. It implements the functionalities illustrated in the workflow diagram.
![UAV images processing workflow](/docs/uav_images_processing.png)
*UAV images processing workflow*

## Installation

GDAL must be installed at the system level before installing this Python package.

---

### **Windows**

#### 1. Install GDAL

Install GDAL using using OSGeo4W (recommended)

- Download the OSGeo4W Network Installer.

- Select **Command Line Tools → gdal** and install.

#### 2. Add GDAL to PATH

```powershell
setx GDAL_DATA "C:\Program Files\GDAL\gdal-data"
setx PATH "%PATH%;C:\Program Files\GDAL"
```

#### 3. Install the Python GDAL bindings

Replace `<gdal_version>` with your installed version:

```bash
pip install GDAL==<gdal_version>
```

#### 4. Install this package

``` bash
pip install .
```

---

### **macOS**

#### 1. Install GDAL (Homebrew recommended)

```bash
brew install gdal
```

#### 2. Install the Python GDAL bindings

```bash
pip install GDAL==$(gdal-config --version)
```

#### 3. Install this package

```bash
pip install .
```

---

### **Linux (Ubuntu / Debian)**

#### 1. Install system GDAL libraries

```bash
sudo apt update
sudo apt install gdal-bin libgdal-dev
```

#### 2. Install Python GDAL bindings

```bash
pip install GDAL==$(gdal-config --version)
```

#### 3. Install the package

```bash
pip install .
```

---

### Alternative Installation (Conda)

If you prefer a fully precompiled environment:

```bash
conda create -n myenv python=3.11
conda activate myenv

conda install -c conda-forge gdal
conda install -c conda-forge rasterio fiona geopandas  # if your package depends on these

pip install .
```

---

### Docker

If you prefer not to install GDAL and the geospatial stack locally, a Docker image is provided that bundles everything (GDAL via conda-forge, all Python dependencies, and the `raster2sensor` CLI).

#### 1. Build the image

```bash
git clone https://github.com/tum-gis/raster2sensor.git
cd raster2sensor
docker build -t raster2sensor:latest .
```

#### 2. Run CLI commands

Mount the directory that contains your config files and raster data as `/data` inside the container. `raster2sensor` will then be able to read paths relative to `/data`.

**Show help:**

```bash
docker run --rm raster2sensor:latest --help
```

**Fetch available OGC API Processes:**

```bash
docker run --rm raster2sensor:latest processes fetch \
  --pygeoapi-url https://<your-pygeoapi-host>/pygeoapi
```

**Fetch plots from SensorThings API:**

```bash
docker run --rm raster2sensor:latest plots fetch \
  --trial-id <trial-id> \
  --sensorthingsapi-url https://<your-frost-host>/frost/v1.1
```

**Create plots from a GeoJSON file** (config and data files are in `./my-data/` on the host):

```bash
docker run --rm \
  -v "$(pwd)/my-data:/data" \
  raster2sensor:latest plots create \
  --config /data/config.yml \
  --file-path /data/plots.geojson
```

**Process raster images** (dry-run):

```bash
docker run --rm \
  -v "$(pwd)/my-data:/data" \
  raster2sensor:latest process-images \
  --config /data/config.yml \
  --dry-run
```

> **Note – Windows paths**: Use `` `pwd` `` (PowerShell) or `%cd%` (CMD) instead of `$(pwd)`:
> ```powershell
> docker run --rm -v "${PWD}\my-data:/data" raster2sensor:latest process-images --config /data/config.yml
> ```

---

### Development Installation

For development with all optional dependencies:

```bash
git clone https://github.com/tum-gis/raster2sensor.git
cd raster2sensor
pip install -e .[dev,full]
```

---

### Verify Installation

Test your installation:

```bash
raster2sensor --version
python -c "import geopandas, rasterio; print('✅ Geospatial dependencies OK')"
```

---

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

### `raster2sensor process-images`

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

### `raster2sensor create-sample-config`

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

### `raster2sensor plots`

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

#### `raster2sensor plots fetch`

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

#### `raster2sensor plots create`

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

#### `raster2sensor plots add-datastreams`

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

### `raster2sensor processes`

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

#### `raster2sensor processes fetch`

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

#### `raster2sensor processes describe`

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

#### `raster2sensor processes execute`

Execute a specific OGC API Process.

You can provide either:

- Individual parameter: --pygeoapi-url
- Configuration file: --config (containing pygeoapi_url)

Args:
process_id: The ID of the process to execute (required)
pygeoapi_url: PyGeoAPI URL
config_file: Path to configuration file
inputs: JSON string of inputs (optional)
sync: Whether to execute synchronously (default: True)

**Usage**:

```console
raster2sensor processes execute [OPTIONS]
```

**Options**:

- `--process-id TEXT`: The ID of the process to execute [required]
- `--pygeoapi-url TEXT`: PyGeoAPI URL
- `--config TEXT`: Path to configuration file (YAML or JSON) containing pygeoapi_url
- `--inputs STRING`: JSON String of input parameters for the process
- `--sync / --no-sync`: Execute synchronously [default: sync]
- `--help`: Show this message and exit.

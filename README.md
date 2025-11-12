# UAV Raster Images Statistics Manager

FAIRagro UAV Images Processing

## Installation

### Windows Installation (Recommended: Conda)

GDAL and geopandas can be challenging to install on Windows via pip. We recommend using conda:

#### Option 1: Conda Installation (Recommended)

```bash
# Use the provided installation script
install-windows-conda.bat
```

Or manually:

```bash
# Create and activate environment
conda create -n raster2sensor python=3.11 -y
conda activate raster2sensor

# Install geospatial dependencies
conda install -c conda-forge gdal geopandas -y

# Install the package
pip install -e .
```

#### Option 2: Pip Installation (Advanced Users)

```bash
# Use the provided installation script
install-windows-pip.bat
```

Or manually:

```bash
# Try installing GDAL from pre-compiled wheels
pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ GDAL
pip install -r requirements-windows.txt
pip install -e .
```

### Linux/macOS Installation

```bash
pip install -e .
```

## Usage

### Processing Raster Images

```bash
raster2sensor process-images --config config.yml
```

### Managing Plots

```bash
# Fetch existing plots
raster2sensor plots fetch --config config.yml

# Create new plots
raster2sensor plots create --config config.yml
```

### OGC API Processes

```bash
# Fetch available processes
raster2sensor processes fetch --url https://your-pygeoapi-url/processes

# Describe a specific process
raster2sensor processes describe --process-id your-process --config config.yml
```

## Configuration

Create a sample configuration file:

```bash
raster2sensor create-sample-config
```

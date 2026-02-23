# Raster2Sensor Docker Image
# Uses Miniconda base for reliable GDAL / geospatial dependency installation

FROM continuumio/miniconda3:latest

LABEL maintainer="joseph.gitahi@tum.de" \
    description="raster2sensor – raster imagery processing and OGC SensorThings API integration" \
    version="1.0.0"

# ── System dependencies ────────────────────────────────────────────────────────
# (libgl1 is required by some matplotlib / OpenCV backends)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── Geospatial stack via conda-forge ──────────────────────────────────────────
# Installing GDAL, geopandas and shapely through conda-forge is the most
# reliable cross-platform approach and avoids binary wheel issues.
RUN conda install -y -c conda-forge \
    gdal \
    geopandas \
    shapely \
    && conda clean -afy

WORKDIR /app

# ── Python application dependencies via pip ───────────────────────────────────
# GDAL / geopandas / shapely are already installed above; exclude them here
# to prevent pip from overwriting the conda-provided binaries.
RUN pip install --no-cache-dir \
    requests>=2.25.0 \
    "typer[all]>=0.9.0" \
    rich>=13.0.0 \
    matplotlib>=3.5.0 \
    PyYAML>=6.0 \
    python-dotenv>=0.19.0

# ── Install the raster2sensor package ─────────────────────────────────────────
COPY setup.py .
COPY raster2sensor/ ./raster2sensor/

# --no-deps avoids pip re-resolving / overwriting conda-managed packages
RUN pip install --no-cache-dir --no-deps .

# ── Runtime configuration ─────────────────────────────────────────────────────
# Mount point for config files and raster data
VOLUME ["/data"]

# Default working directory when the container is used with bind-mounts
WORKDIR /data

ENTRYPOINT ["raster2sensor"]
CMD ["--help"]

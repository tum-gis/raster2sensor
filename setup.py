# -*- coding: utf-8 -*-
from setuptools import setup
import sys
import os


def show_gdal_installation_help():
    """Display helpful GDAL installation instructions for Windows users."""
    print("\n" + "="*70)
    print("🗺️  WINDOWS: GEOSPATIAL DEPENDENCIES REQUIRED")
    print("="*70)
    print("On Windows, GDAL and GeoPandas must be installed separately due to pip compatibility issues.")
    print("(Linux/macOS users get these dependencies automatically via pip!)\n")

    if sys.platform == 'win32':
        print("Windows Installation (choose one method):\n")
        print("🥇 CONDA (Recommended - most reliable):")
        print("   conda install -c conda-forge gdal geopandas")
        print("   pip install raster2sensor\n")
        print("🥈 PIP with conda-forge wheels:")
        print(
            "   pip install --find-links https://girder.github.io/large_image_wheels GDAL")
        print("   pip install geopandas raster2sensor\n")
        print("🥉 OSGeo4W (advanced users):")
        print("   Install OSGeo4W: https://trac.osgeo.org/osgeo4w/")
        print("   Set GDAL_DATA environment variable")
        print("   pip install geopandas raster2sensor")
    else:
        print("Linux/macOS Installation:\n")
        print("📦 System packages (Ubuntu/Debian):")
        print("   sudo apt-get install gdal-bin libgdal-dev")
        print("   pip install geopandas raster2sensor\n")
        print("🍺 Homebrew (macOS):")
        print("   brew install gdal")
        print("   pip install geopandas raster2sensor\n")
        print("🐍 Conda (all platforms):")
        print("   conda install -c conda-forge gdal geopandas")
        print("   pip install raster2sensor")

    print("\n💡 More help: https://geopandas.org/en/stable/getting_started/install.html")
    print("🔧 Use 'check-gdal' command after installation to verify setup")
    print("="*70 + "\n")


# Core requirements - these install reliably via pip on all platforms
install_requirements = [
    'requests>=2.25.0',
    'typer[all]>=0.9.0',
    'rich>=13.0.0',
    'matplotlib>=3.5.0',
    'PyYAML>=6.0',
    'python-dotenv>=0.19.0',
    'shapely>=2.0.0',
]

# Platform-specific geospatial dependencies
# GDAL pip installation works fine on Linux/macOS but is problematic on Windows
if sys.platform != 'win32':
    # Linux/macOS: Include geospatial dependencies for smooth installation
    install_requirements.extend([
        'GDAL>=3.5.0',
        'geopandas>=1.0.0',
    ])
    print("📍 Linux/macOS detected: Including GDAL and GeoPandas in pip installation")

# Check if we're in a conda environment (safer for geospatial packages)
is_conda = any([
    'CONDA_DEFAULT_ENV' in os.environ,
    'CONDA_PREFIX' in os.environ,
    'MAMBA_ROOT_PREFIX' in os.environ,
])

# Check if GDAL is already available
gdal_available = False
try:
    import importlib.util
    gdal_specs = [
        importlib.util.find_spec("gdal"),
        importlib.util.find_spec("osgeo.gdal"),
        importlib.util.find_spec("osgeo")
    ]
    gdal_available = any(spec is not None for spec in gdal_specs)
except ImportError:
    pass

# Windows: Follow Rasterio's approach (GDAL pip issues)
# Linux/macOS: Include GDAL in pip for smooth experience
if sys.platform == 'win32' and not gdal_available and not is_conda:
    show_gdal_installation_help()
    print("\n⚠️  Note: On Windows, GDAL and GeoPandas must be installed separately.")
    print("After installing them, run: pip install raster2sensor\n")
elif sys.platform != 'win32':
    print("✅ Linux/macOS: GDAL and GeoPandas will be installed automatically via pip")

setup(
    name='raster2sensor',
    version='1.0.0',
    description='A tool for processing raster images for integration as sensor data.',
    author='Joseph Gitahi',
    author_email='joseph.gitahi@tum.de',
    license='MIT',
    packages=['raster2sensor'],
    install_requires=install_requirements,
    extras_require={
        'test': [
            'pytest>=6.0.0',
            'pytest-cov>=3.0.0',
            'pytest-mock>=3.6.0',
        ],
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
            'isort>=5.10.0',
        ],
        'docs': [
            'sphinx>=4.0.0',
            'sphinx-rtd-theme>=1.0.0',
            'myst-parser>=0.17.0',
        ]
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    entry_points={
        'console_scripts': [
            'raster2sensor=raster2sensor.cli:app',
            'check-gdal=check_gdal:main',
        ],
    },
)

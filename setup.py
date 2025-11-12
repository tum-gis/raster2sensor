from setuptools import setup
import sys
import os

# Base requirements that work on all platforms
base_requirements = [
    'requests',
    'typer',
    'rich',
    'matplotlib',
    'PyYAML',
    'python-dotenv',
    'shapely>=2.1.1',
]

# Platform-specific or problematic requirements
# GDAL and geopandas should be installed separately on Windows
optional_requirements = [
    'geopandas>=1.1.1',
]

# Only add GDAL if not on Windows or if conda environment is detected
install_requirements = base_requirements.copy()

# # Check if we're in a conda environment (safer for GDAL)
# is_conda = 'CONDA_DEFAULT_ENV' in os.environ or 'CONDA_PREFIX' in os.environ

# if sys.platform != 'win32' or is_conda:
#     # Add GDAL and geopandas if not on Windows or in conda environment
#     install_requirements.extend([
#         'GDAL>=3.11.0',
#         'geopandas>=1.1.1',
#     ])
# else:
#     # On Windows without conda, print installation instructions
#     print("\n" + "="*60)
#     print("WINDOWS INSTALLATION NOTE:")
#     print("GDAL and geopandas require special handling on Windows.")
#     print("Please install them using one of these methods:")
#     print("\n1. Using conda (recommended):")
#     print("   conda install -c conda-forge gdal geopandas")
#     print("\n2. Using pip with pre-compiled wheels:")
#     print("   pip install GDAL --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/")
#     print("   pip install geopandas")
#     print("\n3. Install OSGeo4W and set GDAL_DATA environment variable")
#     print("="*60 + "\n")

setup(
    name='raster2sensor',
    version='0.1.0',
    description='A tool for processing raster images for integration as sensor data.',
    author='Joseph Gitahi',
    author_email='joseph.gitahi@tum.de',
    license='MIT',
    packages=['raster2sensor'],
    install_requires=install_requirements,
    extras_require={
        'full': [
            # 'GDAL>=3.11.0',
            'geopandas>=1.1.1',
        ],
        'dev': [
            'pytest',
            'pytest-cov',
            'black',
            'flake8',
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
        ],
    },
)

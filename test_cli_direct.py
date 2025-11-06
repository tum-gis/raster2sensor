#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

# Test calling the CLI function directly
from raster2sensor.cli import process_images

try:
    print("Testing process_images function directly...")
    
    # Call the function directly with parameters
    process_images(
        config_file='config.yml',
        trial_id=None,
        indices=None, 
        images=None,
        dry_run=True
    )
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
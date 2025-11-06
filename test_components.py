#!/usr/bin/env python3

import sys
import traceback

try:
    print("Testing CLI imports...")
    
    from raster2sensor.config_parser import ConfigParser
    print("✓ UnifiedConfigParser imported")
    
    from raster2sensor.image_processor import ImageProcessor  
    print("✓ ImageProcessor imported")
    
    print("\nTesting config loading...")
    config = ConfigParser.load_config('config.yml')
    print(f"✓ Config loaded: trial_id={config.trial_id}")
    print(f"  Images: {len(config.raster_images)}")
    print(f"  Indices: {len(config.vegetation_indices)}")
    
    print("\nTesting ImageProcessor creation...")
    processor = ImageProcessor()
    print("✓ ImageProcessor created")
    
    print("\nAll components work individually!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
# Utilities
import os
import time
from functools import wraps
from rich import print
from pprint import pprint


def clear():
    '''Clears Console'''
    os.system('cls' if os.name == 'nt' else 'clear')


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(
            f'[blue]{func.__name__} took {end - start:.6f} seconds to complete')
        return result
    return wrapper


def get_file_name(file_path: str):
    return os.path.splitext(os.path.basename(file_path))[0]


def get_files(input_dir: str, extensions: list):
    '''Returns a list of files with the specified extensions in the input directory'''
    files = []
    for file in os.listdir(input_dir):
        if file.endswith(tuple(extensions)):
            files.append(os.path.join(input_dir, file))
    return files

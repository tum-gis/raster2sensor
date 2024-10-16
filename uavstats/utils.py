# Utilities
import os
import sys
import time
import requests
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


def get_file_extension(file_path: str):
    return os.path.splitext(file_path)[1]


def get_files(input_dir: str, extensions: list):
    '''Returns a list of files with the specified extensions in the input directory'''
    files = []
    for file in os.listdir(input_dir):
        if file.endswith(tuple(extensions)):
            files.append(os.path.join(input_dir, file))
    return files


def fetch_data(url):
    """Fetch data from an API

    Args:
        url (_type_): API URL
    Returns:
        response (_type_): API response
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[red]An error occurred: {e}")
        sys.exit(1)
    return response.json()


def fetch_sensorthingsapi(url):
    """Fetch SensorThings Paginated API endpoint

    Args:
        url (_type_): API URL

    Returns:
        json (_type_): JSON data
    """

    data = fetch_data(url)
    fetched_entities = data['value']

    while data.get('@iot.nextLink'):
        data = fetch_data(data['@iot.nextLink'])
        fetched_entities.extend(data['value'])

    return fetched_entities


def create_sensorthingsapi_thing(url: str, thing: dict):
    """Create a SensorThingsAPI Thing

    Args:
        url (_type_): API URL
        thing (_type_): Thing data

    Returns:
        response (_type_): API response
    """
    try:
        response = requests.post(url, json=thing)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[red]An error occurred: {e}")
        sys.exit(1)
    return response.json()

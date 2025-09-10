# Utilities
import os
import sys
import time
import requests
import json
from functools import wraps
from rich import print
import xml.etree.ElementTree as ET
from pathlib import Path


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


def get_file_name(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_extension(file_path: Path) -> str:
    return file_path.suffix


def get_files(input_dir: str, extensions: list) -> list:
    '''Returns a list of files with the specified extensions in the input directory'''
    files = []
    for file in os.listdir(input_dir):
        if file.endswith(tuple(extensions)):
            files.append(os.path.join(input_dir, file))
    return files


def fetch_data(url) -> dict:
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
        print(f"[red]An error occurred while fetching data: {e}")
        sys.exit(1)
    return response.json()


def fetch_sensorthingsapi(url) -> list:
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


def create_sensorthingsapi_entity(url: str, entity: dict) -> requests.Response:
    """Create a SensorThingsAPI Entity

    Args:
        url (string): API URL
        entity (dict): Entity data

    Returns:
        response.status_code (int): API response status code
    """
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    response = None
    try:
        response = requests.post(
            url=url, data=json.dumps(entity), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(
            f"[red]An error occurred while posting to the SensorThings API: {e}")
        if response is not None:
            try:
                print(response.json())
            except Exception:
                print(response.text)
        sys.exit(1)
    return response


def pretty_xml(xml_string: str) -> str:
    '''Pretty print XML from a String'''
    element = ET.fromstring(xml_string)
    ET.indent(element, level=2)
    print(ET.tostring(element, encoding='unicode'))
    return ET.tostring(element, encoding='unicode')

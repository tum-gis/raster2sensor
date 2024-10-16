import os
import sys
from rich import print
import requests
import base64
import json
import config
from utils import clear, timeit, get_file_name, get_files


def get_capabilities():
    get_capabilities = requests.get(config.WPS_GET_CAPABILITIES_URL)
    print(get_capabilities.text)


@timeit
def run_wps_process(payload: str, file_path: str = None):
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(config.WPS_URL, data=payload, headers=headers, auth=(
        config.GEOSERVER_USER, config.GEOSERVER_PASSWORD))
    # Handle the response
    if response.status_code == 200:
        print("Request successful")
        print(response.text)  # or process the JSON data as needed
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(response.json(), file)
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)


def encode_geotiff_to_base64(file_path):
    with open(file_path, 'rb') as file:
        encoded_string = base64.b64encode(file.read())
    return encoded_string


if __name__ == '__main__':
    clear()
    print('Running WPS Process')
    image_base64 = encode_geotiff_to_base64(config.VARI_GEO_TIFF)
    payload = config.XML_BODY_IMAGE_BASE64.substitute(
        image_base64=image_base64)
    # with open('image_base64.txt', 'w') as file:
    #     file.write(image_base64)

    # payload2 = config.XML_BODY_UPLOAD.substitute(encoded_geotiff=image_base64)
    run_wps_process(config.XML_BODY_SAMPLE, config.OUTPUT_JSON)
    # run_wps_process(payload)

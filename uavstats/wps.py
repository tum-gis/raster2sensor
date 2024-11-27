import os
import sys
import requests
import base64
import json
from dataclasses import dataclass
from rich import print
from rich.pretty import pprint
from rich.console import Console
from rich.traceback import install
from uavstats import config
from uavstats.utils import clear, timeit, pretty_xml, get_file_name, get_files

install(show_locals=True)
console = Console()


@dataclass
class WPS:
    geoserver_url: str = config.GEOSERVER_URL
    geoserver_user = config.GEOSERVER_USER
    geoserver_password = config.GEOSERVER_PASSWORD

    def __post_init__(self):
        if not self.geoserver_url:
            raise ValueError("Geoserver URL not provided")
        self.wps_url = config.WPS_URL.substitute(
            geoserver_url=self.geoserver_url)
        self.wps_get_capabilities_url = config.WPS_GET_CAPABILITIES_URL.substitute(
            geoserver_url=self.geoserver_url)

    def get_capabilities(self) -> str:
        '''Get WPS Capabilities'''
        get_capabilities = requests.get(self.wps_get_capabilities_url)
        return get_capabilities.text

    def describe_wps_process(self, identifier: str) -> str:
        '''Describe a WPS process
            Args: identifier (str): WPS Process Identifier
            Returns: response (str): WPS Process Description
        '''
        describe_process_url = f"{self.wps_url}&request=DescribeProcess&identifier={
            identifier}"
        print(f'[green]Describing WPS Process: {identifier}')
        response = requests.get(describe_process_url)
        return response.text

    @timeit
    def execute_wps_process(self, payload: str, file_path: str = None):
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

    @staticmethod
    def encode_geotiff_to_base64(file_path):
        with open(file_path, 'rb') as file:
            encoded_string = base64.b64encode(file.read())
        return encoded_string


if __name__ == '__main__':
    clear()
    wps = WPS(config.GEOSERVER_URL)

    # # GET CAPABILITIES
    # get_capabilities = wps.get_capabilities()
    # pretty_xml(get_capabilities)

    # DESCIBE WPS PROCESS
    vector_processes = wps.describe_wps_process(
        'ras:RasterZonalStatistics')
    pretty_xml(vector_processes)

    # EXECUTE WPS PROCESS
    # image_base64 = encode_geotiff_to_base64(config.VARI_GEO_TIFF)
    # payload = config.XML_BODY_IMAGE_BASE64.substitute(
    #     image_base64=image_base64)
    # with open('image_base64.txt', 'w') as file:
    #     file.write(image_base64)

    # payload2 = config.XML_BODY_UPLOAD.substitute(encoded_geotiff=image_base64)
    # print('Running WPS Process')
    # execute_wps_process(config.XML_BODY_SAMPLE, config.OUTPUT_JSON)
    # execute_wps_process(payload)

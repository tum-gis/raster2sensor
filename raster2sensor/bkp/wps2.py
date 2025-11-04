'''
TEST: OWSLib WPS
https://ouranosinc.github.io/pavics-sdi/tutorials/wps_with_python.html
'''

from collections import OrderedDict
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
from owslib.wps import WebProcessingService
from uavstats import config
from uavstats.utils import clear, timeit, pretty_xml, get_file_name, get_files
from uavstats import xml_templates


install(show_locals=True)
console = Console()


@dataclass
class WPS:
    geoserver_url: str = config.GEOSERVER_URL
    geoserver_user: str = config.GEOSERVER_USER
    geoserver_password: str = config.GEOSERVER_PASSWORD

    def __post_init__(self):
        if not self.geoserver_url:
            raise ValueError("Geoserver URL not provided")
        self.wps_url = config.WPS_URL.substitute(
            geoserver_url=self.geoserver_url)
        self.wps_get_capabilities_url = config.WPS_GET_CAPABILITIES_URL.substitute(
            geoserver_url=self.geoserver_url)
        self.headers = {'Content-Type': 'application/xml'}
        self._wps = WebProcessingService(self.wps_url, version='1.0.0', username=self.geoserver_user,
                                         password=self.geoserver_password, headers=self.headers)

    def get_capabilities(self) -> str:
        '''Get WPS Capabilities'''
        # get_capabilities = requests.get(self.wps_get_capabilities_url)
        # return get_capabilities.text
        return self._wps.getcapabilities(xml=None)

    def get_processes(self) -> list:
        '''Get WPS Processes'''
        return self._wps.processes

    def describe_wps_process(self, identifier: str) -> str:
        '''Describe a WPS process
            Args: identifier (str): WPS Process Identifier
            Returns: response (str): WPS Process Description
        '''

        process = self._wps.describeprocess(identifier)
        return process

    @timeit
    def execute_wps_process(self, pid: str, inputs: list, outputs: list = None, mode: str = 'ASYNC', request: str = None):
        try:
            response = self._wps.execute(
                pid, inputs=inputs, output=outputs, mode=mode, request=request)
            return response
        except Exception as e:
            print(f'[red]Error: {e}')
            return None

    # @staticmethod
    # def encode_geotiff_to_base64(file_path):
    #     with open(file_path, 'rb') as file:
    #         encoded_string = base64.b64encode(file.read())
    #     return encoded_string


if __name__ == '__main__':
    clear()
    wps = WPS(config.GEOSERVER_URL)
    wps.get_capabilities()

    print('[red] GET PROCESSES')
    print(wps.get_processes())

    print('[red] DESCRIBE PROCESS')
    zonal_stats = wps.describe_wps_process('ras:RasterZonalStatistics')
    print(zonal_stats)
    inputs = [x.identifier for x in zonal_stats.dataInputs]
    print(inputs)

    wps.execute_wps_process(
        pid='', inputs='', outputs=config.OUTPUT_JSON, request=xml_templates.XML_BODY_SAMPLE)

'''
TEST: Birdy
https://birdy.readthedocs.io/en/latest/api.html
'''

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
from birdy import WPSClient
from requests.auth import HTTPBasicAuth
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


if __name__ == '__main__':
    clear()
    wps_url = config.WPS_URL.substitute(
        geoserver_url=config.GEOSERVER_URL)
    print(wps_url)
    auth = HTTPBasicAuth(config.GEOSERVER_USER, config.GEOSERVER_PASSWORD)
    wps = WPSClient(wps_url, auth=auth)
    pprint(wps._get_process_description('vec:VectorZonalStatistics'))

import json
from rich import print
import requests
from raster2sensor.utils import fetch_data
from raster2sensor.logging import get_logger, log_and_print

logger = get_logger(__name__)


# Create a class to handle OGC API - Processes
class OGCAPIProcesses:
    '''OGC API - Processes Class
    Args:
        url (str): URL to OGC API - Processes
    '''

    def __init__(self, url: str):
        self.url = url

    def get_processes(self):
        '''Fetches OGC API - Processes'''
        log_and_print(
            f'Fetching OGC API - Processes from {self.url}', level='info')
        # Add code here to fetch OGC API - Processes
        processes = fetch_data(f'{self.url}/processes')
        log_and_print(json.dumps(processes, indent=2), level='info')
        return processes

    def describe_process(self, process_id: str):
        '''Describes OGC API - Process
        Args:
            process_id (str): Process ID
        '''
        log_and_print(
            f'Describing OGC API - Process {process_id}', level='info')
        # Add code here to describe OGC API - Process
        process = fetch_data(f'{self.url}/processes/{process_id}')
        log_and_print(json.dumps(process, indent=2), level='info')
        return process

    def execute_process(self, process_id: str, inputs: dict):
        '''Executes OGC API - Process
        Args:
            process_id (str): Process ID
            inputs (dict): Inputs for the Process
        '''
        log_and_print(
            f'Executing OGC API - Process {process_id}', level='info')
        # Add code here to execute OGC API - Process
        headers = {'Content-Type': 'application/json'}
        data = {'inputs': inputs}
        try:
            execution = requests.post(
                f'{self.url}/processes/{process_id}/execution', headers=headers, json=data)
            execution.raise_for_status()
        except requests.exceptions.RequestException as e:
            log_and_print(f'Error executing process: {e}', level='error')
            print(execution.text)  # type: ignore
            return None
        return execution.json()

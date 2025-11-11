import json
import requests
from raster2sensor.utils import fetch_data
from raster2sensor.logging import get_logger

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
        logger.info(f'Fetching OGC API - Processes from {self.url}')
        processes = fetch_data(f'{self.url}/processes')
        logger.info(json.dumps(processes, indent=2))
        return processes

    def describe_process(self, process_id: str):
        '''Describes OGC API - Process
        Args:
            process_id (str): Process ID
        '''
        logger.info(
            f'Describing OGC API - Process {process_id}')
        try:
            process = fetch_data(f'{self.url}/processes/{process_id}')
            logger.info(json.dumps(process, indent=2))
            return process
        except Exception as e:
            logger.error(f'Error describing process {process_id}: {e}')
            raise e

    def execute_process(self, process_id: str, inputs: dict):
        '''Executes OGC API - Process
        Args:
            process_id (str): Process ID
            inputs (dict): Inputs for the Process
        '''
        logger.info(
            f'Executing OGC API - Process "{process_id}"')
        # Add code here to execute OGC API - Process
        headers = {'Content-Type': 'application/json'}
        data = {'inputs': inputs}
        try:
            execution = requests.post(
                f'{self.url}/processes/{process_id}/execution', headers=headers, json=data)
            execution.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f'Error executing process: {e}')
            logger.error(execution.text)  # type: ignore
            return None
        return execution.json()

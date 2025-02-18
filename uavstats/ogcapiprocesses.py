from rich import print
import requests
from uavstats.utils import fetch_data


# Create a class to handle OGC API - Processes
class OGCAPIProcesses:
    '''OGC API - Processes Class
    Args:
        url (str): URL to OGC API - Processes
    '''

    def __init__(self, url: str):
        self.url = url

    def fetch_processes(self):
        '''Fetches OGC API - Processes'''
        print(f'Fetching OGC API - Processes from {self.url}')
        # Add code here to fetch OGC API - Processes
        processes = fetch_data(f'{self.url}/processes')
        print(f'[yellow]Fetched {len(processes)} OGC API - Processes')
        print(processes)
        return processes

    def describe_process(self, process_id: str):
        '''Describes OGC API - Process
        Args:
            process_id (str): Process ID
        '''
        print(f'Describing OGC API - Process {process_id}')
        # Add code here to describe OGC API - Process
        process = fetch_data(f'{self.url}/processes/{process_id}')
        print(process)
        return process

    def execute_process(self, process_id: str, inputs: dict):
        '''Executes OGC API - Process
        Args:
            process_id (str): Process ID
            inputs (dict): Inputs for the Process
        '''
        print(f'Executing OGC API - Process {process_id}')
        # Add code here to execute OGC API - Process
        headers = {'Content-Type': 'application/json'}
        data = {'inputs': inputs}
        try:
            execution = requests.post(
                f'{self.url}/processes/{process_id}/execution', headers=headers, json=data)
            execution.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f'[red]Error executing process: {e}')
            print(execution.text)
            return None
        return execution.json()

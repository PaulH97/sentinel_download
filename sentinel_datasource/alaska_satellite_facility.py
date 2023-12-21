import asf_search as asf
import hyp3_sdk as sdk
from datetime import datetime, timedelta
from sentinel_datasource.utils import get_transformed_bbox_as_polygon
import os

class ASF():
    def __init__(self, ):
        self.collections_with_products = {'Sentinel-1': ["RAW", "SLC", "GRD", "OCN"]}
        self.session = None # class Hyp3

    def activate_session(self, credentials):
        self.session = sdk.HyP3(username=credentials["username"], password=credentials["password"])
        return

    def convert_search_parameters(self):
        # Rewrite the param in the necessary syntax for search function
        return
    
    def search(self, search_parameters):
        updated_search_parameters = {}
        for param, value in search_parameters.items():
            if param == "start":
                updated_search_parameters['start'] = search_parameters.get('start', datetime.now() - timedelta(days=15))
            elif param == "end":
                updated_search_parameters['end'] = search_parameters.get('end', datetime.now())
            elif param == 'shapefile' and value:
                polygon = get_transformed_bbox_as_polygon(value)
                updated_search_parameters['intersectsWith'] = str(polygon)
            else:
                updated_search_parameters[param] = value

        results = asf.geo_search(**updated_search_parameters)
        print(f'{len(results)} results found.')
        return results

    def start_rtc_jobs(self, search_results, rtc_specifications=None, job_name="rtc_jobs"):
        granule_ids = [result.properties["sceneName"] for result in search_results]
        # Prepare default parameters and update with rtc_specifications if provided
        default_params = {'name': job_name, 'resolution': 10}
        if rtc_specifications:
            default_params.update(rtc_specifications)
        
        # Create a batch job for all granule IDs
        rtc_jobs = sdk.Batch()
        for granule_id in granule_ids:
            rtc_jobs += self.session.submit_rtc_job(granule_id, **default_params)
        
        return rtc_jobs
        
    def start_insar_jobs(self, search_results, insar_specifications=None, job_name="insar_jobs"):
        granule_ids = [result.properties["sceneName"] for result in search_results]
        
        # Prepare default parameters and update with rtc_specifications if provided
        default_params = {'name': job_name}
        if insar_specifications:
            default_params.update(insar_specifications)

        # Create a batch job for all granule IDs
        insar_jobs = sdk.Batch()
        for granule_id in granule_ids:
            insar_jobs += self.session.submit_insar_job(granule_id, **default_params)
        
        return insar_jobs 

    def download_jobs(self, job_name, output_folder=None):
        jobs = self.session.find_jobs(name=job_name)
        output_folder = os.getcwd() if not output_folder else output_folder
        downloaded_file_paths = jobs.download_files(location=output_folder)
        return downloaded_file_paths
import asf_search as asf
import hyp3_sdk as sdk
from datetime import datetime, timedelta
from .utils import get_transformed_bbox_as_polygon
import os
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import json
from shapely.geometry import shape
import pandas as pd

class ASF():
    def __init__(self, credentials_jsonpath=""):
        self.collections = {attr: getattr(asf.PLATFORM, attr) for attr in dir(asf.PLATFORM) if not attr.startswith('_')}
        self.search_results = None
        self.credentials = {}
        self.session = None # class Hyp3

        if credentials_jsonpath and os.path.exists(credentials_jsonpath):
            self.set_credentials(credentials_jsonpath)
            self.activate_session()
        
    def available_collections(self):
        print("All available satellite platforms. Please use the exact names when searching for products.")
        print([k for k in self.collections.keys()])

    def set_credentials(self, credentials_jsonpath):
        with open(credentials_jsonpath, 'r') as file:
            self.credentials = json.load(file)

    def activate_session(self):
        try:
            # Attempt to create a session with the provided credentials
            self.session = sdk.HyP3(username=self.credentials["username"], password=self.credentials["password"])
            print("Successfully activated HyP3 session. You are now able to submit jobs and download them via ASF.")
        except ValueError as e:
            print(f"Unable to activate session with the provided user credentials: {e}")
            print("Please ensure your credentials are correct and try again.")
        except Exception as e:
            print(f"An unexpected error occurred while trying to activate the session: {e}")
            print("Please check your network connection and the status of the HyP3 service.")

    def translate_search_parameters(self, search_parameters):
        # Translate user search parameters to those expected by search function
        updated_search_parameters = {}

        # Set default start and end dates if they are not present or are empty
        updated_search_parameters['start'] = search_parameters.get('start') or datetime.now() - timedelta(days=15)
        updated_search_parameters['end'] = search_parameters.get('end') or datetime.now()

        for param, value in search_parameters.items():
            if param == "satellite":
                # Use self.collections_with_products to validate the satellite name
                if value in self.collections.keys():
                    updated_search_parameters['platform'] = self.collections[value]
                else:
                    raise ValueError(f"{value} is not a valid satellite name. Please use self.available_collections().")
            elif param == 'shapefile' and value:
                polygon = get_transformed_bbox_as_polygon(value)
                updated_search_parameters['intersectsWith'] = str(polygon)
            elif param not in ('start', 'end'):
                updated_search_parameters[param] = value
        return updated_search_parameters
    
    def search(self, search_parameters):
        updated_search_parameters = self.translate_search_parameters(search_parameters)
        self.search_results = asf.geo_search(**updated_search_parameters)
        print(f'{len(self.search_results)} results found.')
        return self.search_results
    
    def plot_results(self, shapefile, epsg_code=4326, save=False):
        data = []
        for product in self.search_results:
            properties = product.properties
            properties["geometry"] = shape(product.geometry)
            data.append(properties)

        products_df = pd.DataFrame(data)
        products_gdf = gpd.GeoDataFrame(products_df, geometry="geometry")
        bbox_epsg4326 = get_transformed_bbox_as_polygon(shapefile)
        raster_bounds = gpd.GeoDataFrame(geometry=[bbox_epsg4326], crs=f"EPSG:{epsg_code}")
        
        fig, ax = plt.subplots()
        raster_bounds.boundary.plot(ax=ax, color='red')  
        products_gdf.boundary.plot(ax=ax, color='blue')

        # Plotting names at centroids for cdse_products_gdf
        for idx, row in products_gdf.iterrows():
            centroid = row['geometry'].centroid
            ax.text(centroid.x, centroid.y, s=row['frameNumber'], horizontalalignment='center')

        ctx.add_basemap(ax, crs=f"EPSG:{epsg_code}")
        
        ax.set_title("Boundaries Overlay")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        if save:
            plt.savefig("asf_results_boundaries.png")
        else:
            plt.show()

    def get_nearest_neighbors(self, granule, max_neighbors=None):
        granule = asf.granule_search(granule)[0]
        stack = reversed([item for item in granule.stack() if item.properties['temporalBaseline'] < 0]) # here we can optimize the search results -> select by frame number etc.
        return asf.ASFSearchResults(stack)[:max_neighbors]

    def start_rtc_jobs(self, rtc_specifications=None, job_name="rtc_jobs"):
        granule_ids = [result.properties["sceneName"] for result in self.search_results]
        # Prepare default parameters and update with rtc_specifications if provided
        default_params = {'name': job_name}
        if rtc_specifications:
            default_params.update(rtc_specifications)
        
        # Create a batch job for all granule IDs
        rtc_jobs = sdk.Batch()
        for granule_id in granule_ids:
            rtc_jobs += self.session.submit_rtc_job(granule_id, **default_params)
        
        return rtc_jobs
        
    def start_insar_jobs(self, insar_specifications=None, job_name="insar_jobs"):
        # Prepare default parameters and update with rtc_specifications if provided
        default_params = {'name': job_name}
        if insar_specifications:
            default_params.update(insar_specifications)
        
        # Create a batch job for all granule IDs
        insar_jobs = sdk.Batch()
        for result in self.search_results:
            granule_id = result.properties["sceneName"]
            neighbors = self.get_nearest_neighbors(granule_id, max_neighbors=2)
            for secondary in neighbors:
                insar_jobs += self.session.submit_insar_job(granule_id, secondary.properties['sceneName'], **default_params)
        return insar_jobs 

    def get_jobs(self, job_name, status="all"):
        if status == "all":
            return self.session.find_jobs(name=job_name)
        else:
            return self.session.find_jobs(name=job_name, status_code=status)
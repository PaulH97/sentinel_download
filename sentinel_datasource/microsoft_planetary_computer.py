import pystac_client
import planetary_computer 
from datetime import datetime, timedelta
from sentinel_datasource.utils import get_transformed_bbox
from urllib import request
from pathlib import Path
from mimetypes import guess_extension

class PlanetaryComputer():
    def __init__(self, api_key):
        self.base_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.collections_with_products = {'Sentinel-1': ['sentinel-1-grd', 'sentinel-1-rtc'], 'Sentinel-2': ['sentinel-2-l2a']}
        self.api_key = api_key
        if self.api_key:
            planetary_computer.set_subscription_key(self.api_key)      

    def search(self, search_parameters):
        start_date = search_parameters.get('start', datetime.now() - timedelta(days=15))
        end_date = search_parameters.get('end', datetime.now())
        updated_search_parameters = {}
        for param, value in search_parameters.items():
            if param == "collection":
                updated_search_parameters['collections'] = [value]
            elif param in ["start", "end"]:
                updated_search_parameters['datetime'] = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            elif param == 'shapefile' and value:
                bbox = get_transformed_bbox(value)
                updated_search_parameters['bbox'] = bbox # [32.60, -20.16, 33.01, -19.50]
            else:
                updated_search_parameters[param] = value

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace
            )
        
        results = catalog.search(**updated_search_parameters)
        print(f"Returned {len(results.item_collection())} items.")
        return results      

    def download_all_assets(search_result, output_dir=""):
        if not output_dir:
            Path().cwd
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []

        for item in search_result.item_collection_as_dict()['features']:
            for asset_key, asset in item['assets'].items():
                if 'href' in asset:
                    file_url = asset['href']
                    file_extension = guess_extension(asset.get('type', ''))
                    file_name = f"{item['id']}_{asset_key}{file_extension}"
                    output_file_path = output_dir / file_name
                    try:
                        request.urlretrieve(file_url, output_file_path)
                        downloaded_files.append(output_file_path)
                        print(f"Downloaded asset: {asset_key}")
                    except Exception as e:
                        print(f"Failed to download asset {asset_key}. Error: {e}")

        return downloaded_files



import requests
from pathlib import Path
from sentinel_datasource.utils import get_transformed_bbox_as_polygon, create_output_dir

class CDSE():
    def __init__(self):
        self.base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"
        self.zipper_url = "https://zipper.dataspace.copernicus.eu/odata/v1"
        self.collections_with_products = {'SENTINEL-1':['SLC', 'GRD', 'RTC'], 'SENTINEL-2':[]}

    def search_odata(self, search_parameters):
        updated_search_parameters = {}
        for param, value in search_parameters.items():
            if param == 'start':
                updated_search_parameters[param] = value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            elif param == 'end':
                updated_search_parameters[param] = value.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            elif param == "shapefile":
                updated_search_parameters[param] = get_transformed_bbox_as_polygon(value) 
            else:
                updated_search_parameters[param] = value
        
        search_query_template = (
            f"{self.base_url}/Products?$filter=Collection/Name eq '{updated_search_parameters["collection"]}' "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{updated_search_parameters['shapefile']}') "
            f"and contains(Name,'{updated_search_parameters["product"]}') "
            f"and ContentDate/Start gt {updated_search_parameters['start']} "
            f"and ContentDate/Start lt {updated_search_parameters['end']}"
        )
        search_query = search_query_template.replace(' ', "%20") # URL cant have spaces
        result = requests.get(search_query).json()['value']
        print(f"Found {len(result)} results.")
        return result

    def search_openSearch(self):
        pass

    def download(self, items, output_dir=""):
        output_dir = create_output_dir(output_dir)
        # for item in items:
        #     print("Start downloading assets for item: ", item.id)
        #     for asset_key, asset in item.assets.items():
        #         mime_type = asset.to_dict()["type"]
        #         # make sure that only one file extension is loaded
        #         mime_type = mime_type.split(';')[0].strip() if ";" in mime_type else mime_type 
            
        #         file_name = f"{item.id}_{asset_key}{file_extension}"
        #         output_file_path = output_dir / file_name
        #         try:
        #             file_url = asset.href
        #             request.urlretrieve(file_url, output_file_path)
        #             print(f"Downloaded asset: {asset_key}")
        #         except Exception as e:
        #             print(f"Failed to download asset {asset_key}. Error: {e}")
        return output_dir





        url = self.zipper_url + "Products({product_id})/$value"

        headers = {"Authorization": f"Bearer {access_token}"}

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)

        with open("product.zip", "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)


import requests
import os
from sentinel_datasource.utils import * 
import json
import boto3
from pathlib import Path

class CDSE():
    def __init__(self, credentials_jsonpath="", aws_keys_jsonpath=""):
        self.base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"
        self.zipper_url = "https://zipper.dataspace.copernicus.eu/odata/v1"
        self.base_s3url = "https://eodata.dataspace.copernicus.eu"
        self.collections_with_products = {'SENTINEL-1':['SLC', 'GRD', 'RTC'], 'SENTINEL-2':['L1C', 'L2A']}
        self.credentials = {}
        self.aws_keys = {}

        if credentials_jsonpath and os.path.exists(credentials_jsonpath):
            self.set_credentials(credentials_jsonpath)

        if aws_keys_jsonpath and os.path.exists(aws_keys_jsonpath):
            self.set_aws_keys(aws_keys_jsonpath)

    def set_aws_keys(self, aws_keys_jsonpath):
        with open(aws_keys_jsonpath, 'r') as file:
            self.aws_keys = json.load(file)

    def set_credentials(self, credentials_jsonpath):
        with open(credentials_jsonpath, 'r') as file:
            self.credentials = json.load(file)

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
        access_token = get_cdse_access_token(self.credentials)
        headers = {"Authorization": f"Bearer {access_token}"}

        for item in items:
            item_name = item["Name"].split(".")[0]
            item_folder = os.path.join(output_dir, item_name)
            os.makedirs(item_folder, exist_ok=True)
            url = os.path.join(self.zipper_url, f"Products({item['Id']})/$value")
            with requests.Session() as session:
                print(f"Starting download of {item['Name']}")
                session.headers.update(headers)
                response = session.get(url, headers=headers, stream=True)
                output_file_path = os.path.join(item_folder, item["Name"].split(".")[0] + ".zip")
                with open(output_file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                print("\nDownloaded file: ", output_file_path)
        return output_dir

    def aws_download(self, items, output_dir=""):
        output_dir = create_output_dir(output_dir)
        s3 = boto3.client(
                's3',
                aws_access_key_id=self.aws_keys["access_key"],
                aws_secret_access_key=self.aws_keys["secret_key"], 
                endpoint_url=self.base_s3url
                )
        for item in items:
            item_name = item["Name"].split(".")[0]
            item_folder = os.path.join(output_dir, item_name)
            os.makedirs(item_folder, exist_ok=True)
            print(f"Starting download of data via AWS-S3 in folder: ", item_folder)
            s3_path_parts = item["S3Path"].split(os.sep)
            bucket_name = s3_path_parts[1]
            prefix = os.path.join(*s3_path_parts[2:])

            paginator = s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=str(prefix))

            for page in page_iterator:
                for obj in page.get("Contents", []):
                    obj_key = obj["Key"]
                    output_path = os.path.join(item_folder, obj_key.split('/')[-1])
                    if not os.path.exists(output_path):
                        s3.download_file(bucket_name, obj_key, str(output_path))
                        print(f"Downloaded {obj_key} to {output_path}")
                    else:
                        print(f"File already existing! Skipped download of {obj_key}")

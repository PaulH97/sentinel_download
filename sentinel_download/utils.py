import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
import requests

def create_output_dir(output_dir):
    if output_dir:
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            # If not an absolute path, make it a subdirectory of the CWD
            output_dir = Path.cwd() / output_dir
    else:
        output_dir = Path().cwd()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_transformed_bbox_as_polygon(shapefile, epsg_code=4326):
    gdf = gpd.read_file(shapefile)
    original_bbox = box(*gdf.total_bounds)
    transformed_bbox = gpd.GeoSeries([original_bbox], crs=gdf.crs).to_crs(epsg=epsg_code).iloc[0]
    transformed_coords = list(transformed_bbox.exterior.coords)
    return box(*transformed_coords[0],*transformed_coords[2])

def get_transformed_bbox(shapefile, epsg_code=4326):
    gdf = gpd.read_file(shapefile)
    original_bbox = box(*gdf.total_bounds)
    transformed_bbox = gpd.GeoSeries([original_bbox], crs=gdf.crs).to_crs(epsg=epsg_code).iloc[0]
    minx, miny, maxx, maxy = transformed_bbox.bounds
    return [minx,miny,maxx,maxy]

def get_file_size_from_header(head_response):
    file_size_bytes = int(head_response.headers.get('Content-Length', 0))
    if file_size_bytes >= 1024 ** 3:  # Greater than 1 GB
        file_size = file_size_bytes / (1024 ** 3)
    else:
        file_size = file_size_bytes / (1024 ** 2)
    return file_size

def get_cdse_access_token(credentials):
    data = {
        "client_id": "cdse-public",
        "username": credentials['username'],
        "password": credentials['password'],
        "grant_type": "password",
        }
    try:
        r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",data=data)
        r.raise_for_status()
    except Exception as e:
        raise Exception(f"Access token creation failed. Reponse from the server was: {r.json()}")
    return r.json()["access_token"]


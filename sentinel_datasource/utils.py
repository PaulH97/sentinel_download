import geopandas as gpd
from shapely.geometry import box
from pathlib import Path

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

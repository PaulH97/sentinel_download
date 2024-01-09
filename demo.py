from sentinel_download.alaska_satellite_facility import ASF
from sentinel_download.microsoft_planetary_computer import PlanetaryComputer
from sentinel_download.copernicus_dataspace import CDSE
from datetime import datetime, timedelta

satellite = 'Sentinel-1'
processing_level = 'SLC'
start_date = datetime(year=2018, month=6, day=28) - timedelta(days=5)
end_date = datetime(year=2018, month=6, day=28) + timedelta(days=5)
shapefile_path = "/p/project/hai_wemonitor/S2LS/data/locations/Hiroshima/annotations/Hiroshima.shp"

search_parameters = {
    'satellite': satellite,
    'processingLevel': processing_level,
    'start' : start_date,
    'end' : end_date,
    'shapefile': shapefile_path
}

asf_results = ASF.search(search_parameters)
print("File ID of first result: ", asf_results[0].properties["fileID"] )
print("Properties: ", [result.properties for result in asf_results])


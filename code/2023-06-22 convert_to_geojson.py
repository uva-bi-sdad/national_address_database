import pandas as pd
import os
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import geopandas as gpd
import contextily as ctx
import matplotlib as mpl
from fiona.io import ZipMemoryFile
import io

if __name__ == "__main__":
    valid_zips = [
        os.path.join("../data/shapefiles", file)
        for file in os.listdir("../data/shapefiles")
        if file.split(".")[-1] == "zip"
    ]

    total_counties_df = []

    for county_file in tqdm(sorted(valid_zips)):
        county = county_file.split("tl_2020_")[1].split("_")[0]
        save_file_path = "../data/shapes/%s.geojson" % county
        # print(save_file_path)
        if os.path.isfile(save_file_path):
            county_shape_df = gpd.read_file(save_file_path)
        else:
            # Annoying read using https://gis.stackexchange.com/questions/383465/from-uploaded-zipped-shapefile-to-geopandas-dataframe-in-django-application
            # Just to create a BytesIO object for the demo,
            # similar to your request.FILES['file'].file
            zipshp = io.BytesIO(open(county_file, "rb").read())

            with ZipMemoryFile(zipshp) as memfile:
                with memfile.open() as src:
                    crs = src.crs
                    county_shape_df = gpd.GeoDataFrame.from_features(src, crs=crs)
            county_shape_df.to_file(save_file_path, driver="GeoJSON")
        county_shape_df.crs = "epsg:4326"
        total_counties_df.append(county_shape_df)

    total_counties_df = pd.concat(total_counties_df)
    print(total_counties_df)

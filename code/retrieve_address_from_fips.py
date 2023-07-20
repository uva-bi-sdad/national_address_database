import pandas as pd
import geopandas as gpd
import random
import numpy as np
from geopy.point import Point
from shapely.geometry import Point as sPoint
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from tqdm import tqdm
import pathlib
import sys
import math
from stem import Signal
from stem.control import Controller
import time
import os
from pathlib import Path


"""
Iterate across each county, use reverse geocoding on 10 random location per census block and get an address
Then, remove duplicates and save back to the original data frame. Worry about verifying the freshness of the address later
"""


def get_lat_longs(gdf, geoid, points_per_geo=10):
    aoi = gdf[gdf["GEOID20"].str[: len(geoid)] == geoid]
    aoi_geom = aoi.unary_union

    # find area bounds
    bounds = aoi_geom.bounds
    xmin, ymin, xmax, ymax = bounds

    xext = xmax - xmin
    yext = ymax - ymin

    points = []
    while len(points) < points_per_geo:
        # generate a random x and y
        x = xmin + random.random() * xext
        y = ymin + random.random() * yext
        p = sPoint(x, y)
        if aoi_geom.contains(p):  # check if point is inside geometry
            points.append(p)

    return points


geolocator = Nominatim(user_agent="test")


def reverse_geocoding(lat, lon):
    try:
        location = geolocator.reverse(Point(lat, lon))
        return location.raw["display_name"]
    except KeyboardInterrupt:
        sys.exit()
    except:
        return None


# signal TOR for a new connection
def renew_connection():
    with Controller.from_port(port=9080) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def get_address_df(geoid, geo_column_id="GEOID20", num_samples=1):
    shape_file_url = os.path.join(
        str(Path.home()),
        "Documents/GitHub/national_address_database/data/shapefiles/tl_2020_{county}_tabblock20.zip",
    )
    county = geoid[:5]
    # Download the shapefiles
    gdf = gpd.read_file(shape_file_url.format(county=county))
    dfs = []

    gdf["layer"] = gdf[geo_column_id].str[
        : len(geoid)
    ]  # variable based on the resolution

    # Filter based on the variable resolution
    gdf = gdf[gdf["layer"] == geoid]

    empty_bar = tqdm(gdf["layer"].unique())
    for geoid in empty_bar:
        empty_bar.set_description("Extracting lat long for: %s" % geoid)
        pdf = pd.DataFrame()
        pts = get_lat_longs(gdf, geoid, points_per_geo=num_samples)
        pdf["geometry"] = pts
        pdf["longitude"] = pdf["geometry"].apply(lambda x: x.x)
        pdf["latitude"] = pdf["geometry"].apply(lambda x: x.y)
        pdf["geoid"] = geoid
        # print(pdf)
        dfs.append(pdf)
    rgeo_df = pd.concat(dfs)

    # rgeo_df = rgeo_df.head(11)  # for quicker testing
    # Set a batch size limit of 2000
    batch_size = 500
    addresses = []
    batch_bar = tqdm(range(int(math.ceil(len(rgeo_df) / batch_size))))
    for i in batch_bar:
        batch_bar.set_description(
            "Processing batch (%s/%s), size: %s"
            % (
                i + 1,
                int(math.ceil(len(rgeo_df) / batch_size)),
                len(rgeo_df["latitude"][i * batch_size : (i + 1) * batch_size]),
            )
        )

        addresses.extend(
            np.vectorize(reverse_geocoding)(
                rgeo_df["latitude"][i * batch_size : (i + 1) * batch_size],
                rgeo_df["longitude"][i * batch_size : (i + 1) * batch_size],
            )
        )

        batch_bar.set_description("Changing ip address")
        # renew_connection()

    rgeo_df["address"] = addresses
    rgeo_df.reset_index(inplace=True)
    return rgeo_df


if __name__ == "__main__":
    """
    Given a list of geoids, return a data frame with the addresses and coordinates
    """
    adf = get_address_df("010070100011", geo_column_id="GEOID20", num_samples=1)
    print(adf)

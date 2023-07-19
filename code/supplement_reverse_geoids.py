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

"""
Iterate across each county, use reverse geocoding on 10 random location per census block and get an address
Then, remove duplicates and save back to the original data frame. Worry about verifying the freshness of the address later
"""


def get_lat_longs(gdf, geoid, point_per_block=10):
    aoi = gdf[gdf["GEOID20"].str[: len(geoid)] == geoid]
    aoi_geom = aoi.unary_union

    # find area bounds
    bounds = aoi_geom.bounds
    xmin, ymin, xmax, ymax = bounds

    xext = xmax - xmin
    yext = ymax - ymin

    points = []
    while len(points) < point_per_block:
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
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def randomly_query_geoids(geoids, num_samples=1, batch_size=500, save=False):
    # Download the shapefiles
    shapefile_url = "../../national_address_database/data/shapefiles/tl_2020_{county}_tabblock20.zip"

    dfs = []
    empty_bar = tqdm(geoids)  # Create the progress bar for the data frame
    # For the given geoid, generate n numnbner of points, equal to num_samples
    for geoid in empty_bar:
        empty_bar.set_description("Extracting lat long for: %s" % geoid)
        county = geoid[:5]
        gdf = gpd.read_file(shapefile_url.format(county=county))
        pdf = gdf[gdf["GEOID20"].str[: len(geoid)] == geoid]
        pdf = pdf.loc[pdf.index.repeat(num_samples)]
        pdf = pdf.reset_index(drop=True)
        pts = get_lat_longs(gdf, geoid, point_per_block=num_samples)

        new_df = pd.DataFrame()
        new_df["geometry"] = pts
        new_df["longitude"] = new_df["geometry"].apply(lambda x: x.x)
        new_df["latitude"] = new_df["geometry"].apply(lambda x: x.y)
        new_df["GEOID20"] = geoid

        dfs.append(new_df)
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
    print("length of addresses: %s" % len(addresses))
    print("length of data frame: %s" % len(rgeo_df))

    rgeo_df["address"] = addresses

    # Read the existing data
    for county in [s[:2] for s in geoids]:
        # For each county division, save back in to the file

        p = pathlib.Path("../data/address/{county}.csv.xz".format(county=county))
        df = pd.read_csv(p.resolve(), dtype={"GEOID20": object})

        pdf = rgeo_df[rgeo_df["GEOID20"].str[:5] == county]
        # Combine the two data frames
        final_df = pd.concat([df, pdf])

        # Get the empty data frame (need to keep because even if address is null, we want to keep null addresses if the geoid is not fiilled)
        edf = final_df[final_df["address"].isnull()]
        final_df = final_df[final_df["address"].notnull()]
        final_df = final_df.drop_duplicates(
            subset="GEOID20", keep="last"
        )  # Remove duplicates, because there could be repeated addresses

        # Retain exsting empties, in case not covered
        final_df = pd.concat([final_df, edf])
        final_df = final_df.sort_values(by="GEOID20")  # sort by geoid, to look good

        if save:
            final_df.to_csv(p.resolve(), index=False)

    return final_df


if __name__ == "__main__":
    # shape_file_url = "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_{county}_tabblock20.zip"

    # Manually look up the ones that are missing
    with open("../../data/missing_census_block_grps.txt", "r") as f:
        geoids = eval(f.read())

    randomly_query_geoids(geoids, num_samples=10, save=True)
    # time.sleep(0.1)

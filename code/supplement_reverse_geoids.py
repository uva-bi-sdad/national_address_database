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

last_changed_time = time.time()


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
    global last_changed_time
    if (time.time() - last_changed_time) > (60 * 5):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        last_changed_time = time.time()
    else:
        print("Last changed within 5 minutes, skipping...")


def randomly_query_geoids(geoid, num_samples=1, batch_size=500, pbar=None, save=False):
    assert pbar is not None
    # Download the shapefiles
    shapefile_url = "../../national_address_database/data/shapefiles/tl_2020_{county}_tabblock20.zip"

    dfs = []

    pbar.set_description("Extracting lat long for: %s" % geoid)
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

    rgeo_df = new_df
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
        renew_connection()

    pbar.set_description("length of addresses: %s" % len(addresses))
    pbar.set_description("length of data frame: %s" % len(rgeo_df))

    rgeo_df["address"] = addresses

    # Read the existing data
    county = geoid[:5]

    # For each county division, save back in to the file

    p = pathlib.Path("../data/address/{county}.csv.xz".format(county=county))
    df = pd.read_csv(p.resolve(), dtype={"GEOID20": object})

    pdf = rgeo_df[rgeo_df["GEOID20"].str[:5] == county]
    # Combine the two data frames
    final_df = pd.concat([df, pdf])

    # Get the empty data frame (need to keep because even if address is null, we want to keep null addresses if the geoid is not fiilled)
    final_df = final_df.drop_duplicates(
        subset=["address", "GEOID20"], keep="last"
    )  # Remove duplicates, because there could be repeated addresses

    final_df = final_df.sort_values(by="GEOID20")  # sort by geoid, to look good

    if save:
        assert len(final_df["GEOID20"].unique()) >= len(df["GEOID20"].unique()), print(
            "Final unique geoid length (%s) is less than original (%s)"
            % (len(final_df["GEOID20"].unique()), len(df["GEOID20"].unique()))
        )
        assert len(final_df["address"].unique()) >= len(df["address"].unique()), print(
            "Final unique address length (%s) is not greater than original (%s)"
            % (len(final_df["address"].unique()), len(df["address"].unique()))
        )

        pbar.set_description(
            "Updating: %s, old size: %s, new size: %s"
            % (
                p.resolve(),
                len(final_df["address"].unique()),
                len(df["address"].unique()),
            )
        )
        final_df.to_csv(p.resolve(), index=False)

    return final_df


if __name__ == "__main__":
    # shape_file_url = "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_{county}_tabblock20.zip"

    # Manually look up the ones that are missing
    with open(
        "../../sdc.broadband.broadbandnow/data/missing_census_block_grps.txt", "r"
    ) as f:
        geoids = sorted(eval(f.read()))

    pbar = tqdm(geoids[138:])
    for geoid in pbar:
        randomly_query_geoids(geoid, num_samples=10, save=True, pbar=pbar)
    # time.sleep(0.1)

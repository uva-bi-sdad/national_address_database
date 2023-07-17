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


def get_lat_longs(gdf, census_block, point_per_block=10):
    aoi = gdf[gdf["GEOID20"] == census_block]
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


def fire_in_the_hole(
    file, county, pbar=None, geo_column_id="GEOID20", num_samples=1, save=False
):
    df = pd.read_csv(file, dtype={geo_column_id: object})
    # We are only interested in reverse-geocoding addresses that are empty
    empty_df = df[df["address"].isnull()]

    # Skip is there are no empty addresses
    if empty_df.empty:
        pbar.set_description("[%s] contains no empty addresses, skipping ..." % county)
        return

    # Download the shapefiles
    gdf = gpd.read_file(shape_file_url.format(county=county))
    empty_sdf = gdf[gdf[geo_column_id].isin(list(empty_df[geo_column_id].unique()))]

    # fire_in_the_hole(file, '12049')
    df = pd.read_csv(file, dtype={geo_column_id: object})
    # We are only interested in reverse-geocoding addresses that are empty
    empty_df = df[df["address"].isnull()]

    dfs = []
    empty_bar = tqdm(empty_df[geo_column_id])
    for geoid in empty_bar:
        empty_bar.set_description("Extracting lat long for: %s" % geoid)
        pdf = empty_df[empty_df[geo_column_id] == geoid]
        pdf = pdf.loc[pdf.index.repeat(num_samples)]
        pdf = pdf.reset_index(drop=True)

        assert geoid in gdf[geo_column_id].unique(), print(geoid)
        pts = get_lat_longs(gdf, geoid, point_per_block=num_samples)
        pdf["geometry"] = pts
        pdf["longitude"] = pdf["geometry"].apply(lambda x: x.x)
        pdf["latitude"] = pdf["geometry"].apply(lambda x: x.y)
        # print(pdf)
        dfs.append(pdf)
    rgeo_df = pd.concat(dfs)
    if pbar:
        pbar.set_description(
            "Running reverse geocoding for %s on %s elements" % (county, len(rgeo_df))
        )
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
    final_df = pd.concat([df, rgeo_df])
    final_df = final_df.sort_values(by=geo_column_id)  # sort by geoid
    final_df = final_df.drop_duplicates(
        subset=geo_column_id, keep="last"
    )  # Remove duplicates, because there could be repeated addresses
    if save:
        if len(df[geo_column_id].unique()) != len(final_df[geo_column_id].unique()):
            os.system(
                'echo "%s final geoid column count not the same: %s/%s\n" >> fill.log'
                % (
                    county,
                    len(df[geo_column_id].unique()),
                    len(final_df[geo_column_id].unique()),
                )
            )
        if len(df[df["address"].isnull()]) <= len(
            final_df[final_df["address"].isnull()]
        ):
            os.system(
                'echo "%s final address count not less than or equal to original same: %s/%s\n" >> fill.log'
                % (
                    county,
                    len(df[df["address"].isnull()]),
                    len(final_df[final_df["address"].isnull()]),
                )
            )

        final_df.to_csv(file, index=False)
        # final_df.to_csv(
        #     os.path.join(file.parents[0], "test_" + file.name), index=False
        # )  # for testing
    print(final_df)
    return final_df


if __name__ == "__main__":
    shape_file_url = "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_{county}_tabblock20.zip"
    p = pathlib.Path("../data/address/").glob("*.xz")
    pbar = tqdm(sorted(p))
    for file in pbar:
        pbar.set_description("Processing: %s" % file.name)
        county = file.name.split(".")[0]
        if not county[:2] in ["01", "13"]:  # custom search
            continue
        fire_in_the_hole(file, county, pbar=pbar, num_samples=3, save=True)
        # time.sleep(0.1)

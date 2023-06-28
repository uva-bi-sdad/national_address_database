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


def fire_in_the_hole(file, county, geo_column_id="GEOID20", num_samples=3, save=False):
    df = pd.read_csv(file)
    # We are only interested in reverse-geocoding addresses that are empty
    empty_df = df[df["address"].isnull()]

    # Skip is there are no empty addresses
    if empty_df.empty:
        return

    # Download the shapefiles
    gdf = gpd.read_file(shape_file_url.format(county=county))
    empty_sdf = gdf[gdf[geo_column_id].isin(list(empty_df[geo_column_id].unique()))]

    # fire_in_the_hole(file, '12049')
    df = pd.read_csv(file, dtype={geo_column_id: object})
    # We are only interested in reverse-geocoding addresses that are empty
    empty_df = df[df["address"].isnull()]

    dfs = []
    for geoid in tqdm(empty_df[geo_column_id]):
        pdf = empty_df[empty_df[geo_column_id] == geoid]
        pdf = pdf.loc[pdf.index.repeat(num_samples)]
        pdf = pdf.reset_index(drop=True)

        assert geoid in gdf[geo_column_id].unique(), print(geoid)
        pts = get_lat_longs(gdf, geoid, point_per_block=num_samples)
        pdf["geometry"] = pts
        pdf["longitude"] = pdf["geometry"].apply(lambda x: x.x)
        pdf["latitude"] = pdf["geometry"].apply(lambda x: x.y)
        pdf["address"] = np.vectorize(reverse_geocoding)(
            pdf["latitude"], pdf["longitude"]
        )
        # print(pdf)
        dfs.append(pdf)
    rgeo_df = pd.concat(dfs)
    final_df = pd.concat([df[~df["address"].isnull()], rgeo_df])
    final_df = final_df.sort_values(by=geo_column_id)  # sort by geoid
    final_df = final_df.drop_duplicates(
        subset=geo_column_id, keep="last"
    )  # Remove duplicates, because there could be repeated addresses
    if save:
        final_df.to_csv(file, index=False)
    return final_df


if __name__ == "__main__":
    shape_file_url = "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_{county}_tabblock20.zip"
    p = pathlib.Path("../data/address/").glob("*.xz")
    pbar = tqdm(sorted(p))
    for file in pbar:
        pbar.set_description("Processing: %s" % file.name)
        county = file.name.split(".")[0]
        fire_in_the_hole(file, county, save=True)

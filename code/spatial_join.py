import requests
import numpy as np
import os
import pandas as pd
from tqdm import tqdm
import argparse
import pandas as pd
import requests
import math
from io import StringIO
import warnings
import logging
import pathlib
import shutil
import geopandas as gpd
from glob import glob

# download shapefiles: wget -P ../data/shapefiles/ https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_13121_tabblock20.zip


def main(
    input_file,
    input_county_fips,
    output_file,
):
    warnings.filterwarnings("ignore")

    # Fix later
    # os.system(
    #     "wget -N ../data/shapefiles/ https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_%s_tabblock20.zip"
    #     % input_county_fips
    # )
    shapefile_path = "../data/shapefiles/tl_2020_%s_tabblock20.zip" % input_county_fips
    assert os.path.isfile(shapefile_path)

    state_df = gpd.read_file(shapefile_path)
    state_df["county_id"] = state_df["STATEFP20"] + state_df["COUNTYFP20"]

    lat_lon_df = pd.read_csv(input_file)
    cgdf = gpd.GeoDataFrame(
        lat_lon_df,
        geometry=gpd.points_from_xy(lat_lon_df.longitude, lat_lon_df.latitude),
    )
    # Spatial join the address with points and the jeffesron county blocks with polygons

    joined_county_df = state_df.sjoin(cgdf, how="left", predicate="intersects")
    print(joined_county_df)
    joined_county_df = joined_county_df[
        ["address", "GEOID20", "longitude", "latitude", "geometry"]
    ]
    joined_county_df = joined_county_df.rename(columns={"GEOID20": "geoid20"})
    joined_county_df.to_csv(output_file, index=False)
    logging.info("[%s] File saved to: %s" % (os.path.isfile(output_file), output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given a csv and you are running in the code repository, download the shape file and attempt an outerjoin spatially and return the results"
    )

    parser.add_argument(
        "-i",
        "--input_file",
        type=str,
        help="The input csv with lat long columns to sptial join",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--input_county_fips",
        type=str,
        help="The input county fips to do the spatial joining",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="The output csv where matches are found",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show debugging outputs",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-f",
        "--force",
        action=argparse.BooleanOptionalAction,
        help="Whether or not to override the output file",
        required=False,
        default=False,
    )

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    assert os.path.isfile(args.input_file), "input file is invalid"

    test_df = pd.read_csv(args.input_file)

    assert "latitude" in test_df.columns
    assert "longitude" in test_df.columns

    if not args.force:
        assert not os.path.isfile(args.output_file), "output file is invalid"

    main(
        args.input_file,
        args.input_county_fips,
        args.output_file,
    )

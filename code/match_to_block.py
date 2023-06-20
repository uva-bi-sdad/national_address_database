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
    input_shapefile_dir,
):
    warnings.filterwarnings("ignore")
    lat_lon_df = pd.read_csv(input_file)
    cgdf = gpd.GeoDataFrame(
        lat_lon_df,
        geometry=gpd.points_from_xy(lat_lon_df.longitude, lat_lon_df.latitude),
    )

    for sf in tqdm(os.listdir(input_shapefile_dir)):
        shapefile_path = os.path.join(input_shapefile_dir, sf)
        state_df = gpd.read_file(shapefile_path)

        # Spatial join the address with points and the jeffesron county blocks with polygons
        joined_county_df = cgdf.sjoin(state_df, how="left", predicate="intersects")

        print(joined_county_df)

        joined_county_df = joined_county_df[
            ["address", "GEOID20", "longitude", "latitude"]
        ]
        joined_county_df = joined_county_df.rename(columns={"GEOID20": "geoid20"})
        joined_county_df.to_csv(input_file, index=False)
        logging.info(
            "[%s] File saved to: %s (%s)"
            % (os.path.isfile(input_file), input_file, len(joined_county_df))
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given a file with lat lon columns, iterate across all shapefiles and join with a GEOID20 column, saving back to the same directory"
    )

    parser.add_argument(
        "-i",
        "--input_file",
        type=str,
        help="The input csv with lat long columns to sptial join",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--input_shapefile_dir",
        type=str,
        help="A directory containing all of the shapefiles downloaded",
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

    main(
        args.input_file,
        args.input_shapefile_dir,
    )

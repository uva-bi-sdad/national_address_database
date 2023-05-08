import requests
import numpy as np
import os
import pandas as pd
from tqdm import tqdm
import argparse
import pandas as pd
import requests
from tqdm import tqdm
import math
from io import StringIO
import warnings
import logging
import pathlib
import shutil
import geopandas as gpd
from glob import glob


def main(
    input_file,
    input_state_shapefile,
    output_file,
    county_fips,
    num_samples_per_block,
):
    warnings.filterwarnings("ignore")

    state_df = gpd.read_file(input_state_shapefile)
    state_df["county_id"] = state_df["STATEFP20"] + state_df["COUNTYFP20"]
    bdf = state_df[state_df["county_id"] == county_fips]

    assert len(bdf) > 0, "No data remains after county filter on (%s)" % county_fips
    lat_lon_df = pd.read_csv(input_file)
    cgdf = gpd.GeoDataFrame(
        lat_lon_df, geometry=gpd.points_from_xy(lat_lon_df.lon, lat_lon_df.lat)
    )
    # Spatial join the address with points and the jeffesron county blocks with polygons

    joined_county_df = state_df.sjoin(cgdf, how="inner", predicate="intersects")
    joined_county_df = joined_county_df[["street", "GEOID20", "lon", "lat", "geometry"]]
    joined_county_df = joined_county_df.rename(columns={"GEOID20": "geoid20"})
    one_per_block = (
        joined_county_df.groupby("geoid20")
        .apply(lambda x: x.sample(num_samples_per_block))
        .reset_index(drop=True)
    )  # randomly get n per county
    one_per_block = one_per_block.rename(columns={"street": "address"})
    one_per_block.to_csv(output_file, index=False)
    logging.info("[%s] File saved to: %s" % (os.path.isfile(output_file), output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given a csv, create an ouput directory with batched fcc area geocoding queries. Assumes that the csv is already formatted to fcc area api standards. Note if the force flag is false, the process will continue where it left off as long as the ouput_dir is the same."
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
        "--input_shapefile",
        type=str,
        help="The input shapefile with block geometries at the state level for the sptial join",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--input_county_fips",
        type=str,
        help="The county fips to filter from the shapefiles",
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
    parser.add_argument(
        "-n",
        "--num_samples_per_block",
        type=int,
        help="The number of values to sample per block (defaults to 1)",
        default=1,
    )

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    assert os.path.isfile(args.input_file), "input file is invalid"

    test_df = pd.read_csv(args.input_file)

    assert "lat" in test_df.columns
    assert "lon" in test_df.columns
    assert (
        args.num_samples_per_block > 0
    ), "number of values to sample per block is not greater than 0"

    if not args.force:
        assert not os.path.isfile(args.output_file), "output file is invalid"

    main(
        args.input_file,
        args.input_shapefile,
        args.output_file,
        args.input_county_fips,
        args.num_samples_per_block,
    )

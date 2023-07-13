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
import psycopg2
import shutil
from sshtunnel import SSHTunnelForwarder, open_tunnel
from decouple import config

# import traceback


def download_data(county_fips, temp_dir):

    # decouple so that passwords are not stored
    logging.debug("Starting download of: %s to %s" % (county_fips, temp_dir))
    ssh_port = int(config("ssh_port"))

    with SSHTunnelForwarder(
        (config("ssh_host"), 22),
        ssh_username=config("ssh_user"),
        ssh_password=config("ssh_password"),
        remote_bind_address=(config("db_host"), ssh_port),
        local_bind_address=("localhost", ssh_port),
    ):

        conn = psycopg2.connect(
            dbname=config("db_name"),
            user=config("db_user"),
            password=config("db_password"),
            port=config("db_port"),
            host="localhost",
            connect_timeout=3,
        )
        logging.debug("Connected to database")
        cur = conn.cursor()

        SQL_for_file_output = (
            "COPY (SELECT situs_address,geoid_cnty FROM corelogic_usda.current_tax_200627_latest_all_add_vars_add_progs_geom_blk WHERE geoid_cnty = '%s') TO STDOUT DELIMITER ',' CSV HEADER;"
            % county_fips
        )
        temp_path = os.path.join(temp_dir, "%s.csv" % county_fips)

        with open(temp_path, "w") as f_output:
            cur.copy_expert(SQL_for_file_output, f_output)

        # save csv to file given county_fips code
        logging.debug('Using temporary path" %s' % temp_path)
        # https://github.com/psycopg/psycopg2/issues/984

        logging.debug("File saved to path")
        cur.close()
        conn.close()

    return pd.read_csv(
        temp_path,
    )


def run(county_fip, output_file, temp_dir, force):
    warnings.filterwarnings("ignore")
    state_fips = pd.read_csv(
        "https://raw.githubusercontent.com/uva-bi-sdad/national_address_database/main/data/fips_state.csv",
        dtype={"fips": object},
    )
    state = state_fips[state_fips["fips"] == county_fip[:2]]["state"].values[0]
    state_abbr = (
        state_fips[state_fips["fips"] == county_fip[:2]]["abbr"].values[0].upper()
    )
    county_fips = pd.read_csv(
        "https://github.com/uva-bi-sdad/national_address_database/raw/main/data/fips_county.csv",
        dtype={"fips": object},
    )
    logging.info(county_fips[county_fips["fips"] == county_fip])
    county = county_fips[county_fips["fips"] == county_fip].values[0][1]
    logging.info("County: %s" % county)

    df = download_data(county_fip, temp_dir)
    assert not df is None, "Data frame returned is None"
    df = df.dropna()
    bdf = pd.DataFrame()

    logging.info("Length of df: %s" % len(df))
    # Clean up the csv and export the results

    logging.info("Cleaning data frame: ")
    bdf["street"] = df["situs_address"].apply(lambda x: x.split(" %s" % state_abbr)[0])
    bdf["county"] = county
    bdf["state"] = state_abbr
    bdf["zip"] = df["situs_address"].apply(lambda x: x.split("%s " % state_abbr)[-1])

    bdf.to_csv(output_file, index=False)
    return os.path.isfile(output_file)


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Given a corelogic template, convert to a csv that can be queried to the fcc. First downloads raw data into the temporary directory, then transforms it to a cleaned format in the output filepath"
    )
    parser.add_argument(
        "-i",
        "--input_county_fips",
        nargs="+",
        help="A list of county fip(s) to filter from the database",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="The output directory for the csvs",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--temp_dir",
        type=str,
        help="The temporary directory to store raw downloaded files",
        default=".temp",
        required=False,
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
        help="Whether or not to override the output file, if it already exists",
        required=False,
        default=False,
    )

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    for fip in args.input_county_fips:
        assert len(fip) == 5, "[%s] not 5 characters long" % (fip)

    if not os.path.isdir(args.temp_dir):  # if temp dir is not a dir, create a dir
        os.mkdir(args.temp_dir)

    for fip in tqdm(args.input_county_fips):
        output_filepath = os.path.join(args.output_dir, "%s.csv.xz" % fip)
        if not args.force and os.path.isfile(output_filepath):
            logging.info(
                "%s already exist and no force flag. Skipping..." % output_filepath
            )

            continue
        success = run(
            fip,
            output_filepath,
            args.temp_dir,
            args.force,
        )
        print("[%s] Output to %s successful" % (success, output_filepath))

    # Cleaning up temporary directory and its contents
    shutil.rmtree(args.temp_dir)


if __name__ == "__main__":
    main()

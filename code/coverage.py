import pandas as pd
import os
import argparse
import logging
from tqdm import tqdm


def calculate_coverage(input_filepath, data_dir):
    cdf = pd.read_csv(input_filepath)

    existing_counties = [
        v[:-7].replace("_county", "") for v in os.listdir(data_dir)
    ]  # assuming .csv.xz, which is 7 characters

    results = {}

    for state in cdf["state"]:
        sdf = cdf[cdf["state"] == state].copy()
        sdf["name"] = sdf["abbr"] + "_" + sdf["county"]
        sdf["name"] = sdf["name"].apply(lambda x: x.replace("_county", ""))

        coverage = sdf[sdf["name"].isin(existing_counties)].copy()
        results[state] = int(len(coverage) / len(sdf) * 100)

    return results


def update_readme(readme_filepath, results):
    with open(readme_filepath, "r") as f:
        contents = f.readlines()

    keys = sorted(results)
    insert = ""
    for key in tqdm(keys):
        insert += "%s: ![](https://geps.dev/progress/%s)\n" % (key, results[key])

    del contents[2:55]

    contents.insert(2, insert)

    with open(readme_filepath, "w") as f:
        contents = "".join(contents)
        f.write(contents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given a csv, create an ouput directory with batched fcc area geocoding queries. Assumes that the csv is already formatted to fcc area api standards. Note if the force flag is false, the process will continue where it left off as long as the ouput_dir is the same."
    )

    parser.add_argument(
        "-i",
        "--input_state_county_csv",
        type=str,
        help="The input csv with state county data assumed to cover the entire US",
        required=True,
    )

    parser.add_argument(
        "-r",
        "--input_readme",
        type=str,
        help="The input readme path to routinely update",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--input_data_dir",
        type=str,
        help="The input directory of csv.xz that represents collected address data per state per county",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show debugging outputs",
        action=argparse.BooleanOptionalAction,
    )

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    assert os.path.isdir(args.input_data_dir)
    assert os.path.isfile(args.input_state_county_csv)
    assert os.path.isfile(args.input_readme)
    results = calculate_coverage(args.input_state_county_csv, args.input_data_dir)

    update_readme(args.input_readme, results)

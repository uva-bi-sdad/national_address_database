import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import os


def main():
    """
    After calling download_all_shapefiles, loop through the files and create a csv containing all the county and block information, and saving it to data/blocks.csv.xz
    """
    dir = "../data/shapefiles"
    total_set = set()
    pbar = tqdm(os.listdir(dir))
    for f in pbar:
        pbar.set_description("Adding: %s" % f)
        if not f.split(".")[-1] == "zip":  # skip not zip files
            continue
        filepath = os.path.join(dir, f)
        df = gpd.read_file(filepath)
        total_set |= set(df["GEOID20"])
        pbar.set_description("Total set length: %s" % len(total_set))

    df = pd.DataFrame()
    df["GEOID20"] = list(total_set)
    df = df.sort_values(by="GEOID20")
    df.to_csv("../data/blocks.csv.xz", index=False)
    return df


if __name__ == "__main__":
    df = main()
    print(df)
    assert (
        len(df) == 8174955  # excluding island areas
    )  # tally from census tallies (https://www.census.gov/geographies/reference-files/time-series/geo/tallies.html)

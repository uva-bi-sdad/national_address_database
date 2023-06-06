import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import os


def main():
    """
    After calling download_all_shapefiles, loop through the files and create a csv containing all the county and block information, and saving it to data/blocks.csv.xz
    """
    dir = "../data/shapefiles"
    dfs = []
    for f in tqdm(os.listdir(dir)):
        if not f.split(".")[-1] == "zip":  # skip not zip files
            continue
        filepath = os.path.join(dir, f)
        df = gpd.read_file(filepath)
        df = df[["GEOID20"]]
        dfs.append(df)

    fdf = pd.concat(dfs)
    fdf = fdf.sort_values(by="GEOID20")
    fdf.to_csv("../data/blocks.csv.xz", index=False)


if __name__ == "__main__":
    main()

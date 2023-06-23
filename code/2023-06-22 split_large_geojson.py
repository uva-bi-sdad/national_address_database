import pandas as pd
import os
from tqdm import tqdm
import geopandas as gpd
import matplotlib as mpl

if __name__ == "__main__":
    print("Converting to geojson")
    valid_files = [
        os.path.join("../data/shapes", file)
        for file in os.listdir("../data/shapes")
        if file.split(".")[-1] == "geojson"
    ]

    for county_file in tqdm(sorted(valid_files)):
        if not os.path.isfile(county_file):
            continue

        mb = os.path.getsize(county_file) >> 20

        if not mb > 50:
            continue
            # skip smaller files

        num_to_split = int(mb / 40) + 1
        county_shape_df = gpd.read_file(county_file)
        chunk_size = int(len(county_shape_df) / num_to_split) + 1

        for i in range(num_to_split):
            # print(county_file)
            county = county_file.split("../data/shapes/")[1].split(".")[0]
            updated_name = county_file.split(".geojson")[0] + "_%s" % i + ".geojson"
            pdf = county_shape_df[(i * chunk_size) : ((i + 1) * chunk_size)]
            # print(pdf)
            pdf.to_csv(updated_name)
            # print("-" * 80)
        os.remove(county_file)  # remove the original file after splitting

import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests

# wget -P ../data/shapefiles/ https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_13121_tabblock20.zip


def main():
    # identify all files to download
    r = requests.get(
        "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/"
    )
    soup = BeautifulSoup(r.content, "html.parser")
    counties = []
    for a in soup.find_all("a", href=True):
        if len(a["href"]) == 28 and a["href"].split(".")[-1] == "zip":
            print(a["href"])
            counties.append(a["href"])

    for county in tqdm(counties):
        os.system(
            "wget -P ../data/shapefiles/https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/%s"
            % county
        )


if __name__ == "__main__":
    main()

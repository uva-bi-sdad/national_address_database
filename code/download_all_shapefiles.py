import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import signal, os

"""
Download all county blocks
"""

# wget -P ../data/shapefiles/ https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_13121_tabblock20.zip


def handler(signum, frame):
    print("Signal handler called with signal", signum)


def main():
    os.system("mkdir -p ../data/shapefiles/")

    # identify all files to download
    r = requests.get(
        "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/"
    )
    soup = BeautifulSoup(r.content, "html.parser")
    counties = []
    for a in soup.find_all("a", href=True):
        if a["href"].split(".")[-1] == "zip":
            print(a["href"])
            counties.append(a["href"])

    for county in tqdm(counties):
        if len(county.split("_")[2]) != 5:  # only donwload county files
            continue
        os.system(
            "wget -nc -P ../data/shapefiles/ https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/%s"
            % county
        )
        filepath = os.path.join("../data/shapefiles", county)
        assert os.path.isfile(filepath), filepath + " was not exported"


if __name__ == "__main__":
    # Set the signal handler
    signal.signal(signal.SIGINT, handler)
    main()

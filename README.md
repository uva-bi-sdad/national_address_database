## Data Sources
- We extracted data from the [Natiaonl Address Database](https://www.transportation.gov/gis/national-address-database)
- We work on filling the gaps for missing information using other data sources

## Example Usage

1. Query the URL with the five-digit county fips code:
```python
import pandas as pd

df = pd.read_csv("https://github.com/uva-bi-sdad/national_address_database/raw/main/data/address/01001.csv.xz", dtype={'GEOI20':object})
```

Results: 
```python
                                            address         GEOID20  longitude   latitude
0        521 mossy oak ridge, prattville, al, 36066  10010205033012 -86.429760  32.468279
1      209 high pointe ridge, prattville, al, 36066  10010205033012 -86.430169  32.470367
2      208 high pointe ridge, prattville, al, 36066  10010205033012 -86.430166  32.470378
3         101 lake haven way, prattville, al, 36066  10010205033012 -86.433429  32.469669
4         103 lake haven way, prattville, al, 36066  10010205033012 -86.433428  32.469648
...                                             ...             ...        ...        ...
16589          422 oregon ct, prattville, al, 36067  10010201002004 -86.489276  32.476746
16590            422 utah ct, prattville, al, 36067  10010201002004 -86.489308  32.477721
16591          827 durden rd, prattville, al, 36067  10010201002004 -86.484975  32.493014
16592         1031 durden rd, prattville, al, 36067  10010201002004 -86.483758  32.493887
16593        707 windmill dr, prattville, al, 36067  10010201002004 -86.489679  32.492366

[16594 rows x 4 columns]
```

## Verification
To verify that the appended addresses are accurate, we can cross check it against the census geocoder and see if there are components in the 'matchedAddress' key

```python
import requests

test_address = df.iat[0,0] # '521 mossy oak ridge, prattville, al, 36066'
r = requests.get('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=%s&benchmark=2020&format=json' % test_address).json()
print(len(r.json()['result']['addressMatches']) > 0)
print(r)  
```

```python
{'result': {'input': {'address': {'address': '521 mossy oak ridge, prattville, al, 36066'}, 'benchmark': {'isDefault': False, 'benchmarkDescription': 'Public Address Ranges - Census 2020 Benchmark', 'id': '2020', 'benchmarkName': 'Public_AR_Census2020'}}, 'addressMatches': [{'tigerLine': {'side': 'L', 'tigerLineId': '2838521'}, 'coordinates': {'x': -86.42976028846772, 'y': 32.46827875597135}, 'addressComponents': {'zip': '36066', 'streetName': 'MOSSY OAK', 'preType': '', 'city': 'PRATTVILLE', 'preDirection': '', 'suffixDirection': '', 'fromAddress': '519', 'state': 'AL', 'suffixType': 'RIDGE', 'toAddress': '599', 'suffixQualifier': '', 'preQualifier': ''}, 'matchedAddress': '521 MOSSY OAK RIDGE, PRATTVILLE, AL, 36066'}]}}
```

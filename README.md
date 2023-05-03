# national_address_database

alabama: ![](https://geps.dev/progress/85)
alaska: ![](https://geps.dev/progress/6)
arizona: ![](https://geps.dev/progress/93)
arkansas: ![](https://geps.dev/progress/100)
california: ![](https://geps.dev/progress/1)
colorado: ![](https://geps.dev/progress/68)
connecticut: ![](https://geps.dev/progress/88)
delaware: ![](https://geps.dev/progress/75)
district_of_columbia: ![](https://geps.dev/progress/0)
florida: ![](https://geps.dev/progress/10)
georgia: ![](https://geps.dev/progress/0)
hawaii: ![](https://geps.dev/progress/0)
idaho: ![](https://geps.dev/progress/0)
illinois: ![](https://geps.dev/progress/2)
indiana: ![](https://geps.dev/progress/88)
iowa: ![](https://geps.dev/progress/87)
kansas: ![](https://geps.dev/progress/80)
kentucky: ![](https://geps.dev/progress/20)
louisiana: ![](https://geps.dev/progress/10)
maine: ![](https://geps.dev/progress/94)
maryland: ![](https://geps.dev/progress/56)
massachusetts: ![](https://geps.dev/progress/93)
michigan: ![](https://geps.dev/progress/1)
minnesota: ![](https://geps.dev/progress/12)
mississippi: ![](https://geps.dev/progress/0)
missouri: ![](https://geps.dev/progress/19)
montana: ![](https://geps.dev/progress/96)
nebraska: ![](https://geps.dev/progress/0)
nevada: ![](https://geps.dev/progress/0)
new_hampshire: ![](https://geps.dev/progress/0)
new_jersey: ![](https://geps.dev/progress/95)
new_mexico: ![](https://geps.dev/progress/94)
new_york: ![](https://geps.dev/progress/100)
north_carolina: ![](https://geps.dev/progress/98)
north_dakota: ![](https://geps.dev/progress/85)
ohio: ![](https://geps.dev/progress/98)
oklahoma: ![](https://geps.dev/progress/32)
oregon: ![](https://geps.dev/progress/0)
pennsylvania: ![](https://geps.dev/progress/22)
rhode_island: ![](https://geps.dev/progress/83)
south_carolina: ![](https://geps.dev/progress/6)
south_dakota: ![](https://geps.dev/progress/8)
tennessee: ![](https://geps.dev/progress/98)
texas: ![](https://geps.dev/progress/87)
utah: ![](https://geps.dev/progress/100)
vermont: ![](https://geps.dev/progress/93)
virginia: ![](https://geps.dev/progress/97)
washington: ![](https://geps.dev/progress/17)
west_virginia: ![](https://geps.dev/progress/0)
wisconsin: ![](https://geps.dev/progress/89)
wyoming: ![](https://geps.dev/progress/37)


## Data Sources
- We extracted data from the [Natiaonl Address Database](https://www.transportation.gov/gis/national-address-database)
- We work on filling the gaps for missing information using other data sources

## Example Usage

1. Download a [json list of state_counties](https://raw.githubusercontent.com/uva-bi-sdad/national_address_database/main/data/state_county.json) and reference to their names
2. Query the file name via `https://github.com/uva-bi-sdad/national_address_database/raw/main/data/<insert file name here>`

In Python
```python
import pandas as pd

df = pd.read_csv("https://github.com/uva-bi-sdad/national_address_database/raw/main/data/va_arlington.csv.xz")
```
Results: 
```python
      state     county    zip  longitude   latitude                                       address
0        va  arlington  22201 -77.089851  38.873820     1 north fenwick street,arlington,va,22201
1        va  arlington  22203 -77.101126  38.871177         1 north glebe road,arlington,va,22203
2        va  arlington  22203 -77.122787  38.866952     1 north granada street,arlington,va,22203
3        va  arlington  22203 -77.132594  38.866696     1 north madison street,arlington,va,22203
4        va  arlington  22203 -77.133909  38.866673  1 north manchester street,arlington,va,22203
...     ...        ...    ...        ...        ...                                           ...
43681    va  arlington  22204 -77.086141  38.850972  2021 south kenmore street,arlington,va,22204
43682    va  arlington  22205 -77.129933  38.870417      5741 4th street north,arlington,va,22205
43683    va  arlington  22205 -77.130048  38.870387      5743 4th street north,arlington,va,22205
43684    va  arlington  22209 -77.072629  38.895806       1818 fort myer drive,arlington,va,22209
43685    va  arlington  22207 -77.115376  38.912716     4110 31st street north,arlington,va,22207

[43686 rows x 6 columns]
```
3. If necessary, you can also use [state fips](https://raw.githubusercontent.com/uva-bi-sdad/national_address_database/main/data/fips_state.csv) and [county fips](https://raw.githubusercontent.com/uva-bi-sdad/national_address_database/main/data/fips_county.csv.xz) prepared in this repo

## Verification
To verify that the appended addresses are accurate, we can cross check it against the census geocoder and see if there are components in the 'matchedAddress' key

```python
import requests

formal_address = '210 N Barton St, Arlington, VA 22201'
r = requests.get('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=%s&benchmark=2020&format=json' % formal_address).json()
print(len(r.json()['result']['addressMatches']) > 0)
print(r)  
```

```python
{'result': {'input': {'address': {'address': '210 N Barton St, Arlington, VA 22201'
            }, 'benchmark': {'isDefault': False, 'benchmarkDescription': 'Public Address Ranges - Census 2020 Benchmark', 'id': '2020', 'benchmarkName': 'Public_AR_Census2020'
            }
        }, 'addressMatches': [
            {'tigerLine': {'side': 'L', 'tigerLineId': '76479213'
                }, 'coordinates': {'x': -77.08608052539722, 'y': 38.87763620769999
                }, 'addressComponents': {'zip': '22201', 'streetName': 'BARTON', 'preType': '', 'city': 'ARLINGTON', 'preDirection': 'N', 'suffixDirection': '', 'fromAddress': '200', 'state': 'VA', 'suffixType': 'ST', 'toAddress': '228', 'suffixQualifier': '', 'preQualifier': ''
                }, 'matchedAddress': '210 N BARTON ST, ARLINGTON, VA,
                22201'
            }
        ]
    }
}
```

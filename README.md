# national_address_database

I extracted into a csv format, addresses from the [National Address Database](https://www.transportation.gov/mission/open/gis/national-address-database/national-address-database-nad-disclaimer)

## Example Usage

1. Download a [json list of state_counties](https://raw.githubusercontent.com/uva-bi-sdad/national_address_database/main/data/state_county.json) and reference to their names
2. Query `https://github.com/uva-bi-sdad/national_address_database/raw/main/data/<insert file name here>` the name

In Python
```python
import pandas as pd

df = pd.read_csv("https://github.com/uva-bi-sdad/national_address_database/raw/main/data/VA_Arlington.csv.xz")
```
Results: 
```python
      state     county      zip  ...  longitude   latitude                  address
0        VA  Arlington  22201.0  ... -77.089851  38.873820       1 Fenwick VA 22201
1        VA  Arlington  22203.0  ... -77.101126  38.871177         1 Glebe VA 22203
2        VA  Arlington  22203.0  ... -77.122787  38.866952       1 Granada VA 22203
3        VA  Arlington  22203.0  ... -77.132594  38.866696       1 Madison VA 22203
4        VA  Arlington  22203.0  ... -77.133909  38.866673    1 Manchester VA 22203
...     ...        ...      ...  ...        ...        ...                      ...
43681    VA  Arlington  22204.0  ... -77.086141  38.850972    2021 Kenmore VA 22204
43682    VA  Arlington  22205.0  ... -77.129933  38.870417        5741 4Th VA 22205
43683    VA  Arlington  22205.0  ... -77.130048  38.870387        5743 4Th VA 22205
43684    VA  Arlington  22209.0  ... -77.072629  38.895806  1818 Fort Myer VA 22209
43685    VA  Arlington  22207.0  ... -77.115376  38.912716       4110 31St VA 22207

[43686 rows x 8 columns]
```

Columns:
```python
df.columns
Index(['state', 'county', 'zip', 'add_number', 'street_name', 'longitude',
       'latitude', 'address'],
      dtype='object')
```

## Potentially useful for next steps?
- Might need to reference the [census geocoder](https://geocoding.geo.census.gov/geocoder/geographies/) and evaluate the block id so that you can consolidate different approaches
- [Schema for the national address database](https://www.transportation.gov/sites/dot.gov/files/docs/mission/gis/national-address-database/308816/nad-schema-v1.pdf)
- [API to reverse long lat into area information](https://geo.fcc.gov/api/census/#!/area/get_area)

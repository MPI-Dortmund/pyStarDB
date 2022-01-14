[![pipeline status](https://gitlab.gwdg.de/mpi-dortmund/sphire/pyStarDB/badges/master/pipeline.svg)](https://gitlab.gwdg.de/mpi-dortmund/sphire/pyStarDB/-/commits/master)
[![coverage report](https://gitlab.gwdg.de/mpi-dortmund/sphire/pyStarDB/badges/master/coverage.svg)](https://gitlab.gwdg.de/mpi-dortmund/sphire/pyStarDB/-/commits/master) 

# pyStarDB
Star file python package

## Basic usage
## Import package
```
from pyStarDB import sp_pystardb as star
import pandas as pd
```
## Read a starfile

```python
sfile = star.StarFile(path)
data: pd.DataFrame = sfile[''] # In case the data block has no name (i.e data_) the key for it is empty
```

Individual columns can be accessed with:

```python
column_data = data["column_name"]
```

## Write a star file
I assume that you have a pandas dataframe `data` that you want to write to disk:
```python
new_sfile = star.StarFile("new_file.star")
new_sfile.update('block_name', data, loop=True)
new_sfile.write_star_file(overwrite=True)
```
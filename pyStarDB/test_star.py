
import pandas as pd
import sp_pystardb as pystar

a = pd.DataFrame([[0, 1], [2, 3]], columns=['col1', 'col2'])
b = pystar.StarFile('name.star')
b['my_tag'] = a
b.write_star_file()



import pandas as pd
import sp_pystardb as pystar

# a = pd.DataFrame([[0, 1], [2, 3]], columns=['_col1', '_col2'])
# b = pystar.StarFile('name.star')
# b.update('my_tag',a,True)
# b.update('my_tag_2',a,True)
# b.write_star_file()


d = pystar.StarFile('ActinLifeAct_000722.star')
data = d.imported_content
print("Hello")


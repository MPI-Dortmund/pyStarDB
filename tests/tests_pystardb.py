import unittest
import os

class MyTestCase(unittest.TestCase):

    def test_file_is_written_loop_notag(self):
        import pandas as pd
        from pyStarDB import sp_pystardb as pystar
        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        a = pd.DataFrame([[0, 1], [2, 3]], columns=['col1', 'col2'])
        b = pystar.StarFile('name.star')
        b.update('', a, True)
        b.write_star_file()
        exists = os.path.exists('name.star')
        os.remove("name.star")

        self.assertTrue(exists,"File (loop) was not written")

    def test_file_is_written_no_loop_notag(self):
        import pandas as pd
        from pyStarDB import sp_pystardb as pystar

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        a = pd.DataFrame([[0, 1], [2, 3]], columns=['col1', 'col2'])
        b = pystar.StarFile('name.star')
        b.update('', a, False)
        b.write_star_file()
        exists = os.path.exists('name.star')

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        self.assertTrue(exists,"File (no-loop) was not written")

    def test_create_and_read(self):
        import pandas as pd
        from pyStarDB import sp_pystardb as pystar

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        a = pd.DataFrame([[0, 1], [2, 3]], columns=['_col1', '_col2'])
        b = pystar.StarFile('name.star')
        b.update('', a, True)
        b.write_star_file()

        c = pystar.StarFile('name.star')

        is_equal_col1 = a['_col1'].equals(c.imported_content['']['_col1'])
        is_equal_col2 = a['_col2'].equals(c.imported_content['']['_col2'])

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        self.assertTrue(is_equal_col1 and is_equal_col2,"Write / Read test failed")



if __name__ == '__main__':
    unittest.main()

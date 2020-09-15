import unittest
import os

class MyTestCase(unittest.TestCase):

    def test_file_is_written_loop(self):
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

    def test_file_is_written_no_loop(self):
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


if __name__ == '__main__':
    unittest.main()

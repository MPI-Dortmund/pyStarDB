import unittest
import os
import pandas as pd
from pyStarDB import sp_pystardb as pystar


class MyTestCase(unittest.TestCase):

    def test_file_is_written_loop_notag(self):
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



    #Test to fix the tag bug
    def test_create_and_read_tag(self):

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        a = pd.DataFrame([[0, 1], [2, 3]], columns=['_col1', '_col2'])
        b = pystar.StarFile('name.star')
        b.update('my_tag', a, True)
        b.write_star_file()

        c = pystar.StarFile('name.star')

        is_equal_col1 = a['_col1'].equals(c.imported_content['my_tag']['_col1'])
        is_equal_col2 = a['_col2'].equals(c.imported_content['my_tag']['_col2'])

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        self.assertTrue(is_equal_col1 and is_equal_col2,"Write / Read test failed")

    def test_create_and_read_tag_multitag(self):

        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        a = pd.DataFrame([[0, 1], [2, 3]], columns=['_col1', '_col2'])
        a2 = pd.DataFrame([[4, 5], [6, 7]], columns=['_col1', '_col2'])
        b = pystar.StarFile('name.star')
        b.update('my_tag', a, True)
        b.update('my_tag_2', a2, True)
        b.write_star_file()

        c = pystar.StarFile('name.star')

        is_equal_col1_mytag = a['_col1'].equals(c.imported_content['my_tag']['_col1'])
        is_equal_col2_mytag = a['_col2'].equals(c.imported_content['my_tag']['_col2'])
        is_equal_col1_mytag2 = a2['_col1'].equals(c.imported_content['my_tag_2']['_col1'])
        is_equal_col2_mytag2 = a2['_col2'].equals(c.imported_content['my_tag_2']['_col2'])
        all_is_equal = is_equal_col1_mytag and is_equal_col2_mytag and is_equal_col1_mytag2 and is_equal_col2_mytag2
        try:
            os.remove("name.star")
        except FileNotFoundError:
            pass

        self.assertTrue(all_is_equal,"Write / Read test failed")



if __name__ == '__main__':
    unittest.main()

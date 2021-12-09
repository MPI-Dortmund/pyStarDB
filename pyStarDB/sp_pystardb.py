# Author: Markus Stabrin 2020 (markus.stabrin@mpi-dortmund.mpg.de)
# Author: Adnan Ali 2020 (adnan.ali@mpi-dortmund.mpg.de)
# Author: Thorsten Wagner 2020 (thorsten.wagner@mpi-dortmund.mpg.de)
# Author: Tapu Shaikh 2020 (tapu.shaikh@mpi-dortmund.mpg.de)

# Copyright (c) 2020- Max Planck Institute of Molecular Physiology

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this program and associated documentation files (the "program"), to deal
# in the program without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the program, and to permit persons to whom the program is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the program.
#
# THE PROGRAM IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# PROGRAM.


import pandas
import re
import argparse
import os
from io import StringIO
import sys
import numpy as np
"""
Base Class for Starfile format. Will be able to handle data
"""


class StarFile(dict):
    """
    Functions:
        __init__() : Initializes
        analyse_star_file(() : Determines line numbers for each block of data
        read_tag() : Populates 'imported_content' with data
        read_with_loop() :  Reads data when block starts with 'loop_'
        read_without_loop() : Reads data when block doesn't start with 'loop_'
        __getitem__() : Returns data
        __setitem__() : Imports data
        write_star_file() : Writes data to disk for specified tag(s)

    Variables:
        star_file : Name of STAR file
        imported_content : Data, as a pandas DataFrame
        line_dict : (dictionary) Line numbers for each section of each block
    """

    def __init__(self, star_file : str):
        """
        :param star_file:
        """
        self.star_file = star_file
        # self.imported_content = {}
        self.line_dict = {}
        self.star_content = ''

        try:
            self.analyse_star_file()
        except Exception as e:
            if str(e) == "Star file not provided or corrupted":
                raise
            elif str(e) == "No column data detected":
                raise
            elif str(e) == "'NoneType' object has no attribute 'start'":
                raise
            elif str(e) == "Unable to grab the header information and column information":
                raise
            else:
                pass

        self.sphire_keys = {
            "_rlnMicrographName"    : "ptcl_source_image",
        }
        self.special_keys = {'ctf', 'xform.projection', 'ptcl_source_coord',
                             'xform.align2d', "data_path"}

        self.ignored_keys = {'HostEndian', 'ImageEndian', 'MRC.maximum', 'MRC.mean', 'MRC.minimum', 'MRC.mx',
                             'MRC.my', 'MRC.mz', 'MRC.nlabels', 'MRC.nsymbt', 'MRC.nx', 'MRC.nxstart', 'MRC.ny',
                             'MRC.nystart', 'MRC.nz', 'MRC.nzstart', 'MRC.rms', 'MRC.xlen', 'MRC.ylen', 'MRC.zlen',
                               'datatype', 'is_complex',  'MRC.label1', 'changecount', "is_complex_ri", "ctf_applied",
                             "resample_ratio", "originalid", 'ptcl_source_coord_id',
                             'is_complex_x', 'is_fftodd', 'is_fftpad', 'is_intensity', 'maximum', 'mean',
                             'mean_nonzero', 'ptcl_source_apix', 'apix_x', 'apix_y', 'apix_z', 'nx', 'ny', 'nz',
                             'minimum', 'origin_x', 'origin_y', 'origin_z', 'sigma', 'sigma_nonzero',
                             'source_n', 'source_path', 'square_sum', 'ptcl_source_box_id',
                             'data_n','MRC.mapc', 'MRC.mapr', 'is_complex_x', 'is_complex',
                             'MRC.maps', 'MRC.alpha', 'MRC.beta', 'MRC.gamma', 'MRC.ispg', 'MRC.label0',
                             'MRC.machinestamp', 'npad', 'ptcl_source_apix', 'data_source'
                             }

    def analyse_star_file(self):
        """
        Populates self.line_dict with line numbers for each section of each block.
        line_dict : Dictionary whose keys are a block of the STAR file, with 'data_'
        removed (e.g., 'data_optics' -> 'optics')
        keys in each block:
            block : Line numbers for entire block
            header : Line numbers for header
            content : Line numbers for data
            is_loop : (boolean) Whether block starts with 'loop_'
        :return: nothing
        """

        with open(self.star_file) as read:
            # reading all the content of the star file. The reading part was modified so that
            # it is able to read thorsten previously generated star files.
            # They had a line space after header information thats why it was not able to read content
            # properly . Normally this is not allowed but as people are already using it thats why
            # we added this functionality also.
            content = ''.join([
                '\n{}\n'.format(_)
                if re.match('^data_([^\s]*)\s*$', _)
                else _
                for _ in read.readlines()
                if _.strip() and not _.startswith('#')
            ]) + '\n'
        self.star_content = StringIO(content)  # It makes a file out of string. Just convenient to reading
        # data of star file

        # WHen you deal with file objects you always need to reset the
        # memory buffer after every read
        self.star_content.seek(0)
        """
        Part of the code which tries to find out / match the keys starting with data_ 
        """
        # https://regex101.com/r/D7O06N/1

        data = self.star_content.read()
        if data.find('data_') == -1:
            raise TypeError("Star file not provided or corrupted")
        else:
            pass
        del data
        self.star_content.seek(0)

        for tag_match in re.finditer('^data_([^\s]*)\s*$', content, re.M):
            tag = tag_match.group(1)
            self.line_dict[tag] = {
                'block': [None, None],
                'header': [None, None],
                'content': [None, None],
                'is_loop': None,
            }

            current_flag = 0
            prev_content = content[:tag_match.start() + current_flag]
            current_content = content[tag_match.start() + current_flag:]
            current_flag += tag_match.start()

            # https://regex101.com/r/4o3dNy/1/
            self.line_dict[tag]['block'][0] = \
                len(re.findall('\n', prev_content)) + 1

            # https://regex101.com/r/h7Wm8y/2
            header_match = re.search(
                '((?:(?:loop_\s*)?^_.*$\r?\n?)+)',
                current_content,
                re.M
            )

            if header_match == None:
                raise TypeError("Unable to grab the header information and column information")

            prev_content = content[:header_match.start() + current_flag]
            current_content = content[header_match.start() + current_flag:]
            current_flag += header_match.start()

            self.line_dict[tag]['is_loop'] = header_match.group(1).startswith('loop_')
            # https://regex101.com/r/4o3dNy/1/
            self.line_dict[tag]['header'][0] = \
                len(re.findall('\n', prev_content)) + 1 + self.line_dict[tag]['is_loop']

            prev_content = content[:header_match.end() + current_flag - header_match.start()]
            current_content = content[header_match.end() + current_flag - header_match.start():]
            current_flag += header_match.end() - header_match.start()
            # https://regex101.com/r/4o3dNy/1/
            self.line_dict[tag]['header'][1] = \
                len(re.findall('\n', prev_content))

            if not self.line_dict[tag]['is_loop']:
                self.line_dict[tag]['content'] = self.line_dict[tag]['header']
            else:
                self.line_dict[tag]['content'][0] = self.line_dict[tag]['header'][1] + 1
                # https://regex101.com/r/HYnKMl/1
                newline_match = re.search('^\s*$', current_content, re.M)

                prev_content = content[:newline_match.start() + current_flag]
                current_content = content[newline_match.start() + current_flag:]
                current_flag += newline_match.start()

                # https://regex101.com/r/4o3dNy/1/
                self.line_dict[tag]['content'][1] = \
                    len(re.findall('\n', prev_content))

            self.line_dict[tag]['block'][1] = self.line_dict[tag]['content'][1]

            self.read_tag(tag, self.line_dict[tag])

            if len(self[tag].columns) == 0:
                raise TypeError("No column data detected")
            else:
                pass

    def read_tag(self, tag:str, line_dict:dict):
        """
        Populates self.imported_content with data.
        :param tag:
        :param line_dict:
        :return:
        """
        try:
            if not line_dict['is_loop']:
                data = self.read_without_loop(line_dict)
            else:
                data = self.read_with_loop(line_dict)
            self.__setitem__(tag, data)
        except Exception as e:
            print("Exception handled", e)
            return

    def read_with_loop(self, line_dict:dict):
        """
        Reads data when block starts with 'loop_'.
        :param line_dict:
        :return:
        """
        # When you deal with file objects you always need to reset the
        # memory buffer after every read
        self.star_content.seek(0)
        header_names = pandas.read_csv(
            self.star_content,
            usecols=[0],
            skiprows=line_dict['header'][0] - 1,
            nrows=line_dict['header'][1] - line_dict['header'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
            squeeze=True,
        )

        self.star_content.seek(0)
        return pandas.read_csv(
            self.star_content,
            index_col=None,
            names=header_names,
            skiprows=line_dict['content'][0] - 1,
            nrows=line_dict['content'][1] - line_dict['content'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
        )

    def read_without_loop(self, line_dict:dict):
        """
        Reads data when block doesn't start with 'loop_'.
        :param line_dict:
        :return:
        """
        # WHen you deal with file objects you always need to reset the
        # memory buffer after every read
        self.star_content.seek(0)
        return pandas.read_csv(
            self.star_content,
            index_col=0,
            names=['', '0'],
            skiprows=line_dict['content'][0] - 1,
            nrows=line_dict['content'][1] - line_dict['content'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
        ).transpose()

    # Never forget the concept of Recursion otherwise you will be doomed
    # This will haunt you forever
    # def __getitem__(self, tag):
    #     return self.__getitem__(tag)
    #
    # def __setitem__(self, tag, data):
    #     self.update(tag, data, True)

    def update(self, tag:str, value, loop=False):
        """
        Updates the value (int, float, dict, list, string) with a specific tag
        :param tag: the key of the database you want to update
        :param value:  the value you want to insert w.r.t key
        :param loop: state whether it is a single value (False) or not (True)
        :return: nothing
        """
        self[tag] = value
        self.line_dict.setdefault(tag, {})['is_loop'] = loop

    def get_ncolumns(self, tags=None):
        """
        Get the number of columns either from entire database or from a specific tag
        :param tags: if the given, then number of columns are w.r.t that tag
        :return: number of columns
        """
        new_tags = {}
        if tags == None:
            new_tags = self.keys()
        else:
            new_tags = [tags]

        if len(new_tags) > 1 and tags is None:
            raise Exception("More than one tags available")
        no_of_columns = 0
        # Go through each tag and get the number of columns.
        for idx, tag in enumerate(new_tags):
            no_of_columns += len(self[tag].columns)
        return no_of_columns

    def get_nrows(self, tags=None):
        """
        Get the number of rows either from entire database or from a specific tag
        :param tags: if the given, then number of columns are w.r.t that tag
        :return: number of rows
        """
        new_tags = {}
        if tags == None:
            new_tags = self.keys()
        else:
            new_tags = [tags]

        if len(new_tags) > 1 and tags is None:
            raise Exception("More than one tags available")
        no_of_rows = 0
        # Go through each tag and get the number of columns.
        for idx, tag in enumerate(new_tags):
            no_of_rows += len(self[tag].values)
        return no_of_rows

    def __add__(self, star_to_add):
        """
        It is to overide the + sign for adding to StarFile class
        e.g.    c = a+b  where a , b ,c are StarFile class
        :param star_to_add: list of StarFile class to add
        :return: new class
        """
        return self.add_star([self, star_to_add])

    def __iadd__(self, star_to_add):
        """
        It is to overide the += sign for adding to StarFile class
        e.g.    a+=b  where a , b  are StarFile class
        The data of b will be copied inside the a
        :param star_to_add: list of StarFile class to add
        :return: updated class
        """
        return self.add_star([self, star_to_add], return_cls=self)

    @staticmethod
    def add_star(star_to_add, return_cls=None, inc_list=None, exc_list=None, step=None):
        """
        Static method that performs the addition of all Starfile class
        :param star_to_add: list of Starfile class to add
        :param return_cls: in case if we want to overwrite/append the existing class
        :param inc_list: List pf particles to include from the final list
        :param exc_list: List of partocles to exclude from the final list
        :param step: In case of having steps within list of particles
        :return: Final StarFileclass
        """
        if return_cls == None:
            return_cls = StarFile(None)
        else:
            pass

        if isinstance(star_to_add, list):
            pass
        else:
            star_to_add = [star_to_add]

        star_to_add = [entry if isinstance(entry, StarFile)
                       else StarFile(entry)
                       for entry in star_to_add]

        for tag in star_to_add[0]:
            data = [
                starclass[tag].iloc[starclass.get_index(starclass[tag], inc_list, exc_list, step)].copy(deep=True)
                for starclass in star_to_add
                if starclass.is_loop(tag)
            ]
            new_df = pandas.concat(data,
                                   join='inner', ignore_index=True, copy=True)
            return_cls.update(tag, new_df, True)
        return return_cls

    @staticmethod
    def get_index(dataframe, inc_list=None, exc_list=None, step=None):
        """
        Static method use to find the specific index in case any of the options are provided
        :param dataframe:  Dataframes of the Starfile class
        :type dataframe:  pandas.DataFrame
        :param inc_list:  List pf particles to include from the final list
        :param exc_list: List of partocles to exclude from the final list
        :param step:  In case of having steps within list of particles
        :return: index
        """

        assert len([entry for entry in [None, None, [0, 2]] if entry is not None]) in (0, 1), \
            "You can only provide one of the options for [inc_list, exc_list, step]"

        if step is not None:
            if len(step) == 2:
                nima = len(dataframe.index)
            elif len(step) == 3:
                nima = min(step[2], nrows)
            else:
                assert False, ('Wrong step values provided, please correct them. '
                               'Length of the tuple needs to be 2 or 3.')

            inc_list = list(range(step[0], nima - 1, step[1]))

        if inc_list is not None:
            index = dataframe.index[inc_list]
        elif exc_list is not None:
            index = dataframe.index.difference(exc_list)
        else:
            index = dataframe.index
        return index

    def is_loop(self, tag):
        """
        Check if it is a loop of values or single value
        :param tag: string value that is to be checked
        :return: True/False or None depending on the tag
        """
        try:
            return self.line_dict[tag]['is_loop']
        except KeyError:
            return None

    def get(self, tag):
        """
        Get the dictionary of a particular tag
        :param tag:
        :return: Dictionary with all the values from that tag
        """
        return self[tag].to_dict()

    def set(self, tag, dicta):
        """
        Set the value (dictionary) of a particle tag
        :param tag: string value that is to be set
        :param dicta: dictionary
        :return: Updated starfile
        """
        return self.update(tag, dicta, True)

    def write_star_file(self, out_star_file=None, tags=None, overwrite=False):
        """
        Write starfile with all the data inside the current starfile class
        :param out_star_file: Name of the starfile to be written
        :param tags: In case you only to write specific keys, can be single string or list of strings
        :param overwrite: Whether to overwrite the existing data in the starfile
        :return: None
        """
        # in case if the new file is not given and wants to overwrite the existing file
        if out_star_file == None:
            out_star_file = self.star_file

        # if file already exists and you dont want to overwrite it
        if os.path.exists(out_star_file) and overwrite == False:
            raise FileExistsError
            return

        # Gets all the tags from star database if they are not given by the user
        if tags == None:
            tags = self.keys()
        # If a single string is provided rather than a list, make it a list
        elif isinstance(tags, str):
            tags = [tags]

        # Go through each tag and load the dataframe in df.
        for idx, tag in enumerate(tags):
            if idx == 0:
                mode = 'w'
            else:
                mode = 'a'

            df = self[tag]

            # print(idx, tag, df)

            try:
                is_loop = self.line_dict[tag]['is_loop']
            except:
                is_loop = False

            # if it is continuous data then write the header information first and then all the data.
            export_header = '\ndata_{}\n'.format(tag)
            if is_loop:
                export_header += '\nloop_\n' + '\n'.join([
                    '{} #{}'.format(entry, idx)
                    for idx, entry
                    in enumerate(df, 1)
                ])

            with open(out_star_file, mode) as write:
                write.write(f'{export_header}\n')

            with open(out_star_file, 'a') as file:
                file.write( create_formatted_data_frame(df, is_loop) )
                file.write( '\n' )
            #df.to_csv(out_star_file, sep=' ', header=False, index=not is_loop, mode='a', na_rep='<NA>')

def create_formatted_data_frame(data_frame, is_loop):
    """
    Format the data frame with ints and floats right aligned and the rest left aligned.
    :data_frame: Data frame to format
    :is_loop: If the data frame represents a loop or not
    :return: formatted data frame
    """
    out_fmt = []
    if is_loop:
        current_data_frame = data_frame.copy()
        for column_name in current_data_frame:
            dtype = current_data_frame[column_name].dtypes
            if np.issubdtype(dtype, np.integer) or np.issubdtype(dtype, np.floating):
                # Get the maximum length of characters before the comma for good alignment
                length = max(map(len, map(str, map(int, current_data_frame[column_name]))))
                align = ' '
                if np.issubdtype(dtype, np.floating):
                    formatter = '.6f'
                    conversion_func = float
                    # In float fmt, the number before the dot includes all characters
                    length += 7
                else:
                    formatter = 'd'
                    conversion_func = int
                # Add an extra whitespace before numbers for better readability
                length += 1
            else:
                align = ' <'
                length = max(map(len, map(str, current_data_frame[column_name])))
                formatter = 's'
                conversion_func = str

            out_format = f"{{:{align}{length}{formatter}}}"
            out_fmt.append((out_format, conversion_func))
    else:
        # Aligned the left column to the left and the right column to the right
        current_data_frame = data_frame.T.copy()
        length_index = max(map(len, map(str, current_data_frame.index)))
        length_data = max(map(len, map(str, current_data_frame.iloc[:, 0])))
        out_fmt = [
            (f"{{:<{length_index+2}s}}", str),
            (f"{{: >{length_data}s}}", str),
            ]

    output = []
    # Remove the header labels for an aligned to_string
    current_data_frame.columns = ['' for _ in current_data_frame.columns]
    for line in current_data_frame \
            .to_string(header=True, index=not is_loop, na_rep='<NA>') \
            .splitlines():
        if not line.strip():
            continue

        output.append(
            ' '.join([
                out_fmt[idx][0].format(out_fmt[idx][1](entry))
                for idx, entry
                in enumerate(line.split())
                ])
            )
    return '\n'.join(output)

def sphire_header_magic(tag, special_keys=None):
    """
    Returns the star_format key which is similar to sphire_format key
    :param tag: key to be checked
    :param special_keys: In case special keys are pass
    :return: star_format key
    """
    star_translation_dict = {
        "ptcl_source_image": "_rlnMicrographName",
        "phi": "_rlnAngleRot",
        "theta": "_rlnAngleTilt",
        "psi": "_rlnAnglePsi",
        "voltage": "_rlnVoltage",
        "cs": "_rlnSphericalAberration",
        "bfactor": "_rlnCtfBfactor",
        "ampcont": "_rlnAmplitudeContrast",
        "apix": "_rlnDetectorPixelSize",
        "tx": "_rlnOriginX",
        "ty": "_rlnOriginY",
        "_rlnMagnification": "_rlnMagnification",
        "_rlnDefocusU": "_rlnDefocusU",
        "_rlnDefocusV": "_rlnDefocusV",
        "_rlnDefocusAngle": "_rlnDefocusAngle",
        "_rlnCoordinateX": "_rlnCoordinateX",
        "_rlnCoordinateY": "_rlnCoordinateY",
        "ISAC_class_id": "_rlnClassNumber",
    }

    for value in list(star_translation_dict.values()):
        star_translation_dict[value] = value

    key_value = 0
    try:
        if tag in special_keys:
            if tag == 'ctf':
                pass
            elif tag == 'xform.projection':
                pass
            elif tag == 'ptcl_source_coord':
                pass
            elif tag == 'xform.align2d':
                pass
            elif tag == 'data_path':
                pass
            else:
                assert False, 'Missing rule for {}'.format(tag)
        else:
            key_value = star_translation_dict[tag]
    except KeyError or TypeError:
        return key_value

    return key_value



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
        type=str
    )
    parser.add_argument(
        'output',
        type=str
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    star_file = StarFile(args.input)
    print(star_file)

"""
A write function to convert the star file 3.1 format to 3.0 . 
It is used for code compatibility for relion 3.0 format. 
Will be exchange to a new function which will be able to write directly in new format

# def write_star_oldform(self, out_star_file, tags):
#     #Writes data to disk for specified tag(s).#
# 
#     for idx, tag in enumerate(tags):
#         if idx == 0:
#             mode = 'w'
#         else:
#             mode = 'a'
#         df = self[tag]
#         is_loop = self.line_dict[tag]['is_loop']
# 
#         if is_loop:
#             export_header = '\ndata_\n\nloop_\n' + '\n'.join([
#                 '{} #{}'.format(entry, idx)
#                 for idx, entry
#                 in enumerate(df, 1)
#             ])
# 
#             with open(out_star_file, mode) as write:
#                 write.write(f'{export_header}\n')
#             df.to_csv(out_star_file, sep='\t', header=False, index=False, mode='a')
"""

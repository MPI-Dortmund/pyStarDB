# Author: Markus Stabrin 2020 (markus.stabrin@mpi-dortmund.mpg.de)
# Author: Adnan Ali 2020 (adnan.ali@mpi-dortmund.mpg.de)
# Author: Thorsten Wagner 2020 (thorsten.wagner@mpi-dortmund.mpg.de)
# Author: Tapu Shaikh 2020 (tapu.shaikh@mpi-dortmund.mpg.de)

# Copyright (c) 2020- Max Planck Institute of Molecular Physiology
#
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
        write_star() : Writes data to disk for specified tag(s)

    Variables:
        star_file : Name of STAR file
        imported_content : Data, as a pandas DataFrame
        line_dict : (dictionary) Line numbers for each section of each block
    """

    def __init__(self, star_file):
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
            "_rlnMicrographName": "ptcl_source_image",
            "_rlnDetectorPixelSize": "ptcl_source_apix",
        }
        self.special_keys = {'ctf', 'xform.projection', 'ptcl_source_coord', 'xform.align2d', "data_path"}

        self.ignored_keys = {'HostEndian', 'ImageEndian', 'MRC.maximum', 'MRC.mean', 'MRC.minimum', 'MRC.mx',
                             'MRC.my', 'MRC.mz', 'MRC.nlabels', 'MRC.nsymbt', 'MRC.nx', 'MRC.nxstart', 'MRC.ny',
                             'MRC.nystart', 'MRC.nz', 'MRC.nzstart', 'MRC.rms', 'MRC.xlen', 'MRC.ylen', 'MRC.zlen',
                             'apix_x', 'apix_y', 'apix_z', 'changecount', 'datatype', 'is_complex', 'is_complex_ri',
                             'is_complex_x', 'is_fftodd', 'is_fftpad', 'is_intensity', 'maximum', 'mean',
                             'mean_nonzero',
                             'minimum', 'nx', 'ny', 'nz', 'origin_x', 'origin_y', 'origin_z', 'sigma', 'sigma_nonzero',
                             'source_n', 'source_path', 'square_sum', 'ptcl_source_coord_id', 'ptcl_source_box_id',
                             'data_n', 'resample_ratio', 'ctf_applied', 'MRC.mapc', 'MRC.mapr',
                             'MRC.maps', 'MRC.alpha', 'MRC.beta', 'MRC.gamma', 'MRC.ispg', 'MRC.label0',
                             'MRC.machinestamp'
                             }

    def analyse_star_file(self):
        """
        Populates self.line_dict with line numbers for each section of each block.
        line_dict : Dictionary whose keys are a block of the STAR file, with 'data_' removed (e.g., 'data_optics' -> 'optics')
            keys in each block:
                block : Line numbers for entire block
                header : Line numbers for header
                content : Line numbers for data
                is_loop : (boolean) Whether block starts with 'loop_'
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
                if _.strip()
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

    def read_tag(self, tag, line_dict):
        """
        Populates self.imported_content with data.
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

    def read_with_loop(self, line_dict):
        """
        Reads data when block starts with 'loop_'.
        """
        # WHen you deal with file objects you always need to reset the
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

    def read_without_loop(self, line_dict):
        """
        Reads data when block doesn't start with 'loop_'.
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
    # def __getitem__(self, tag):
    #     return self.__getitem__(tag)
    #
    # def __setitem__(self, tag, data):
    #     self.__setitem__(tag,  data)
    # self.line_dict[tag]['is_loop'] = True

    def update(self, tag, value, loop):
        self[tag] = value
        self.line_dict.setdefault(tag, {})['is_loop'] = loop

    def get_ncolumns(self, tags=None):
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

    def write_star_file(self, out_star_file=None, tags=None, overwrite=False):
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

        # Go through each tag and load the dataframe in df.
        for idx, tag in enumerate(tags):
            if idx == 0:
                mode = 'w'
            else:
                mode = 'a'
            df = self[tag]

            try:
                is_loop = self.line_dict[tag]['is_loop']
            except:
                is_loop = False

            # if it is continuous data then write the header information first and then all the data.
            export_header = '\ndata_{}\n'.format(tag)
            index_loop = True
            if is_loop:
                export_header += '\nloop_\n' + '\n'.join([
                    '{} #{}'.format(entry, idx)
                    for idx, entry
                    in enumerate(df, 1)
                ])

                index_loop = False

            else:
                df = df.transpose()

            with open(out_star_file, mode) as write:
                write.write(f'{export_header}\n')

            df.to_csv(out_star_file, sep='\t', header=False, index=index_loop, mode='a')


def sphire_header_magic(tag, special_keys=None):
    star_translation_dict = {
        "ptcl_source_image": "_rlnMicrographName",
        "ptcl_source_apix": "_rlnDetectorPixelSize",
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
        "_rlnCoordinateY": "_rlnCoordinateY"
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
    except KeyError:
        return key_value

    return key_value


def get_emdata_ctf(star_data):
    idx_cter_astig_ang = 45 - star_data["_rlnDefocusAngle"]
    if idx_cter_astig_ang >= 180:
        idx_cter_astig_ang -= 180
    else:
        idx_cter_astig_ang += 180

    try:
        ctfdict = {"defocus": ((star_data["_rlnDefocusU"] +
                                star_data["_rlnDefocusV"]) / 20000),
                   "bfactor": star_data["_rlnCtfBfactor"],
                   "ampcont": 100 * star_data["_rlnAmplitudeContrast"],
                   "apix": (10000 * star_data["_rlnDetectorPixelSize"]) /
                           star_data["_rlnMagnification"],
                   "voltage": star_data["_rlnVoltage"],
                   "cs": star_data["_rlnSphericalAberration"],
                   "dfdiff": ((-star_data["_rlnDefocusU"] +
                               star_data["_rlnDefocusV"]) / 10000),
                   "dfang": idx_cter_astig_ang
                   }
    except:
        ctfdict = {"defocus": ((star_data["_rlnDefocusU"] +
                                star_data["_rlnDefocusV"]) / 20000),
                   "bfactor": 0.0,
                   "ampcont": 100 * star_data["_rlnAmplitudeContrast"],
                   "apix": (10000 * star_data["_rlnDetectorPixelSize"]) /
                           star_data["_rlnMagnification"],
                   "voltage": star_data["_rlnVoltage"],
                   "cs": star_data["_rlnSphericalAberration"],
                   "dfdiff": ((-star_data["_rlnDefocusU"] +
                               star_data["_rlnDefocusV"]) / 10000),
                   "dfang": idx_cter_astig_ang
                   }
    return ctfdict


def get_emdata_transform(star_data):
    trans_dict = {
        "type": "spider",
        "phi": star_data["_rlnAngleRot"],
        "theta": star_data["_rlnAngleTilt"],
        "psi": star_data["_rlnAnglePsi"],
        "tx": -star_data["_rlnOriginX"],
        "ty": -star_data["_rlnOriginY"],
        "tz": 0.0,
        "mirror": 0,
        "scale": 1.0
    }
    return trans_dict


def get_emdata_transform_2d(star_data):
    trans_dict = {
        "type": "2d",
        "tx": -star_data["_rlnOriginX"],
        "ty": -star_data["_rlnOriginY"],
        "alpha": star_data["_rlnAnglePsi"],
        "mirror": 0,
        "scale": 1.0
    }
    return trans_dict


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

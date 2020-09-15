import pandas
import re
import argparse


"""
Base Class for Starfile format. Will be able to handle data
"""
class StarFile:

    def __init__(self, star_file):
        self.star_file = star_file
        self.imported_content = {}
        self.line_dict = {}
        try:
            self.analyse_star_file()
        except:
            pass

        self.sphire_keys = {
            "_rlnMicrographName"      : "ptcl_source_image",
            "_rlnDetectorPixelSize"   : "ptcl_source_apix",
        }


    def analyse_star_file(self):
        with open(self.star_file) as read:
            content = read.read()

        """
        Part of the code which tries to find out / match the keys starting with data_ 
        """
        # https://regex101.com/r/D7O06N/1
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

    def read_tag(self, tag, line_dict):
        try:
            if not line_dict['is_loop']:
                data = self.read_without_loop(line_dict)
            else:
                data = self.read_with_loop(line_dict)
            self.imported_content[tag] = data
        except:
            return

    def read_with_loop(self, line_dict):
        header_names = pandas.read_csv(
            self.star_file,
            usecols=[0],
            skiprows=line_dict['header'][0] - 1,
            nrows=line_dict['header'][1] - line_dict['header'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
            squeeze=True,
            )
        return pandas.read_csv(
            self.star_file,
            index_col=None,
            names=header_names,
            skiprows=line_dict['content'][0]-1,
            nrows=line_dict['content'][1] - line_dict['content'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
            )

    def read_without_loop(self, line_dict):
        return pandas.read_csv(
            self.star_file,
            index_col=0,
            names=['', '0'],
            skiprows=line_dict['content'][0]-1,
            nrows=line_dict['content'][1] - line_dict['content'][0] + 1,
            skip_blank_lines=False,
            header=None,
            delim_whitespace=True,
            ).transpose()

    def __getitem__(self, tag):
        return self.imported_content[tag]

    def __setitem__(self, tag, data):
        self.imported_content[tag] = data
        # self.line_dict[tag]['is_loop'] = True


    def sphire_header_magic(self, tag):
        star_translation_dict = {
            "ptcl_source_image"         : "_rlnMicrographName",
            "data_path"                 : "_rlnImageName",
            "ptcl_source_apix"          : "_rlnDetectorPixelSize",
            "phi"                       :  "_rlnAngleRot",
            "theta"                     : "_rlnAngleTilt",
            "psi"                       : "_rlnAnglePsi",
            "voltage"                   : "_rlnVoltage",
            "cs"                        : "_rlnSphericalAberration",
            "bfactor"                   : "_rlnCtfBfactor",
            "ampcont"                   : "_rlnAmplitudeContrast",
            "apix"                      : "_rlnDetectorPixelSize",
            "tx"                        : "_rlnOriginX",
            "ty"                        : "_rlnOriginY",
            "_rlnMagnification"         : "_rlnMagnification",
            "_rlnDefocusU"              : "_rlnDefocusU",
            "_rlnDefocusV"              : "_rlnDefocusV",
            "_rlnDefocusAngle"          : "_rlnDefocusAngle",
            "_rlnCoordinateX"           : "_rlnCoordinateX",
            "_rlnCoordinateY"           : "_rlnCoordinateY"
        }


        for value in list(star_translation_dict.values()):
            star_translation_dict[value] = value

        key_value = 0
        special_keys = ('ctf', 'xform.projection', 'ptcl_source_coord', 'xform.align2d')

        try:
            if tag in special_keys:
                if tag == 'ctf':
                    pass
                elif tag == 'xform.projection':
                    pass
                elif tag == 'ptcl_source_coord':
                    pass
                elif tag == 'ptcl_source_coord':
                    pass
                elif tag == 'xform.align2d':
                    pass
                else:
                    assert False, 'Missing rule for {}'.format(tag)
            else:
                key_value  = star_translation_dict[tag]
        except KeyError:
            pass
        return key_value

    def get_emdata_ctf(self, star_data):
        # star_data = self.data[tag].iloc[idx]
        idx_cter_astig_ang = 45 - star_data["_rlnDefocusAngle"]
        if idx_cter_astig_ang >= 180:
            idx_cter_astig_ang -= 180
        else:
            idx_cter_astig_ang += 180
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

        return ctfdict

    def get_emdata_transform(self, star_data):
        trans_dict=  {
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

    def get_emdata_transform_2d(self, star_data):
        trans_dict = {
            "type": "2d",
            "tx": -star_data["_rlnOriginX"],
            "ty": -star_data["_rlnOriginY"],
            "alpha": star_data["_rlnAnglePsi"],
            "mirror": 0,
            "scale": 1.0
        }

        return trans_dict



        # import json
        # with open('translation_dict.json') as read:
        #     translation_dict = json.load(read)

    """
    A write function to convert the star file 3.1 format to 3.0 . 
    It is used for code compatibility for relion 3.0 format. 
    Will be exchange to a new function which will be able to write directly in new format
    """
    def write_star_oldform(self, star_file, tags):
        for idx, tag in enumerate(tags):
            if idx == 0:
                mode = 'w'
            else:
                mode = 'a'
            df = self.imported_content[tag]
            is_loop = self.line_dict[tag]['is_loop']

            if is_loop:
                export_header = '\ndata_\n\nloop_\n' + '\n'.join([
                    '{} #{}'.format(entry, idx)
                    for idx, entry
                    in enumerate(df, 1)
                    ])

                with open(star_file, mode) as write:
                    write.write(f'{export_header}\n')
                df.to_csv(star_file, sep='\t', header=False, index=False, mode='a')


    def write_star_file(self,star_file, tags):
        import os
        for idx, tag in enumerate(tags):
            if idx == 0:
                mode = 'w'
            else:
                mode = 'a'
            df = self.imported_content[tag]

            try:
                is_loop = self.line_dict['is_loop']
            except:
                is_loop = False

            if is_loop:
                if not os.path.isfile(star_file):
                    export_header = '\ndata_\n\nloop_\n' + '\n'.join([
                        '{} #{}'.format(entry, idx)
                        for idx, entry
                        in enumerate(df, 1)
                        ])

                    with open(star_file, mode) as write:
                        write.write(f'{export_header}\n')
                    df.to_csv(star_file, sep='\t', header=False, index=False, mode='a')
                else:
                    df.to_csv(star_file, sep='\t', header=False, index=False, mode='a')




def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
        type = str
    )
    parser.add_argument(
        'output',
        type = str
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    star_file = StarFile(args.input)


    print(star_file)

    # for val_particles, df_particles in star_file['particles'].groupby('_rlnOpticsGroup'):
    #     for val_optics, df_optics in star_file['optics'].groupby('_rlnOpticsGroup'):
    #         if val_particles == val_optics:
    #             for key in df_optics:
    #                 if key == '_rlnImagePixelSize':
    #                     new_key = '_rlnDetectorPixelSize'
    #                     star_file['particles'].loc[df_particles.index, '_rlnMagnification'] = 10000
    #                 else:
    #                     new_key = key
    #
    #                 star_file['particles'].loc[df_particles.index, new_key] = star_file['optics'].loc[df_optics.index, key].iloc[0]
    #
    #             star_file['particles'].loc[df_particles.index, '_rlnOriginX'] = \
    #                 star_file['particles'].loc[df_particles.index, '_rlnOriginXAngst'] / \
    #                 star_file['optics'].loc[df_optics.index, '_rlnImagePixelSize'].iloc[0]
    #             star_file['particles'].loc[df_particles.index, '_rlnOriginY'] = \
    #                 star_file['particles'].loc[df_particles.index, '_rlnOriginYAngst'] / \
    #                 star_file['optics'].loc[df_optics.index, '_rlnImagePixelSize'].iloc[0]
    #
    # star_file.write_star_oldform(args.output, ['particles'])
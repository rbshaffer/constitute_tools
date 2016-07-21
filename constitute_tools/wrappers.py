__author__ = 'rbshaffer'

import os
import re
import csv
import codecs
import parser
import _file_utils as utils


class Tabulator:
    def __init__(self, working_directory):
        """
        Wrapper class, which provides an easy interface to manage paths and outputs created by Segmenter.

        :param working_directory: working directory to use (with or without preexisting file structure)
        """

        self.pwd = working_directory
        self.set_structure()

    def clean_text(self, text_path):
        """
        Wrapper for clean_text function in segmenter. Output placed in Cleaned_Texts folder.

        :param text_path: path to file to be cleaned.
        """

        with utils.TextLoader(text_path) as f:
            raw_text = f.read()

        file_name = os.path.basename(text_path)
        out_path = '{1}{0}Constitute{0}Cleaned_Texts{0}{2}'.format(os.sep, self.pwd, file_name)

        cleaned = parser.clean_text(raw_text)

        with codecs.open(out_path, 'wb', 'utf-8') as f:
            f.write(cleaned)

    def tabulate(self, text_path, header_regex, preamble_level=0, case_sensitive=False, tag_format='ccp',
                 writer_format='ccp'):
        """
        Wrapper function for hierarchical parser contained in segmenter. Outputs placed in Tabulated_Texts and Reports.
        Tag data assumed to be contained in the Article_Numbers folder, with the same base name as the document to be
        parsed.

        :param text_path: path to text to be segmented.
        :param header_regex: regular expressions to use for segmentation.
        :param preamble_level: highest-level parameter immediately following the end of the preamble.
        :param case_sensitive: if True, hierarchical tag searches are case-sensitive.
        :param tag_format: format for content tags.
        :param writer_format: format for data output.
        """

        # format paths and generate output
        file_name = os.path.basename(text_path)
        file_name = re.sub('\..*', '', file_name)

        out_path = '{1}{0}Constitute{0}Tabulated_Texts{0}{2}.csv'.format(os.sep, self.pwd, file_name)
        tag_report_path = '{1}{0}Constitute{0}Reports{0}{2}_failed_tags.csv'.format(os.sep, self.pwd, file_name)
        skeleton_path = '{1}{0}Constitute{0}Reports{0}{2}_skeleton.txt'.format(os.sep, self.pwd, file_name)
        tag_path = '{1}{0}Constitute{0}Article_Numbers{0}{2}.csv'.format(os.sep, self.pwd, file_name)

        manager = parser.HierarchyManager(text_path=text_path, header_regex=header_regex,
                                          preamble_level=preamble_level, case_sensitive=case_sensitive,
                                          tag_format=tag_format, tag_path=tag_path)
        manager.parse()
        manager.apply_tags()
        out = manager.create_output(output_format=writer_format)

        # write output and generate reports
        with open(out_path, 'wb') as f:
            utils.UnicodeWriter(f).writerows(out)

        if manager.tag_data:
            with open(tag_report_path, 'wb') as f:
                var_names = sorted(manager.tag_report[0].keys())

                writer = csv.DictWriter(f, var_names)
                writer.writeheader()
                writer.writerows(manager.tag_report)

        with codecs.open(skeleton_path, 'wb') as f:
            f.write(repr(header_regex) + os.linesep)
            f.write(''.join(manager.skeleton))

    def set_structure(self):
        """
        Helper function to create the file structure assumed to be present for the rest of this wrapper. If folders are
        already present, folder creation step not done.
        :return:
        """
        if os.path.exists(self.pwd):
            path = self.pwd.rstrip('/')

            dir_list = ['Article_Numbers', 'Cleaned_Texts', 'Raw_Texts', 'Reports', 'Tabulated_Texts']
            for dir_name in dir_list:
                try:
                    os.makedirs('{1}{0}Constitute{0}{2}'.format(os.sep, path, dir_name))
                except OSError:
                    pass
        else:
            raise IOError('The given path does not exist!')

__author__ = 'rbshaffer'

import os
import re
import csv
import codecs
import cStringIO
import segmenter

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

        encodings = ['utf-8-sig', 'utf-8', 'iso-8859-15']
        raw_text = None

        for encoding in encodings:
            try:
                with codecs.open(text_path, 'rb', encoding) as f:
                    raw_text = f.read()

                print('Assuming ' + encoding + ' encoding.')
                break
            except UnicodeDecodeError:
                pass

        if raw_text is None:
            raise UnicodeDecodeError('Encoding not recognized! Re-save the cleaned text as utf-8 to continue.')

        file_name = os.path.basename(text_path)
        out_path = '{1}{0}Constitute{0}Cleaned_Texts{0}{2}'.format(os.sep, self.pwd, file_name)

        cleaned = segmenter.clean_text(raw_text)

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
        :param tag_format: format for content tags. Only 'ccp' format currently implemented.
        :param writer_format: format for data output. Only 'ccp' format currently implemented.
        :return:
        """

        file_name = os.path.basename(text_path)
        file_name = re.sub('\..*', '', file_name)

        tag_path = '{1}{0}Constitute{0}Article_Numbers{0}{2}.csv'.format(os.sep, self.pwd, file_name)

        parser = segmenter.HierarchyTagger(text_path=text_path, header_regex=header_regex,
                                              preamble_level=preamble_level, case_sensitive=case_sensitive,
                                              tag_format=tag_format, tag_path=tag_path)
        parser.parse()
        parser.apply_tags()
        out = parser.create_output(output_format=writer_format)

        out_path = '{1}{0}Constitute{0}Tabulated_Texts{0}{2}.csv'.format(os.sep, self.pwd, file_name)
        tag_report_path = '{1}{0}Constitute{0}Reports{0}{2}_failed_tags.csv'.format(os.sep, self.pwd, file_name)
        skeleton_path = '{1}{0}Constitute{0}Reports{0}{2}_skeleton.txt'.format(os.sep, self.pwd, file_name)

        with open(out_path, 'wb') as f:
            UnicodeWriter(f).writerows(out)

        if parser.tag_report:
            print('{0} out of {1} tags not matched. See reports for details.'.format(len(parser.tag_report),
                                                                                     len(parser.tag_data)))
            with open(tag_report_path, 'wb') as f:
                var_names = sorted(parser.tag_report[0].keys())

                writer = csv.DictWriter(f, var_names)
                writer.writeheader()
                writer.writerows(parser.tag_report)
        else:
            print('All tags successfully matched.')

        with open(skeleton_path, 'wb') as f:
            f.write(repr(header_regex) + os.linesep)
            f.writelines(parser.skeleton)

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


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
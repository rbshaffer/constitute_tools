import os
import csv
import codecs
import cStringIO


class TagLoader:
    """
    Helper function to load tags. Currently, only tags in the CCP format are implemented.
    """
    def __init__(self, tag_path, tag_format):

        self.tag_path = tag_path
        self.data = getattr(self, tag_format, None)()

        if self.data is None:
            print('Tag path not found or invalid tag format, so tagging will not be conducted.')

    def ccp(self):
        tag_data = None

        if self.tag_path and os.path.exists(self.tag_path):
            with open(self.tag_path, 'rb') as f:
                tag_data = list(csv.DictReader(f))
        return tag_data


class TextLoader:
    """
    Helper function to load texts of unknown encoding. Loops through a few common encodings, and throws an error if
    none work.
    """
    def __init__(self, filename):
        encodings = ['utf-8-sig', 'utf-8', 'iso-8859-15']
        for encoding in encodings:
            try:
                with codecs.open(filename, 'rb', encoding) as f:
                    self.content = f.read()

                print('Assuming ' + encoding + ' encoding.')
                break
            except UnicodeDecodeError:
                pass

        if not self.content:
            raise UnicodeDecodeError('Encoding not recognized! Re-save the cleaned text as utf-8 to continue.')


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

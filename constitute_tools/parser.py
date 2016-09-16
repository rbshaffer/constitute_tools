# -*- coding: utf-8 -*-

# Created on Feb 17, 2013
# Last updated on June 28, 2016
# @author: Robert Shaffer

import os
import re
import _file_utils as utils
import inspect
import unicodedata
from copy import deepcopy
from itertools import chain



class HierarchyManager:
    def __init__(self, text_path, header_regex, tag_path=None, preamble_level=0, case_sensitive=False,
                 tag_format='ccp'):
        """
        Regular expression-based tagger. Wraps Segmenter and uses outputs to apply content tags to hierarchy levels.
        Also generates a few reports and formats output.

        :param text_path: path to document being analyzed. Assumed to have been cleaned appropriately.
        :param header_regex: list of regular expressions corresponding to organizational headers.
        :param tag_path: optionally, path to hierarchical tags. If not given, tagging is not conducted.
        :param preamble_level: optionally, highest-level organizational tag following the document's preamble.
        :param case_sensitive: indicator for whether the header regex matches should be case-sensitive.
        :param tag_format: format in which tag data are given.
        :return:
        """

        # read raw text data, get tags, set flags, create containers for outputs
        self.pwd = os.path.dirname(inspect.getfile(inspect.currentframe()))
        self.file_name = re.sub('\..+', '', os.path.basename(text_path))

        self.header_regex = header_regex

        self.text = None
        self.parsed = None
        self.skeleton = None
        self.tag_data = None

        if case_sensitive:
            self.case_flags = re.M
        else:
            self.case_flags = re.I | re.M

        self.text = utils.TextLoader(text_path).content

        # read reference data, if any
        self.tag_data = utils.TagLoader(tag_path, tag_format).data

        if self.tag_data:
            self.tag_report = []
        else:
            self.tag_report = None

        # initialize Segmenter()
        self.parser = _Parser(self.text, self.header_regex, self.case_flags, preamble_level)

    def parse(self):
        """
        Parse the document. This function largely wraps the Segmenter class, and creates a skeleton of the
        organizational hierarchy that can be used as a diagnostic tool.
        """

        def create_skeleton(obj, out=None, depth=0):
            if not out:
                out = []

            for i in obj:
                entry = obj[i]
                if entry['header']:
                    header_to_write = entry['header']
                    out.append(depth * '\t' + header_to_write + os.linesep)

                if entry['children']:
                    if entry['children'][0]['header']:
                        out = create_skeleton(entry['children'], out, depth+1)
                    else:
                        out = create_skeleton(entry['children'], out, depth)
            return out

        self.parser.segment()
        self.parsed = self.parser.parsed
        self.skeleton = create_skeleton(self.parsed)

    def apply_tags(self):
        """
        Apply the actual content tags to the text. Tags assumed to come in the form "75.4", which indicates that the tag
        should be applied to section 4 of section 75. The only requirement imposed here is that any potential matches be
        sequential (so "75.4" would match "3.75.4" or "75.4.3" but not "75.3.4"). Unmatched tags or tags that match to
        more than one section are added to the tag_report container.
        """

        def create_stub_table(obj, out=None, current_header=None):
            """
            Helper function to recursively create a "stub" table, consisting of a mapping between all possible header
            stubs and the index combination used to reach that header stub in the parsed object. Used later for matching
            and tag application.
            """

            def format_header(h):
                """
                Helper function to strip sequences not used for matching from headers (e.g. "Title" or "Article")
                """
                h = h.lower()
                h = ''.join(e for e in h if unicodedata.category(e)[0] not in ['P', 'C'])

                if h != 'preamble':
                    h = re.sub('[a-zA-Z]{3,}|\s+', '', h)

                return h

            if not out:
                out = {}

            for i in obj:
                entry = obj[i]
                header = entry['header']

                if current_header:
                    updated_header = deepcopy(current_header)
                    if header:
                        updated_header['header'].append(format_header(header))

                    updated_header['key'].append(i)
                else:
                    updated_header = {'header': [format_header(header)], 'key': [i]}

                if entry['text_type'] != 'body':
                    joined_header = '.'.join(h for h in updated_header['header'] if h)
                    out[joined_header] = updated_header['key']

                if entry['children']:
                    create_stub_table(entry['children'], out, updated_header)

            return out

        def apply_tag(obj, index_seq, tag):
            """
            Helper function to apply tags to the parsed object.
            """
            entry = obj[index_seq.pop(0)]

            if index_seq:
                entry['children'] = apply_tag(entry['children'], index_seq, tag)
            else:
                entry['tags'].append(tag)

            return obj

        stub_table = create_stub_table(self.parsed)

        # check for tag matches and apply tags to the parsed object
        if self.tag_data:
            for tag_entry in self.tag_data:
                tag_name = tag_entry['tag']
                tag_reference = tag_entry['article']

                matches = [s for s in stub_table if re.search('^' + tag_reference + '$|\.' + tag_reference + '$', s,
                                                              self.case_flags)]

                if len(matches) == 1:
                    key_sequence = deepcopy(stub_table[matches[0]])
                    self.parsed = apply_tag(self.parsed, key_sequence, tag_name)
                else:
                    self.tag_report.append(tag_entry)

            # output a quick summary of number of tags matched
            if self.tag_report is not None:
                print('{0} out of {1} tags not matched. See reports for details.'.format(len(self.tag_report),
                                                                                         len(self.tag_data)))
            else:
                print('All tags successfully matched.')

    def create_output(self, output_format='ccp'):
        """
        Format the parsed object for easier output.

        :param output_format: format to use. Only CCP format currently implemented.
        """

        def format_ccp(obj, out=None, parent_index=0):
            """
            CCP format setup. Outputs a CSV with document hierarchy expressed using parent/child index columns.
            """
            if not out:
                out = []

            for i in sorted(obj):
                current_index = len(out)
                entry = obj[i]

                if entry['header']:
                    header_to_write = entry['header']
                else:
                    header_to_write = ''

                split_text = re.split('[\n\r]+', entry['text'])
                for line in split_text:
                    current_index = len(out)+1

                    if entry['text_type'] != 'body' or line:
                        out.append([str(current_index), str(parent_index), header_to_write, '',
                                    entry['text_type'], line] + entry['tags'])

                if entry['children']:
                    out = format_ccp(entry['children'], out, parent_index=current_index)

            return out

        if 'ccp' in output_format:
            out_data = format_ccp(self.parsed)

            # rectangularize
            max_cols = max(len(row) for row in out_data)
            out_data = [row + ['']*(max_cols - len(row)) for row in out_data]

            if 'multilingual' in output_format:
                out_data = [row[0:2] + 3*[row[2]] + row[3:5] + 3*[row[5]] + row[6:] for row in out_data]

            return out_data

        else:
            print('Only CCP output format currently implemented.')


class _Parser:
    def __init__(self, text, header_regex, case_flags, preamble_level):
        """
        Segmenter class, which does actual document segmentation work. Intended to be called through HierarchyTagger.

        :param text: text to be segmented
        :param header_regex: list of header regex to be used for segmentation
        :param preamble_level: highest-level organizational tag following the document's preamble.
        :param case_flags: indicator for whether the header regex matches should be case-sensitive.
        """

        self.text = text
        self.header_regex = ['^' + unicode(h, encoding='utf8').replace('|', '|^') for h in header_regex]
        self.preamble_level = preamble_level
        self.case_flags = case_flags

        self.parsed, self.list_table = self._pre_process()

    def segment(self):
        """
        Set up organizational headers, using regex list provided in self.header_regex. Text is pre-processed, then
        segmented into a hierarchical structure. Regular text and auxiliary list table are segmented separately, and
        then reassembled into a single output.
        """

        def shatter(obj, header_tag, case_flags):
                """
                Recursive function to segment a given object, using a given organizational tag. Segmented items are
                placed under the "children" key of the object, and then recursively segmented if any additional headers
                matching the same tag are present.

                :param obj: Dictionary object to segmented. Expected to be tabulated text or list container object.
                :param header_tag: Regex tag for a particular header.
                :param case_flags: Flags for case sensitivity.
                :return: segmented obj
                """

                # iterate over object (note that object may change size during iteration)
                entry_counter = 0
                while entry_counter < len(obj):
                    entry = obj[entry_counter]
                    header_matches = list(re.finditer(header_tag, entry['text'], flags=case_flags))

                    # if a header match is found, split the text into pre-match start_stub and post-match content
                    if len(header_matches) > 0:
                        header_starts = [header.start() for header in header_matches]
                        header_starts.append(len(entry['text']))

                        start_stub = entry['text'][:header_starts[0]].strip('\t\n\r ')

                        new_entries = []

                        # for all header matches in post-match content, extract titles and text and format an entry
                        for j, header_regex in enumerate(header_matches):
                            text = entry['text'][header_regex.end():header_starts[j+1]].strip('\t\n\r ')

                            if '</title>' in text and '<title>' in text:
                                title = re.search('<title>.*?</title>', text)
                            elif '<title>' in text:
                                title = re.search('.*<title>.*', text)
                            else:
                                title = None

                            header = header_regex.group(0).strip('\t\n\r ')
                            header = re.sub('[,|;^#*]', '', header)
                            header = re.sub('[-.:](?![A-Za-z0-9])', '', header)

                            if title:
                                text = text[:title.start()] + text[title.end():]
                                title_text = re.sub('</?title>', '', title.group(0)).strip('\t\n\r ')
                            else:
                                title_text = ''

                            new_entry = {'header': header,
                                         'text': title_text,
                                         'children': {},
                                         'text_type': 'title',
                                         'tags': []}

                            new_entry['children'][0] = {'header': None,
                                                        'text': text,
                                                        'children': {},
                                                        'text_type': u'body',
                                                        'tags': []
                                                        }

                            new_entries.append(new_entry)

                        # if there is a start_stub, then add new header matches as children of the current entry
                        if start_stub:
                            entry['children'][0] = {'header': None,
                                                    'text': start_stub,
                                                    'children': {i: new_entries[i] for i in range(len(new_entries))},
                                                    'text_type': u'body',
                                                    'tags': []}
                            entry['text'] = ''
                        # otherwise, add the new entries to the current level (keeping preexisting content)
                        else:
                            updated_obj = {i: obj[i] for i in obj if i < entry_counter}
                            updated_obj.update({i+entry_counter: new_entries[i] for i in range(len(new_entries))})
                            updated_obj.update({i+len(new_entries)-1: obj[i] for i in obj if i > entry_counter})

                            obj = updated_obj

                    entry['children'] = shatter(entry['children'], header_tag, case_flags)
                    entry_counter += 1

                return obj

        def assemble(obj, list_data):
                """
                Recursively reassemble the tabulated text and any lists extracted earlier. Lists are re-inserted at
                their positions marked by the extract_lists() function.

                :param obj: tabulated text object being checked for lists
                :param list_data: table of lists extracted earlier
                :return: assembled obj
                """

                # iterate through the object until end is reached
                entry_counter = 0
                while entry_counter < len(obj):
                    entry = obj[entry_counter]
                    list_search = re.search('\{@([0-9]+)\}', entry['text'], flags=re.M)

                    # if a list is present, separate pre/post list content into two separate entries, insert the list as
                    # a set of children under the pre-list entry, and add the post-list entry if present
                    if list_search:
                        list_entry = list_data[int(list_search.group(1))]

                        new_entries = []

                        pre_list_entry = deepcopy(entry)
                        post_list_entry = deepcopy(entry)

                        pre_list_entry['text'] = entry['text'][:list_search.start()].strip('\n\r ')
                        post_list_entry['text'] = entry['text'][list_search.end():].strip('\n\r ')

                        if len(list_entry) > 1:
                            for i in list_entry:
                                list_entry[i]['text_type'] = u'olist'

                            pre_list_entry['children'] = list_entry
                        else:
                            pre_list_entry['children'] = {0: {'header': '',
                                                              'text': '',
                                                              'children': list_entry,
                                                              'text_type': u'ulist',
                                                              'tags': []}}

                        new_entries.append(pre_list_entry)

                        if post_list_entry['text'] or post_list_entry['children']:
                            new_entries.append(post_list_entry)

                        # rebuild the object by combining earlier content, re-inserted content, and later content
                        updated_obj = {i: obj[i] for i in obj if i < entry_counter}
                        updated_obj.update({i + entry_counter: new_entries[i] for i in range(len(new_entries))})
                        updated_obj.update({i + len(new_entries)-1: obj[i] for i in obj if i > entry_counter})

                        obj = updated_obj

                    # recursively apply assemble() to check for lists in children of the current object

                    if obj[entry_counter]['children']:
                        obj[entry_counter]['children'] = assemble(obj[entry_counter]['children'], list_data)

                    entry_counter += 1

                return obj

        # shatter tabulated file and the list table
        for tag in self.header_regex:
            self.parsed = shatter(self.parsed, tag, self.case_flags)
            for key in self.list_table:
                self.list_table[key] = shatter(self.list_table[key], tag, self.case_flags)

        # reassemble the tabulated file and the list table together
        self.parsed = assemble(self.parsed, self.list_table)

        self._check_desync()

    def _pre_process(self):
        """
        Pre-processing function, to prepare for parsing. Markup tags are sanitized, lists are extracted and placed
        into an auxiliary table.
        """
        def extract_lists(text):
            """
            Extract tagged lists out of the base text. Lists are extracted as blocks of text and placed into a
            temporary table, to be re-added after the organizational headers are created. List locations are marked
            using a special tag of the form {@*}, with * corresponding to the entry in the list table.
            """

            def check_list_syntax(text_data):
                """
                Check for valid list syntax. In particular, check that all tags are closed, that no illegal
                substitution tags are present, and that tags are appropriately nested within one another.
                """

                # check for illegal list substitution characters (used as list substitutes)
                list_markers = list(re.finditer('{@[0-9]+}', text_data))
                if list_markers:
                    raise Exception('Illegal character strings present. Delete the following to continue:  ' +
                                    ', '.join([l.group(0) for l in list_markers]))

                # check that lists are closed and that tag pairs properly follow one another
                openings = list(re.finditer('<(list_?[0-9]*)>', text_data))
                openings = {opening: [o.start() for o in openings if o == opening]
                            for opening in set([o.group(1) for o in openings])}

                closings = re.finditer('</(list_?[0-9]*)>', text_data)
                closings = {closing: [c.start() for c in closings if c == closing]
                            for closing in set([c.group(1) for c in closings])}

                for opening_text in openings:
                    if opening_text not in closings:
                        raise Exception('A list tag of the following type was not closed: ' + opening_text)
                    else:
                        for o_start in openings[opening_text]:
                            next_closings = [c_start for c_start in closings[opening_text] if c_start > o_start]
                            subsequent_openings = [o for o in openings[opening_text] if o > o_start]

                            if len(subsequent_openings) > 0 and next_closings[0] > subsequent_openings[0]:
                                raise Exception('A list tag pair of the following type was malformed: ' +
                                                opening_text)

            def get_lists(text_data, list_counter):
                if re.search('<(list_?[0-9]*)>', text_data):
                    open_tag_regex = re.search('<(list_?[0-9]*)>[\n\r]*', text_data)
                    close_tag_regex = re.search('[\n\r]*</' + open_tag_regex.group(1) + '>',
                                                text_data[open_tag_regex.end():])

                    list_section = text_data[open_tag_regex.end():(open_tag_regex.end() + close_tag_regex.start())]

                    text_data = text_data[:open_tag_regex.start()] + '{@' + str(list_counter) + '}' + \
                                text_data[(open_tag_regex.end() + close_tag_regex.end()):]

                    list_obj = {'header': None,
                                'text': list_section,
                                'children': {},
                                'text_type': 'body',
                                'tags': []
                                }
                    return {'text': text_data, 'list_obj': list_obj, 'index': list_counter}
                else:
                    return None

            check_list_syntax(text)
            list_data = {}

            # get lists from text
            while True:
                list_output = get_lists(text, len(list_data))
                if list_output:
                    text = list_output['text']
                    list_data.update({list_output['index']: {0: list_output['list_obj']}})
                else:
                    break

            # handle nested lists by iterating over the list table
            list_table_counter = 0
            while list_table_counter < len(list_data):
                entry = list_data[list_table_counter][0]
                list_output = get_lists(entry['text'], len(list_data))

                if list_output:
                    entry['text'] = list_output['text']
                    list_data.update({list_output['index']: {0: list_output['list_obj']}})
                else:
                    list_table_counter += 1

            return text, list_data

        def shatter_preamble(text, headers, pre_level):
            """
            Extract the preamble. Preambles are separated from the body of the text and placed into self.tabulated.
            """

            # find the start of the preamble (either an explicit tag or the beginning of the text)
            if '<preamble>' in text:
                preamble_start = re.search('\s*<preamble>\s*', text).start()
            else:
                preamble_start = 0

            # find the end of the preamble (either an explicit tag or the first instance of a particular header tag)
            if '</preamble>' in text:
                preamble_end = re.search('\s*</preamble>\s*', text).end()
            elif pre_level >= 0:
                preamble_end = re.search(headers[pre_level], text, self.case_flags).start()
            else:
                preamble_end = 0

            preamble = text[preamble_start:preamble_end].strip('\n\r\t ')
            body = text[preamble_end:]

            to_add = []

            # add the preamble (if any) and the body text to self.tabulated
            if preamble:
                preamble = re.sub('</?preamble>', '', preamble)
                to_add.append({'header': u'preamble',
                               'text': u'',
                               'children': {0: {'header': None,
                                                'text': preamble,
                                                'children': {},
                                                'text_type': u'body',
                                                'tags': []}
                                            },
                               'text_type': u'title',
                               'tags': []})

            to_add.append({'header': u'',
                           'text': body,
                           'children': {},
                           'text_type': u'body',
                           'tags': []})

            tabulated = {i: to_add[i] for i in range(len(to_add))}
            return tabulated

        to_process = self.text

        # sanitize tags, change newline formatting
        to_process = to_process.replace('\n" .', '" .')
        to_process = to_process.replace(' >', '>')

        preamble_tags = re.finditer('\s*(</?preamble>)\s*', to_process)
        list_tags = re.finditer('\s+(</?list[_]?[0-9]*>)\s*', to_process)

        for t in chain(list_tags, preamble_tags):
            to_process = to_process.replace(t.group(0), t.group(1) + '\n')

        to_process = re.sub('[\n\r]+', '\n', to_process)

        # get lists, split preamble from the rest of the text, and return containers ready for further segmentation
        to_process, lists = extract_lists(to_process)
        segmented = shatter_preamble(to_process, self.header_regex, self.preamble_level)

        return segmented, lists

    def _check_desync(self):
        """
        Sanity-checking function, which makes sure that the body text has been maintained after processing. If a
        desynchronization between the processed and original text occurs, then something has gone very wrong!
        """

        def minimal_format(text_string):
            text_string = re.sub('<.*?>', ' ', text_string)
            text_string = re.sub('\s+', ' ', text_string)
            text_string = ''.join(e for e in text_string if unicodedata.category(e)[0] not in ['P', 'C'])
            text_string = text_string.lower()
            text_string = text_string.strip()
            text_string = re.sub('\s+', ' ', text_string)

            return text_string

        def combine(obj, out=None):
            if not out:
                out = u''

            for i in obj:
                entry = obj[i]
                if entry['text']:
                    out += u' ' + entry['text'].strip()
                    out = out.strip()
                if entry['children']:
                    out = combine(entry['children'], out)

            return out

        original_text = self.text
        for tag in self.header_regex:
            tag = '^' + tag.replace('|', '|^')
            original_text = re.sub(tag, ' ', original_text, flags=self.case_flags)

        original_text = minimal_format(original_text)

        processed_text = combine(self.parsed)
        processed_text = minimal_format(processed_text)

        desync_point = 0
        while desync_point < min(len(processed_text), len(original_text)):
            if processed_text[desync_point] != original_text[desync_point]:
                break
            else:
                desync_point += 1

        if len(processed_text) != len(original_text) or desync_point != len(processed_text):
            print('Warning! Desync between original and tabulated text found.')

            print('Original text fragment:')
            print(original_text[desync_point-50:desync_point+100])
            print('Processed text fragment:')
            print(processed_text[desync_point-50:desync_point+100])


def clean_text(raw_text):
    """
    Simple text-cleaning function, which attempts to delete unnecessary whitespace.

    :param raw_text: text string to be cleaned
    :return: cleaned text
    """

    cleaned = re.sub('[\t ]+', ' ', raw_text)
    cleaned = re.sub('\n(?=[a-z]+[^.:)])| +', ' ', cleaned)
    cleaned = re.sub('\n+', '\n', cleaned)
    cleaned = re.sub('(\n\r)+', '\n\r', cleaned)
    cleaned = re.sub('\n +', '\n', cleaned)
    cleaned = re.sub('\r +', '\r', cleaned)

    return cleaned

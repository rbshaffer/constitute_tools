# constitute_tools

Auxilary toolset for [Constitute](https://www.constituteproject.org/) data backend. The **constitute_tools** package performs two basic functions:

1. *Segment* hierarchical documents according to given organizational headers.

2. *Match* content tags (tags noting the presense of some concept in a block of text) to appropriate positions in document hierarchy.

Basic functionality is provided through ``parser.HierachyManager``, which exposes analysis, error-checking, and output-generating methods. A wrapper for ``parser.HierarchyManager`` is provided in ``wrappers.Tabulator``, which handles file path management and output creation for smaller-scale tagging applications.

# Dependencies and installation
**constitute_tools** assumes Python 2.7.x (Python 3 version coming soon). No dependencies beyond the base Python packages are required. 

# Usage
## Markup
Suppose a user is interested in segmenting the following text:

```
The people of New Exampleland hereby found a new nation on December 1st, 2020.
Chapter 1: The President.
The country of New Exampleland shall have a president. The president's powers shall be:
1. Appoint judges.
2. Veto laws.
3. Propose the national budget.
Chapter 2: The Legislature.
A. The legislature shall have the power to legislate on all topics by a simple majority vote.
B. Members of the legislature shall be limited to 10 years in office.
```

This text contains a preamble, a list with some preceding content, and titles on several headers. To capture this content, the user might mark up the text as follows:

```
<preamble>
The people of New Exampleland hereby found a new nation on December 1st, 2020.
</preamble>
Chapter 1: <title> The President. </title>
The country of New Exampleland shall have a president. The president's powers shall be:
<list>
1. Appoint judges.
2. Veto laws.
3. Propose the national budget.
</list>
Chapter 2: <title>The Legislature. </title>
A. The legislature shall have the power to legislate on all topics by a simple majority vote.
B. Members of the legislature shall be limited to 10 years in office.
```

The headers in this setup can be caputured with the following regular expression sequence: `['Chapter [0-9]+:', '[0-9]\.|[A-Z]\.']`.

## Parsing

To actually parse the document structure, the user might use the following code snippet:

```
import csv
from constitute_tools.parser import HierarchyManager, clean_text

# read in and do a first-pass clean on the text
raw_text_path = '/path/to/raw_text.txt'
clean_text_path = '/path/to/cleaned_text.txt'

with open(raw_text_path, 'rb') as f:
  raw_text = f.read()
```

`parser.clean_text(raw_text)` cleans `raw_text` by removing extraneous whitespace and sanitizing tags. Users should review the text before proceeding for other formatting issues (see below for details), as some issues may not be caught.

```
with open(clean_text_path, 'wb') as f:
  cleaned_text = clean_text(raw_text)
  f.write(cleaned_text)
  
# after confirming that the text is fully cleaned, parse it:
tag_path = '/path/to/tags.csv'
header_regex = ['Chapter [0-9]+:', '[0-9]\.|[A-Z]\.']

manager = HierarchyManager(text_path = clean_text_path, header_regex = header_regex, tag_path = tag_path)
manager.parse()
manager.apply_tags()
```

`tag_path` should contain a path to any available content tags (see below for formatting details). If omitted, no tagging will be conducted.

## Outputs
The parsed document is contained in HierarchyManager.parsed, which uses the following data structure:

```
{0: 
  {'header': u'preamble', 
   'tags': [], 
   'children': {0: 
                  {'header': None, 
                   'tags': [], 
                   'children': {}, 
                   'text_type': u'body', 
                   'text': u'\nThe people of New Exampleland hereby found a new nation on December 1st, 2020.\n'
                   }
                }
    'text': u'',
    'text_type'=u'title'
  }
  1: 
    {'header': u'Chapter 1', 
     'tags': [], 
     'children': {0: 
                    {'header': None, 
                     'text': u"The country of New Exampleland shall have a president. The president's powers shall be:", 'children': {...},
                     'text_type': 'body', 
                     'tags': []
                     }
                  }
      'text': u'The President.',
      'text_type': u'title'
      }
  ...
}
```
This structure can be nested to arbitrary depth. Each level can contain text, headers, children, tags, and a `type` tag, which is assigned automatically during parsing. Possible types include `body`, `title`, `ulist` (for "unorganized list", or a list without headers) and `olist` (for "organized list", or a list with headers).

Other outputs include `HierarchyManager.skeleton`, a visual aid which helps to check for parsing errors:

```
>>print(''.join(manager.skeleton))
preamble
Chapter 1
	1
	2
	3
Chapter 2
	A
	B
```

With punctuation automatically stripped for readability. For other details, see docstrings.

## Error-checking
As a sanity check, the model automatically checks for desyncronization (lost text) between the original text and the parsed text, and outputs a warning if text goes missing. If content tag data is given, unmatched tag entries will be placed in `HierarchyManager.tag_report`. Otherwise, parser correctness is difficult to determine programmatically, so users will need to confirm parser accuracy by hand.

## Writing 
After the user is satisfied with their results, parser.HierarchyManager offers a small function to write outputs in a flatted "CCP-style" structure, which may be useful for some applications:

```
>> ccp_out = manager.create_output('ccp')
>> print(ccp_out)
[['1', '0', u'preamble', 'title', ''],
 ['2', '1', '', 'body', u'The people of New Exampleland hereby found a new nation on December 1st, 2020.'],
 ['3', '0', u'Chapter 1', 'title', u'The President.'],
 ['4', '3', '', 'body', u"The country of New Exampleland shall have a president. The president's powers shall be:"],
 ...
]
```
In this format, the first column is an index and the second column gives the "parent" index of the current row (with 0 reserved for the "base" level of the document). 

## Scripting wrappers
For serial tagging taks, the wrappers.Tabulate class can streamline file management and function calls:

```
from constitute_tools.wrappers import Tabulator

working_dir = '/path/to/working_directory'
raw_text_path = '/path/to/raw_text.txt'

# initialize Tabulator with a working directory
# if not already present, the script will create a file structure in the working directory to dump outputs
tabulator = Tabulator(working_dir)
tabulator.clean_text(raw_text_path)

# after checking to make sure that the text was cleaned appropriately, parse and generate output
# by default, Tabulate will look for tag data in the Article_Numbers working directory folder
cleaned_text = '/path/to/Constitute/Cleaned_Text/cleaned.txt'
header_regex = ['Chapter [0-9]+:', '[0-9]\.|[A-Z]\.']`

# tabulate() will parse, apply tags, and write a CCP-style output to the Tabulated_Texts folder
# reports will be written to the Reports folder
tabulator.tabulate(cleaned_text, header_regex)
```


# Details
## Texts
Texts should be formatted with organizational headers at the beginning of the line. Organizational headers can be any text string that can be expressed as a Python-style [regular expression](https://docs.python.org/2/library/re.html) (e.g. "Article [0-9]+" or "Title [0-9]+[a-z]?"). 

Non-ASCII text formats are usually handled gracefully. However, for best results, texts should be saved in UTF-8 format.

Texts can be marked up using two different tagging structures. Some headers contain titles (e.g. ``'Article 1: The Presidency'``), which can be marked using a ``<title>`` tag placed anywhere on the same line (e.g. ``'Article 1: The Presidency <title>'``). If the closing `</title` tag is omitted, the line containing the opening `<title>` tag will be treated as the title.

Other headers contain lists, which may be preceded or followed by additional text. Lists should be enclosed in ``<list>`` tags, with nested lists differentiated using index numbers (e.g. ``'<list_1>...<list_2>...</list_2></list_3>'``). Indices can be replicated outside of a given nested structure.

## Header list
The organizational header list should be ordered from highest- to lowest-level header, with same-level headers contained in the same text string and separated by pipes (e.g. ``'[ivx]+|(Introduction|Notes|Sources)'``). 

## Content tags (optional)
Currently, only Comparative Constitutions Project (CCP)-style tags are supported. In the CCP format, tags are organized into a CSV file with labeled 'tag' and 'article' columns (as well as any other variables that might be useful). The 'tag' column should contain variable names and the 'article' column should contain a reference to an organizational header level (e.g. ``'75.1.a'`` for ``'Article 75, Section 1, Part a'``). 

The only assumption made regarding header references is that headers are sequential; so, ``'75.1'`` would match ``'Article 75, Section 1, Part a'`` or ``'Article A, Section 75, Part 1'`` but not ``'Article 75, Section A, Part 1'``. If multiple matches are found, tags are not applied, and are instead appended to HierarchyManager.tag_report.

# constitute_tools

Auxilary toolset for [Constitute](https://www.constituteproject.org/) data backend. The **constitute_tools** package performs two basic functions:

1. *Segment* hierarchical documents according to given organizational headers.

2. *Match* content tags to appropriate positions in document hierarchy.

Basic functionality is provided through ``parser.HierachyManager``, which exposes analysis, error-checking, and output-generating methods. A wrapper for ``parser.HierarchyManager`` is provided in ``wrappers.Tabulator``, which handles file path management and output creation for smaller-scale tagging applications.

# Dependencies and installation
**constitute_tools** assumes Python 2.7.x (Python 3 version coming soon). No dependencies beyond the base Python packages are required. 

# Usage
The workhorse class in **constitute_tools** is ``parser.HierarchyManager``. ``parser.HierachyManager`` has three main methods, which take (1) a path to the text, (2) a list of header tags, and (3) a path to the content tags (if any) as inputs. Additional arguments provide further customization; for details, see documentation.

# Inputs
## Texts
Texts should be formatted with organizational headers at the beginning of the line. Organizational headers can be any text string that can be expressed as a Python-style [regular expression](https://docs.python.org/2/library/re.html) (e.g. "Article [0-9]+" or "Title [0-9]+[a-z]?"). 

Non-ASCII text formats are usually handled gracefully. However, for best results, texts should be saved in UTF-8 format.

Texts can be marked up using two different tagging structures. Some headers contain titles (e.g. ``'Article 1: The Presidency'``), which can be marked using a ``<title>`` tag placed anywhere on the same line (e.g. ``'Article 1: The Presidency <title>'``). ``<title>`` tags do not need to be closed.

Other headers contain lists, which may be preceded or followed by additional text. Lists should be enclosed in ``<list>`` tags, with nested lists differentiated using index numbers (e.g. ``'<list_1>...<list_2>...</list_2></list_3>'``). Indices can be replicated outside of a given nested structure. ``<list>`` tags should be closed. 

## Header list
The organizational header list should be ordered from highest- to lowest-level header, with same-level headers contained in the same text string and separated by pipes (e.g. ``'[ivx]+|(Introduction|Notes|Sources)'``). 

## Content tags (optional)
Currently, only Comparative Constitutions Project (CCP)-style tags are supported. In the CCP format, tags are organized into a CSV file with labeled 'tag' and 'article' columns (as well as any other variables that might be useful). The 'tag' column should contain variable names and the 'article' column should contain a reference to organization an organizational header level (e.g. ``'75.1.a'`` for ``'Article 75, Section 1, Part a'``). 

The only assumption made regarding header references is that headers are sequential; so, ``'75.1'`` would match ``'Article 75, Section 1, Part a'`` or ``'Article A, Section 75, Part 1'`` but not ``'Article 75, Section A, Part 1'``. If multiple matches are found, tags are not applied, and are instead appended to HierarchyManager.tag_report.

# Outputs

# Examples
A basic tagging application might look as follows:

```
import csv
from constitute_tools.parser import HierarchyManager, clean_text

# read in and do a first-pass clean on the text
raw_text_path = '/path/to/raw_text.txt'
clean_text_path = '/path/to/cleaned_text.txt'

with open(raw_text_path, 'rb') as f:
  raw_text = f.read()

with open(clean_text_path, 'wb') as f:
  cleaned_text = clean_text(raw_text)
  f.write(cleaned_text)
  
# after making sure that the text is fully cleaned, parse it:
tag_path = '/path/to/tags.csv'
header_regex = ['Header the First [0-9]+', 'Header the Second [a-z]', 'Header|The|Third']

manager = HierarchyManager(text_path = text_path, header_regex = header_regex, tag_path = tag_path)
manager.parse()
manager.apply_tags()
```

After parsing and tag application, HierarchyManager then offers several output and error-checking options:

```
# view the first object in the parsed output (which can be written if appropriate)
print(manager.parsed[0])

# view the "skeleton" of header tags, to make sure that all relevant headers were captured
print(manager.skeleton)

# view any failed tags
print(manager.tag_report)

# generate and write a CCP-style CSV output, with flattened hierarchical structure
ccp_out = manager.create_output('ccp')

with open('/path/to/output.csv', 'wb') as f:
  csv.writer(f).writerows(ccp_out)
```

For serial tagging taks, the wrappers.Tabulate wrapper can streamline file management and function calls:

```
from constitute_tools.wrapper import Tabulate

working_dir = '/path/to/working_directory'
raw_text_path = '/path/to/raw_text.txt'

# initialize Tabulator with a working directory
# if not already present, the script will create a file structure in the working directory to dump outputs
tabulator = Tabulate(working_dir)
tabulator.clean_text(raw_text_path)

# after checking to make sure that the text was cleaned appropriately, parse and generate output
# by default, Tabulate will look for tag data in the Article_Numbers working directory folder
cleaned_text = '/path/to/Constitute/Cleaned_Text/cleaned.txt'
header_regex = ['Header the First [0-9]+', 'Header the Second [a-z]', 'Header|The|Third']

# tabulate() will parse, apply tags, and write the output to the Tabulated_Texts folder, using the CCP output format
# reports will be written to the Reports folder
tabulator.tabulate(cleaned_text, header_regex)
```

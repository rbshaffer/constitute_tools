# constitute_tools

Auxilary toolset for [Constitute](https://www.constituteproject.org/) data backend. The **constitute_tools** package is intended to perform two basic functions:

1. Subdivide hierarchical documents to arbitrary depth according to organizational headers, while maintaining hierarchical structure.

2. Match content tags to appropriate positions in document hierarchy.

Basic functionality is provided through the parser.HierachyManager class, which exposes a variety of analysis, error-checking, and output-generating methods. A wrapper for parser.HierarchyManager is provided in wrappers.Tabulator, which handles file path management and output creation for smaller-scale tagging applications.

# Dependencies and installation
**constitute_tools** assumes Python 2.7.x (Python 3 version coming soon). No dependencies beyond the base Python environment are required, so running `python setup.py install` from a base Python installation should be sufficient.

# Inputs
The workhorse class in **constitute_tools** is parser.HierarchyManager. parser.HierarchyManager takes three basic inputs:

## Texts
Texts should be formatted with organizational headers at the beginning of the line. Organizational headers can be any text string that can be expressed as a Python-style [regular expression](https://docs.python.org/2/library/re.html) (e.g. "Article [0-9]+" or "Title [0-9]+[a-z]?"). Non-ASCII text formats are usually handled gracefully; however, for best results, texts should be saved in UTF-8 format.

Texts can be marked up using two different tagging structures. Some headers contain titles (e.g. "Article 1: The Presidency"), which can be marked using a <title> tag placed anywhere on the same line (e.g. "Article 1: The Presidency <title>"). <title> tags do not need to be closed.

Other headers contain lists, which may be preceded or followed by additional text. Lists should be enclosed in <list> tags, with nested lists differentiated using index numbers (e.g. "<list_1>...<list_2>...</list_2></list_3>"). Indices can be replicated outside of a given nested structure. List tags should be closed. 

## Header list
The organizational header list should be ordered from highest- to lowest-level header, with same-level headers contained in the same text string and separated by pipes (e.g. '[ivx]+|(Introduction|Notes|Sources)'). 

## Content tags (optional)
Currently, the only tag format that is supported is the Comparative Constitutions Project (CCP) format, which organizes tags into a CSV with labeled 'tag' and 'article' columns (as well as any others that might be useful). The 'tag' column should contain variable names and the 'article' column should contain a reference to organization an organizational header level (e.g. '75.1.a' for "Article 75, Section 1, Part a"). 

The only assumption made regarding header references is that headers are sequential; so, "75.1" would match "Article 75, Section 1, Part a" or "Article A, Section 75, Part 1" but not "Article 75, Section A, Part 1". If multiple matches are found, tags are not applied, and are instead appended to HierarchyManager.tag_report.

# Usage

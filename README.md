# constitute_tools

Auxilary toolset for [Constitute](https://www.constituteproject.org/) data backend. The **constitute_tools** package is intended to perform two basic functions:

1. Arbitrarily subdivide hierarchical documents according to organizational headers, while maintaining hierarchical structure.

2. Match content tags to appropriate positions in document hierarchy.

Basic functionality is provided through the parser.HierachyManager class, which exposes a variety of analysis, error-checking, and output-generating methods. A wrapper for parser.HierarchyManager is provided in wrappers.Tabulator, which handles file path management and output creation for smaller-scale tagging applications.

# Dependencies and installation
**constitute_tools** assumes Python 2.7.x (Python 3 version coming soon). No dependencies beyond the base Python environment are required, so running `python setup.py install` from a base Python installation should be sufficient.

# Usage
The workhorse class in **constitute_tools** is parser.HierarchyManager. parser.HierarchyManager takes three basic inputs:

- A cleaned, properly-formatted text file.
- A set of regular expressions corresponding to the organization headers contained in the text file.
- (Optionally) a set of content tags, to be applied to the parsed text file.

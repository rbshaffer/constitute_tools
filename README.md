# constitute_tools

Auxilary toolset for [Constitute](https://www.constituteproject.org/) data backend. Package is intended to perform two basic functions:

1. Arbitrarily subdivide hierarchical documents according to organizational headers, while maintaining hierarchical structure.

2. Match content tags to appropriate positions in document hierarchy.

Basic functionality is provided through the parser.HierachyManager class, which exposes a variety of analysis, error-checking, and output-generating methods. A wrapper for parser.HierarchyManager is provided in wrappers.Tabulator, which handles file path management and output creation for smaller-scale tagging applications.

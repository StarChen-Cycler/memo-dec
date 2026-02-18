#!/usr/bin/env python3
"""
Unit tests for Jupyter notebook (.ipynb) file symbol extraction.
"""
import sys
import json
import unittest
from pathlib import Path
from memo_dec.symbol_extractor import extract_symbols, extract_symbols_from_notebook


class TestJupyterNotebookExtraction(unittest.TestCase):
    """Test Jupyter notebook symbol extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "test_notebook_files"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_test_notebook(self, filename, cells):
        """Helper to create a test notebook file."""
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        test_file = self.test_dir / filename
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2)

        return test_file

    def test_simple_notebook_with_functions(self):
        """Test extracting functions from a simple notebook."""
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# My Analysis\n",
                    "This notebook contains data analysis functions."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import numpy as np\n",
                    "import pandas as pd\n",
                    "\n",
                    "def load_data(filepath):\n",
                    "    \"\"\"Load data from a CSV file.\"\"\"\n",
                    "    return pd.read_csv(filepath)\n",
                    "\n",
                    "def clean_data(df):\n",
                    "    \"\"\"Clean the dataframe by removing nulls.\"\"\"\n",
                    "    return df.dropna()\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "class DataAnalyzer:\n",
                    "    \"\"\"Class for analyzing data.\"\"\"\n",
                    "    \n",
                    "    def __init__(self, data):\n",
                    "        self.data = data\n",
                    "    \n",
                    "    def calculate_mean(self, column):\n",
                    "        \"\"\"Calculate mean of a column.\"\"\"\n",
                    "        return self.data[column].mean()\n",
                    "    \n",
                    "    def calculate_std(self, column):\n",
                    "        \"\"\"Calculate standard deviation.\"\"\"\n",
                    "        return self.data[column].std()\n"
                ]
            }
        ]

        test_file = self.create_test_notebook("analysis.ipynb", cells)
        symbols = extract_symbols(test_file)

        print("\n=== Jupyter Notebook (Functions and Classes) ===")
        for sym in symbols:
            print(f"Cell {sym.get('cell', '?'):2d}, Line {sym['line']:3d}: {sym['type']:10s}: {sym['name']}")

        self.assertTrue(len(symbols) > 0, "Should find symbols in notebook")

        # Check for functions
        functions = [s for s in symbols if s['type'] == 'function']
        func_names = [f['name'] for f in functions]
        self.assertIn('load_data', func_names, "Should find load_data function")
        self.assertIn('clean_data', func_names, "Should find clean_data function")

        # Check for class
        classes = [s for s in symbols if s['type'] == 'class']
        class_names = [c['name'] for c in classes]
        self.assertIn('DataAnalyzer', class_names, "Should find DataAnalyzer class")

        # Check for methods
        methods = [s for s in symbols if s['type'] == 'function' and s['name'] in ['__init__', 'calculate_mean', 'calculate_std']]
        self.assertTrue(len(methods) >= 3, "Should find DataAnalyzer methods")

    def test_notebook_with_variables(self):
        """Test extracting variables from notebook."""
        cells = [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Configuration constants\n",
                    "DATA_PATH = 'data/input.csv'\n",
                    "OUTPUT_PATH = 'data/output.csv'\n",
                    "THRESHOLD = 0.95\n",
                    "MAX_ITERATIONS = 1000\n",
                    "\n",
                    "# Data parameters\n",
                    "columns_to_keep = ['id', 'value', 'timestamp']\n",
                    "filter_conditions = {'status': 'active'}\n"
                ]
            }
        ]

        test_file = self.create_test_notebook("config.ipynb", cells)
        symbols = extract_symbols(test_file)

        print("\n=== Jupyter Notebook (Variables) ===")
        for sym in symbols:
            print(f"Cell {sym.get('cell', '?'):2d}, Line {sym['line']:3d}: {sym['type']:10s}: {sym['name']}")

        # Check for variables
        variables = [s for s in symbols if s['type'] == 'variable']
        var_names = [v['name'] for v in variables]

        self.assertIn('DATA_PATH', var_names, "Should find DATA_PATH variable")
        self.assertIn('OUTPUT_PATH', var_names, "Should find OUTPUT_PATH variable")
        self.assertIn('THRESHOLD', var_names, "Should find THRESHOLD variable")
        self.assertIn('MAX_ITERATIONS', var_names, "Should find MAX_ITERATIONS variable")
        self.assertIn('columns_to_keep', var_names, "Should find columns_to_keep variable")
        self.assertIn('filter_conditions', var_names, "Should find filter_conditions variable")

    def test_notebook_multiple_cells(self):
        """Test that symbols are correctly tracked across multiple cells."""
        cells = [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def function_in_cell1():\n",
                    "    return \"cell1\"\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "This is a markdown cell with no code."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def function_in_cell3():\n",
                    "    return \"cell3\"\n",
                    "\n",
                    "class ClassInCell3:\n",
                    "    pass\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# This cell has 4 lines total\n",
                    "variable_in_cell4 = 42\n",
                    "\n",
                    "def function_in_cell4():\n",
                    "    return variable_in_cell4\n"
                ]
            }
        ]

        test_file = self.create_test_notebook("multi_cell.ipynb", cells)
        symbols = extract_symbols(test_file)

        print("\n=== Jupyter Notebook (Multiple Cells) ===")
        for sym in symbols:
            print(f"Cell {sym.get('cell', '?'):2d}, Line {sym['line']:3d}: {sym['type']:10s}: {sym['name']}")

        # Check that we have symbols from different cells
        self.assertTrue(len(symbols) > 0, "Should find symbols across multiple cells")

        # Group by cell
        symbols_by_cell = {}
        for sym in symbols:
            cell_num = sym.get('cell', 0)
            if cell_num not in symbols_by_cell:
                symbols_by_cell[cell_num] = []
            symbols_by_cell[cell_num].append(sym)

        # Should have symbols from cells 1, 3, and 4 (markdown cell 2 is skipped)
        self.assertIn(1, symbols_by_cell, "Should have symbols from cell 1")
        self.assertIn(3, symbols_by_cell, "Should have symbols from cell 3")
        self.assertIn(4, symbols_by_cell, "Should have symbols from cell 4")
        self.assertNotIn(2, symbols_by_cell, "Should not have symbols from markdown cell 2")

        # Check line numbers are calculated correctly across cells
        cell4_symbols = symbols_by_cell[4]
        for sym in cell4_symbols:
            # Line numbers in cell 4 should be > lines from cells 1 and 3
            self.assertGreaterEqual(sym['line'], 4, "Line numbers should account for previous cells")

    def test_empty_notebook(self):
        """Test handling of empty notebook."""
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["Just a markdown cell"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["\n"]  # Empty code cell
            }
        ]

        test_file = self.create_test_notebook("empty.ipynb", cells)
        symbols = extract_symbols(test_file)

        # Should return empty list, not crash
        self.assertEqual(len(symbols), 0, "Empty notebook should have no symbols")

    def test_invalid_notebook(self):
        """Test handling of invalid notebook file."""
        test_file = self.test_dir / "invalid.ipynb"
        test_file.write_text("not valid json", encoding='utf-8')

        symbols = extract_symbols(test_file)

        # Should return empty list, not crash
        self.assertEqual(len(symbols), 0, "Invalid notebook should return empty list")

    def test_direct_function_call(self):
        """Test calling extract_symbols_from_notebook directly."""
        cells = [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def direct_test():\n",
                    "    return \"test\"\n"
                ]
            }
        ]

        test_file = self.create_test_notebook("direct.ipynb", cells)

        # Call the function directly
        symbols = extract_symbols_from_notebook(test_file)

        self.assertTrue(len(symbols) > 0, "Direct function call should work")
        self.assertEqual(symbols[0]['name'], 'direct_test', "Should find the test function")
        self.assertEqual(symbols[0]['cell'], 1, "Should track cell number")

    def test_notebook_with_mixed_content(self):
        """Test notebook with mixed markdown and code cells."""
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Introduction\n", "This is markdown."]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Setup - constants\n",
                    "DATA_DIR = 'data/'\n",
                    "import os\n",
                    "import sys\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Analysis"]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def analyze(data):\n",
                    "    \"\"\"Analyze the data.\"\"\"\n",
                    "    return len(data)\n",
                    "\n",
                    "result = analyze([1, 2, 3])\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Conclusion"]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Save results\n",
                    "OUTPUT_FILE = 'results.txt'\n",
                    "\n",
                    "def save_results(data, filename):\n",
                    "    with open(filename, 'w') as f:\n",
                    "        f.write(str(data))\n",
                    "\n",
                    "save_results(result, OUTPUT_FILE)\n"
                ]
            }
        ]

        test_file = self.create_test_notebook("mixed.ipynb", cells)
        symbols = extract_symbols(test_file)

        print("\n=== Jupyter Notebook (Mixed Content) ===")
        for sym in symbols:
            print(f"Cell {sym.get('cell', '?'):2d}, Line {sym['line']:3d}: {sym['type']:10s}: {sym['name']}")

        # Should find symbols from code cells 2, 4, and 6
        # Note: cell 2 has a DATA_DIR variable, cells 4 and 6 have functions/classes
        code_cells = [sym.get('cell') for sym in symbols]
        self.assertIn(2, code_cells, "Should have symbols from cell 2 (setup)")
        self.assertIn(4, code_cells, "Should have symbols from cell 4")
        self.assertIn(6, code_cells, "Should have symbols from cell 6")

        # Should not have symbols from markdown cells
        self.assertNotIn(1, code_cells, "Should not have symbols from markdown cell 1")
        self.assertNotIn(3, code_cells, "Should not have symbols from markdown cell 3")
        self.assertNotIn(5, code_cells, "Should not have symbols from markdown cell 5")

        # Check specific symbols
        func_names = [s['name'] for s in symbols if s['type'] == 'function']
        self.assertIn('analyze', func_names, "Should find analyze function")
        self.assertIn('save_results', func_names, "Should find save_results function")

        var_names = [s['name'] for s in symbols if s['type'] == 'variable']
        self.assertIn('DATA_DIR', var_names, "Should find DATA_DIR variable from cell 2")
        self.assertIn('OUTPUT_FILE', var_names, "Should find OUTPUT_FILE variable")
        self.assertIn('result', var_names, "Should find result variable")


if __name__ == '__main__':
    unittest.main(verbosity=2)

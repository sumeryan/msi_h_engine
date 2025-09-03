#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Formula Pre-Processor Module
----------------------------

This module is responsible for processing hierarchical formulas and extracting variables
from a tree-structured data source. It performs several key operations:

1. Loading tree data from a JSON file (tree_data.json)
2. Extracting and parsing formulas using the engine_parser module
3. Processing variables by analyzing the tree structure and applying filters
4. Saving the processed results to output JSON files

The module handles both simple variable references and complex aggregation functions,
supporting both global and ID-specific contexts. It processes each formula for each ID
in the tree, extracting relevant variable values according to the formula's structure.

Example workflow:
1. Load the tree data from JSON
2. Extract and parse formulas using the parser
3. Process each formula group for each ID
4. For each formula, extract variables both with and without aggregation
5. Save the processed results to the output file

This module is typically used as part of a larger hierarchical formula evaluation system.

Dependencies:
- filters.filters_paths: For filtering tree data based on paths and expressions
- engine_parser: For parsing formula syntax
- log.logger: For logging events and errors
"""
import json
import copy
from os import urandom
from pydoc import classify_class_attrs
from sqlite3.dbapi2 import Timestamp
import engine_entities
import engine_parser
import engine_eval
import update_tree
import engine_entities.engine_data, engine_entities.get_doctypes, engine_parser 
from typing import Dict, List, Any
from filters.filters_paths import tree_data_filter
from log.logger import get_logger
from variable_filter import FilterVariableExtractor
from engine_logger import EngineLogger
from formula_classifier import FormulaExecutionClassifier
from engine_entities.arteris_frappe import ArterisApi

class EngineProcessor(EngineLogger):

    def __init__(self):
        self.logger = get_logger("Engine - Processor")
        self.data_filter = tree_data_filter()

    def calculate_measurements(self, use_cached_data: bool = False):
        """
        Main function to orchestrate the formula pre-processing workflow.
        
        This function serves as the entry point for the formula pre-processing module,
        orchestrating the entire workflow:
        
        1. Load tree data from the JSON file
        2. Extract and parse formulas from the tree data
        3. Process formula variables for each formula and ID
        4. Save the results to the output JSON file
        
        The function handles errors at each step, logging them appropriately and
        preventing further processing if a critical error occurs.
        
        Returns:
            None
        """

        self.log_info("Starting formula pre-processing")

        # Engine processor
        entities_processor = engine_entities.get_doctypes.DoctypeProcessor()
        
        # Get formulas
        formulas = entities_processor.get_formula_data(using_cached_data=False)

        ufrappe = ArterisApi()

        # Get contract keys
        contracts = ufrappe.get_contracts()

        # Load and calculate tree data for each contract
        #for k in contract_keys:
            # 44149 10b3cd58-d02b-48f7-990f-78c7d3b3b741
            # 38733 ad3fb0c7-4e6b-4213-a59a-b57a21fe49ee      
            # 34540 019745f2-cb96-7782-9699-d5223234d984  
            # 40812 01974609-0a12-70e1-a32c-4fba54fa8939
            # 33287 019745f2-05db-7a62-8c75-619498b296e2
            # 32148 019745f1-74f1-7ba0-9b6b-c51aea37e953
            # 32904-RB 019745f1-b460-7603-9885-3df32abd1390
            # 34092 019745f2-7b66-7792-ad0f-8b1d17cdbe5f
            # 32570 019745f1-9759-72c2-a010-90c9d3dfeef3
            # 31824 019745f1-31b2-7bf3-9ed4-610c56cb4644
            # 32904-RB 019745f1-b460-7603-9885-3df32abd1390
            # 36534 01974601-6908-7420-9ec1-4c8851a0baca
            # 43135 0197460a-8f40-7483-9041-2d4e812b194d
            # 10000 01987fd2-8753-7cd0-8662-f3a2eae9ad4a
        contar = 1
        for c in contracts['contracts']: # ['01987fd2-8753-7cd0-8662-f3a2eae9ad4a']:

            self.log_info(f"{contar:03} de {len(contracts['contracts']):03} BM: {c['boletimmedicao']}")
            contar += 1

            engine_results_converted = []

            # # Update highways and cities records
            ufrappe.update_cities(c['boletimmedicao'])
            ufrappe.sumarize_measurement(c['boletimmedicao'])


if __name__ == "__main__":
    processor = EngineProcessor()
    try:
        processor.calculate_measurements(use_cached_data=True)
    except Exception as e:
        processor.log_error(f"An error occurred during formula processing: {e}")
        raise
    finally:
        processor.log_info("Formula processing completed.") 
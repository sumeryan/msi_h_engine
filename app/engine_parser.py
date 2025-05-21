#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Formula Parser Module
--------------------

This module contains functions to parse formulas and efficiently extract aggregation functions,
their associated variables, and filters.

The module provides functionality to:
1. Parse and analyze mathematical formulas with aggregation functions
2. Extract variables, aggregation functions, and their filters
3. Create dependency graphs for formula evaluation
4. Recursively extract and process formulas from hierarchical data structures

Supported aggregation functions are defined in the configuration file.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from app.config import get_config
from app.log.logger import get_logger
from app.engine_dag import get_ordered_formulas

# Initialize logger for this module
logger = get_logger("formula_parser")


class FormulaParser:
    """
    Class for parsing formulas and extracting their aggregation functions.
    
    This class implements an efficient parser using regular expressions and token analysis
    to identify aggregation functions, extract variables, and handle nested structures
    in mathematical formulas.
    
    The parser supports:
    - Detection of aggregation functions from a configurable list
    - Extraction of variables from formulas
    - Analysis of filter expressions within aggregation functions
    - Balanced parentheses parsing for nested expressions
    """
    
    
    def __init__(self):
        """
        Initialize the parser with allowed aggregation functions from configuration.
        
        Loads the list of allowed aggregation functions from the application configuration
        and compiles regular expression patterns for efficient formula parsing.
        """
        logger.debug("Initializing FormulaParser")
        config = get_config()
        self.safe_aggr_functions = config.safe_aggr_functions
        self.safe_custom_functions = config.safe_custom_functions
        
        logger.debug(f"Loaded aggregation functions: {self.safe_aggr_functions}")
        logger.debug(f"Loaded custom functions: {self.safe_custom_functions}")
        
        # Pattern to identify variables in e12345v format
        self.var_pattern = re.compile(r'e\d{5}v')
        logger.debug("Compiled variable pattern: e\\d{5}v")
        
        # Create efficient regex patterns to identify aggregation functions
        self._compile_patterns()
    
    def _compile_patterns(self):
        """
        Compile regex patterns to identify aggregation functions and their arguments.
        
        Creates regular expression patterns for:
        1. Detecting aggregation functions with their arguments and filters
        2. Identifying custom functions used in filter expressions
        
        These patterns are used throughout the parsing process for efficient formula analysis.
        """
        logger.debug("Compiling regex patterns for function detection")
        
        # Create pattern for aggregation functions
        aggr_funcs = '|'.join(self.safe_aggr_functions)
        pattern = rf'({aggr_funcs})\s*\((.*?)(?:,\s*(.*?))?\)'
        self.aggr_pattern = re.compile(pattern, re.DOTALL)
        logger.debug(f"Compiled aggregation pattern: {pattern}")
        
        # Pattern to find custom functions in filters
        custom_funcs = '|'.join(self.safe_custom_functions)
        custom_pattern = rf'({custom_funcs})\s*\((.*?)\)'
        self.custom_func_pattern = re.compile(custom_pattern, re.DOTALL)
        logger.debug(f"Compiled custom function pattern: {custom_pattern}")
    
    def extract_variables(self, expression: str) -> List[str]:
        """
        Extracts variables (e.g., e00001v) from an expression.
        
        Identifies all variables in the expression matching the pattern 'e' followed by exactly
        5 digits and then 'v', and returns a list of unique variables found.
        
        Args:
            expression: The expression to analyze
            
        Returns:
            List of unique variables found while preserving their original order
        """
        if not expression:
            logger.debug("Empty expression provided, returning empty variables list")
            return []
        
        logger.debug(f"Extracting variables from: {expression}")
        
        # Find all variables
        variables = self.var_pattern.findall(expression)
        logger.debug(f"Found {len(variables)} variables (with duplicates): {variables}")
        
        # Remove duplicates while preserving order
        unique_vars = []
        for var in variables:
            if var not in unique_vars:
                unique_vars.append(var)
        
        logger.debug(f"Extracted {len(unique_vars)} unique variables: {unique_vars}")
        return unique_vars
    
    def _fix_comparison_operators(self, str_expr):
        """
        Replaces invalid occurrences of '=' with '==' in an expression string.
        
        Ensures that only comparisons are adjusted, avoiding multiple '==' in sequence.
        This is necessary because users sometimes use a single equals sign for comparisons
        instead of the required double equals.
        
        Args:
            str_expr: The expression string to fix
            
        Returns:
            The expression with properly corrected comparison operators
        """
        if not str_expr:
            logger.debug("Empty expression provided to fix comparison operators")
            return str_expr
            
        logger.debug(f"Fixing comparison operators in: {str_expr}")
        import re
        
        # Substitutes '=' with '==' only when not part of '==' or '===' and avoids duplication
        result = re.sub(r'(?<![=!<>])=(?![=])', '==', str_expr).replace('== ==', '==')
        
        if result != str_expr:
            logger.debug(f"Fixed comparison operators: '{str_expr}' -> '{result}'")
        else:
            logger.debug("No comparison operators needed fixing")
            
        return result

    def _parse_aggregate_call(self, match) -> Dict:
        """
        Analyzes an aggregation function call and extracts its components.
        
        Parses a regex match of an aggregation function, extracting:
        - Function name
        - Main argument expression
        - Filter expression (if present)
        - Variables in the argument and filter
        
        Args:
            match: Regex match object containing the captured groups
            
        Returns:
            Dictionary with information about the aggregation function
        """
        logger.debug("Parsing aggregate function call from regex match")
        
        func_name = match.group(1)
        arg_expr = match.group(2).strip() if match.group(2) else ""
        filter_expr = match.group(3).strip() if match.group(3) else ""
        filter_expr = self._fix_comparison_operators(filter_expr)
    
        logger.debug(f"Function name: {func_name}")
        logger.debug(f"Argument expression: {arg_expr}")
        logger.debug(f"Filter expression: {filter_expr}")
        
        # Extract variables from the main argument
        arg_vars = self.extract_variables(arg_expr)
        
        # Extract variables from the filter
        filter_vars = self.extract_variables(filter_expr)
        
        # Build the complete function as a string
        full_func = f"{func_name}({arg_expr}"
        if filter_expr:
            full_func += f", {filter_expr}"
        full_func += ")"
        
        logger.debug(f"Full function string: {full_func}")
        
        return {
            "formula": full_func,
            "vars": arg_vars,
            "filter": filter_expr,
            "filter_vars": filter_vars
        }
    
    def balance_parentheses(self, expression: str, start_idx: int) -> Tuple[int, str]:
        """
        Finds the index of the corresponding closing parenthesis and extracts the subexpression.
        
        Uses a stack-based approach to match opening and closing parentheses, ensuring
        nested parentheses are correctly handled.
        
        Args:
            expression: The complete expression
            start_idx: Index of the opening parenthesis
            
        Returns:
            Tuple with the index of the closing parenthesis and the subexpression
        """
        if start_idx >= len(expression) or expression[start_idx] != '(':
            logger.warning(f"Invalid start index {start_idx} for parenthesis balancing")
            return -1, ""
        
        logger.debug(f"Balancing parentheses starting at index {start_idx} in: {expression[start_idx:start_idx+20]}...")
        
        stack = []
        for i in range(start_idx, len(expression)):
            if expression[i] == '(':
                stack.append('(')
                logger.debug(f"Found opening parenthesis at index {i}, stack depth: {len(stack)}")
            elif expression[i] == ')':
                if stack:
                    stack.pop()
                    logger.debug(f"Found closing parenthesis at index {i}, stack depth after pop: {len(stack)}")
                    if not stack:  # Balanced parentheses
                        subexpr = expression[start_idx+1:i]
                        logger.debug(f"Balanced parentheses: closing at index {i}, extracted: {subexpr[:20]}...")
                        return i, subexpr
        
        logger.warning(f"Unbalanced parentheses starting at index {start_idx} in: {expression[start_idx:]}")
        return -1, ""  # Unbalanced parentheses
    
    def find_top_level_commas(self, expr: str) -> List[int]:
        """
        Finds positions of commas at the top level (not inside parentheses).
        
        This is essential for separating the main arguments from filter expressions in
        aggregation functions.
        
        Args:
            expr: The expression to analyze
            
        Returns:
            List of indices of top-level commas
        """
        logger.debug(f"Finding top-level commas in: {expr[:20]}...")
        
        comma_positions = []
        paren_level = 0
        
        for i, char in enumerate(expr):
            if char == '(':
                paren_level += 1
                logger.debug(f"Found open parenthesis at {i}, level increased to {paren_level}")
            elif char == ')':
                paren_level -= 1
                logger.debug(f"Found close parenthesis at {i}, level decreased to {paren_level}")
            elif char == ',' and paren_level == 0:
                logger.debug(f"Found top-level comma at position {i}")
                comma_positions.append(i)
        
        logger.debug(f"Found {len(comma_positions)} top-level commas at positions: {comma_positions}")
        return comma_positions
    
    def parse_aggregate_functions(self, formula: str) -> List[Dict]:
        """
        Extracts aggregation functions and their associated variables from a formula.
        
        Implements a token-based approach and parenthesis analysis
        to correctly handle filters and nested functions.
        
        Args:
            formula: The formula to analyze
            
        Returns:
            List of dictionaries with information about the aggregation functions found
        """
        logger.debug(f"Analyzing formula: {formula}")
        
        if not formula:
            logger.debug("Empty formula provided, returning empty list")
            return []
        
        logger.info(f"Parsing formula for aggregation functions: {formula[:50]}...")
        
        # Result
        aggregations = []
        
        # Current position in the formula
        pos = 0
        formula_len = len(formula)
        
        while pos < formula_len:
            # Search for aggregation function names
            found_func = None
            for func_name in self.safe_aggr_functions:
                if formula[pos:].startswith(func_name) and pos + len(func_name) < formula_len:
                    # Check if followed by an opening parenthesis
                    next_pos = pos + len(func_name)
                    
                    # Skip whitespace
                    while next_pos < formula_len and formula[next_pos].isspace():
                        next_pos += 1
                    
                    if next_pos < formula_len and formula[next_pos] == '(':
                        logger.debug(f"Found aggregation function '{func_name}' at position {pos}")
                        found_func = func_name
                        pos = next_pos
                        break
            
            if found_func:
                # Found an aggregation function, now we need to extract its arguments
                # Find the corresponding closing parenthesis
                closing_paren_pos, content = self.balance_parentheses(formula, pos)
                
                if closing_paren_pos != -1:
                    logger.debug(f"Successfully balanced parentheses, content length: {len(content)}")
                    
                    # Find top-level commas to separate arguments from filters
                    comma_positions = self.find_top_level_commas(content)
                    
                    if comma_positions:
                        # There's a top-level comma, separate the argument from the filter
                        arg_expr = content[:comma_positions[0]].strip()
                        filter_expr = content[comma_positions[0]+1:].strip()
                        logger.debug(f"Found filter expression: {filter_expr}")
                    else:
                        # No filter
                        arg_expr = content.strip()
                        filter_expr = ""
                        logger.debug("No filter expression found")
                    
                    # Extract variables from argument and filter
                    arg_vars = self.extract_variables(arg_expr)
                    filter_vars = self.extract_variables(filter_expr)
                    
                    logger.debug(f"Argument variables: {arg_vars}")
                    logger.debug(f"Filter variables: {filter_vars}")
                    
                    full_func = f"{found_func}({content})"
                    logger.debug(f"Full function: {full_func}")

                    # Build the aggregation object
                    # Include aggregation function without the internal filter
                    if found_func in ["first", "last", "firstc", "lastc"]:
                        # Special case for first/last functions
                        base_func = f"{arg_expr}"   
                        logger.debug(f"Special case for {found_func}, base function: {base_func}")                     
                    else:
                        base_func = f"{found_func.replace('_node','')}({arg_expr})"
                        logger.debug(f"Standard case, base function: {base_func}")
                    
                    filter_expr = self._fix_comparison_operators(filter_expr)
                    logger.debug(f"Fixed filter expression: {filter_expr}")

                    aggr_obj = {
                        "base": full_func,  # Aggregation without filter
                        "eval": base_func,
                        "vars": arg_vars,
                        "global": (not "_node" in base_func),
                        "filter": filter_expr,
                        "filter_vars": filter_vars
                    }
                    
                    aggregations.append(aggr_obj)
                    logger.debug(f"Added aggregation function: {found_func}")
                    
                    pos = closing_paren_pos + 1
                    logger.debug(f"Updated position to {pos}")
                else:
                    # Unbalanced parentheses, move to next character
                    logger.warning(f"Unbalanced parentheses at position {pos}, skipping character")
                    pos += 1
            else:
                # No aggregation function found, move to next character
                pos += 1
        
        logger.info(f"Found {len(aggregations)} aggregation functions in the formula")
        return aggregations
    
    def extract_non_aggregated_variables(self, formula: str, aggr_vars: List[str], filter_vars: List[str]) -> List[str]:
        """
        Extracts variables that are not part of aggregation functions.
        
        Identifies variables in the formula that are not already accounted for in
        aggregation functions or filters, which are likely used directly in calculations.
        
        Args:
            formula: The complete formula
            aggr_vars: Variables already identified in aggregation functions
            filter_vars: Variables used in filter conditions
            
        Returns:
            List of variables that are not in aggregation functions or filters
        """
        logger.debug(f"Extracting non-aggregated variables from formula")
        
        # Find all variables in the formula
        all_vars = set(self.extract_variables(formula))
        logger.debug(f"All variables in formula: {all_vars}")
        
        # Remove variables already present in aggregation functions or filters
        aggr_set = set(aggr_vars)
        filter_set = set(filter_vars)
        
        logger.debug(f"Aggregation variables to exclude: {aggr_set}")
        logger.debug(f"Filter variables to exclude: {filter_set}")
        
        # Variables that are not in aggregation functions or filters
        other_vars = all_vars - aggr_set - filter_set
        
        logger.debug(f"Non-aggregated variables: {other_vars}")
        return list(other_vars)
    
    def analyze_formula(self, formula_str: str) -> Dict:
        """
        Analyzes a complete formula and extracts all aggregation functions and variables.
        
        Performs a comprehensive analysis of the formula, identifying:
        - All aggregation functions and their components
        - Variables used in aggregation functions and their filters
        - Variables used directly in the formula (not in aggregations)
        - Creates a dependency graph (DAG) for formula evaluation
        
        Args:
            formula_str: The formula to analyze
            
        Returns:
            Dictionary with aggregation functions, their variables, and other variables
        """
        logger.info(f"Analyzing formula: {formula_str[:50]}...")
        
        # Initialize lists to store results
        aggr_functions = []
        all_aggr_vars = []
        all_filter_vars = []
        dag_paths = []
        
        # Extract aggregation functions
        aggregations = self.parse_aggregate_functions(formula_str)
        logger.debug(f"Found {len(aggregations)} aggregation functions")
        
        # Process the aggregation functions found
        logger.debug("Processing aggregation functions")
        for idx, aggr in enumerate(aggregations):
            logger.debug(f"Processing aggregation function {idx+1}/{len(aggregations)}")
            aggr_functions.append(aggr)
            all_aggr_vars.extend(aggr["vars"])
            all_filter_vars.extend(aggr["filter_vars"])
            
            # Add variables to DAG paths
            dag_paths.extend(aggr["vars"])
            dag_paths.extend(aggr["filter_vars"])
        
        # Remove duplicates while preserving order
        logger.debug("Removing duplicates from variable lists")
        unique_aggr_vars = []
        for var in all_aggr_vars:
            if var not in unique_aggr_vars:
                unique_aggr_vars.append(var)
                
        unique_filter_vars = []
        for var in all_filter_vars:
            if var not in unique_filter_vars:
                unique_filter_vars.append(var)
        
        logger.debug(f"Unique aggregation variables: {unique_aggr_vars}")
        logger.debug(f"Unique filter variables: {unique_filter_vars}")
        
        # Extract non-aggregated variables
        logger.debug("Extracting non-aggregated variables")
        other_vars = self.extract_non_aggregated_variables(
            formula_str, unique_aggr_vars, unique_filter_vars
        )
        logger.debug(f"Non-aggregated variables: {other_vars}")
        
        # Add other variables to DAG paths
        dag_paths.extend(other_vars)
        
        # Remove duplicates from DAG paths while preserving order
        logger.debug("Building final DAG paths list")
        unique_dag_paths = []
        for path in dag_paths:
            if path not in unique_dag_paths:
                unique_dag_paths.append(path)
        
        logger.debug(f"Final DAG paths: {unique_dag_paths}")
        
        # Build the final result
        result = {
            "aggr": aggr_functions,
            "vars": other_vars,
            "dag_paths": unique_dag_paths
        }
        
        logger.info("Formula analysis complete")
        return result


# Main function for external use
def parse_formula(formula: str) -> Dict:
    """
    Parses a formula and extracts its aggregation functions, variables, and DAG paths.
    
    This is the main entry point for formula parsing, creating a FormulaParser instance
    and using it to analyze the formula.
    
    Args:
        formula: The formula to analyze
        
    Returns:
        Dictionary with aggregation functions, their variables, and DAG paths
    """
    logger.info(f"Parsing formula: {formula[:50]}...")
    parser = FormulaParser()
    result = parser.analyze_formula(formula)
    logger.info("Formula parsing complete")
    return result

def extract_formulas(data: Any, results_dict: Optional[Dict[str, Dict]] = None) -> List[Dict]:
    """
    Recursively extract formulas from the tree data structure.
    
    This function traverses the data structure, identifying entities with formulas
    and collecting them into a results dictionary keyed by entity path to avoid duplicates.
    
    The function handles hierarchical data structures, recursively exploring nested
    objects and arrays to find all formula definitions.
    
    Args:
        data: The data object to process (can be a dict or list)
        results_dict: The dictionary to store results by path (to avoid duplicates)
        
    Returns:
        List of entities with their formulas and IDs
    """

    # Initialize results dictionary if not provided
    if results_dict is None:
        results_dict = {}
        logger.debug("Initializing new results dictionary")
    
    # Process data list by recursively calling extract_formulas on each item
    if isinstance(data, list):
        logger.debug(f"Processing list of {len(data)} items")
        for idx, item in enumerate(data):
            logger.debug(f"Processing list item {idx+1}/{len(data)}")
            extract_formulas(item, results_dict)
        logger.debug(f"Finished processing list, returning {len(results_dict)} results")
        return list(results_dict.values())
            
    # Process data object (dictionary)
    if isinstance(data, dict):
        # Check if this is an entity with formulas
        if "path" in data and "formulas" in data and "data" in data:
            path = data["path"]
            formulas = data.get("formulas", [])
            
            # Only process if it has formulas
            if formulas:
                logger.info(f"Found entity with path '{path}' containing {len(formulas)} formulas")
                
                # Extract IDs from data
                ids = []
                for item in data.get("data", []):
                    if "id" in item and item["id"]:  # Only add non-null IDs
                        ids.append({"id": item["id"]})
                
                logger.debug(f"Extracted {len(ids)} IDs for entity '{path}'")
                
                # Create or update the entity in results_dict
                if path in results_dict:
                    # If the entity already exists, merge the formulas and IDs
                    logger.info(f"Merging duplicated entity '{path}'")
                    existing = results_dict[path]
                    
                    # Add new formulas if they don't already exist
                    existing_formula_paths = {f["path"] for f in existing["formulas"]}
                    formulas_added = 0
                    
                    for formula in formulas:
                        if formula["path"] not in existing_formula_paths:
                            existing["formulas"].append(formula)
                            existing_formula_paths.add(formula["path"])
                            formulas_added += 1
                    
                    logger.debug(f"Added {formulas_added} new formulas to existing entity '{path}'")
                    
                    # Add new IDs if they don't already exist
                    existing_ids = {id_obj["id"] for id_obj in existing["ids"]}
                    ids_added = 0
                    
                    for id_obj in ids:
                        if id_obj["id"] not in existing_ids:
                            existing["ids"].append(id_obj)
                            existing_ids.add(id_obj["id"])
                            ids_added += 1
                    
                    logger.debug(f"Added {ids_added} new IDs to existing entity '{path}'")
                else:
                    # Add the entity with its formulas and IDs to results
                    logger.debug(f"Adding new entity '{path}' to results")
                    results_dict[path] = {
                        "path": path,
                        "formulas": formulas,
                        "ids": ids
                    }
            
            # Continue recursively processing the data field
            logger.debug(f"Recursively processing 'data' field of entity '{path}'")
            extract_formulas(data.get("data", []), results_dict)
        
        # Process other fields that might contain nested data
        for key, value in data.items():
            if isinstance(value, (dict, list)) and key != "formulas":
                logger.debug(f"Processing nested field '{key}'")
                extract_formulas(value, results_dict)

    return list(results_dict.values())

def parse_formulas(data: Any) -> List[Dict]:
    """
    Extract, parse, and order formulas from the data structure.
    
    This function provides a complete pipeline for formula processing:
    1. Extract formulas from the hierarchical data structure
    2. Parse each formula to identify its components (variables, aggregations, filters)
    3. Order the formulas based on their dependencies for proper evaluation
    
    Args:
        data: The data object to process (can be a dict or list)
        
    Returns:
        List of entities with their formulas and IDs, ordered for execution
    """
    logger.info("Extracting formulas from data structure")
    results = extract_formulas(data)
    logger.info(f"Extracted {len(results)} formula groups")

    # Parse each formula to extract aggregation functions and variables
    formula_count = 0
    for r in results:
        group_path = r.get("path", "unknown")
        formulas = r.get("formulas", [])
        logger.info(f"Processing group '{group_path}' with {len(formulas)} formulas")
        
        for f in formulas:
            formula_path = f.get("path", "unknown")
            formula_value = f.get("value", "")
            logger.debug(f"Parsing formula '{formula_path}': {formula_value[:50]}...")
            
            try:
                f["parsed"] = parse_formula(formula_value)
                formula_count += 1
                logger.debug(f"Successfully parsed formula '{formula_path}'")
            except Exception as e:
                logger.error(f"Error parsing formula '{formula_path}': {e}", exc_info=True)
    
    logger.info(f"Successfully parsed {formula_count} formulas")

    # Order formulas based on dependencies
    logger.info("Ordering formulas based on dependencies")
    try:
        ordered_results = get_ordered_formulas(results)
        logger.info("Formula ordering complete")
    except Exception as e:
        logger.error(f"Error ordering formulas: {e}", exc_info=True)
        ordered_results = results
        logger.warning("Using unordered formulas due to ordering error")

    return ordered_results

# Function for direct module testing
if __name__ == "__main__":
    # Configure logging for console output
    logger = get_logger("Formula Parser")
    logger.info("Starting formula parser module test")
    
    input_path = os.path.join(os.path.dirname(__file__), "tree_data.json")
    output_path = os.path.join(os.path.dirname(__file__), "extracted_formulas.json")

    logger.info(f"Loading data from {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            logger.debug("Reading input file")
            data = json.load(f)    
        logger.info(f"Successfully loaded data from {input_path}")
        
        logger.info("Parsing and ordering formulas")
        results = parse_formulas(data)
        logger.info(f"Successfully parsed and ordered {len(results)} formula groups")

        logger.info(f"Writing results to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            logger.debug("Writing output file")
            json.dump(results, f, indent=4, ensure_ascii=False)        
        logger.info(f"Successfully wrote results to {output_path}")
        
        print(f"Processed formulas saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error processing formulas: {e}", exc_info=True)
        print(f"Error: {e}")
    
    logger.info("Formula parser completed")
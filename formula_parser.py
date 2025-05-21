#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formula Parser Module
--------------------
Powered by Renoir
Created by igor.goncalves@renoirgroup.com

This module contains functions to parse formulas and efficiently extract aggregation functions,
their associated variables, and filters.

Supported aggregation functions are defined in the configuration file.
"""

import json
import os
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from config import get_config
from log.logger import get_logger
from formulas_dag import get_ordered_formulas
from log import get_logger

# Initialize logger for this module
logger = get_logger("formula_parser")


class FormulaParser:
    """
    Class for parsing formulas and extracting their aggregation functions.
    Implements an efficient parser using regular expressions and token analysis.
    """
    
    
    def __init__(self):
        """Initialize the parser with allowed aggregation functions from configuration."""
        logger.debug("Initializing FormulaParser")
        config = get_config()
        self.safe_aggr_functions = config.safe_aggr_functions
        self.safe_custom_functions = config.safe_custom_functions
        
        logger.debug(f"Loaded aggregation functions: {self.safe_aggr_functions}")
        logger.debug(f"Loaded custom functions: {self.safe_custom_functions}")
        
        # Pattern to identify variables in e12345v format
        self.var_pattern = re.compile(r'e\d{5}v')
        
        # Create efficient regex patterns to identify aggregation functions
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns to identify aggregation functions and their arguments."""
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
        
        Args:
            expression: The expression to analyze
            
        Returns:
            List of unique variables found
        """
        if not expression:
            return []
        
        logger.debug(f"Extracting variables from: {expression}")
        
        # Find all variables
        variables = self.var_pattern.findall(expression)
        
        # Remove duplicates while preserving order
        unique_vars = []
        for var in variables:
            if var not in unique_vars:
                unique_vars.append(var)
        
        logger.debug(f"Extracted variables: {unique_vars}")
        return unique_vars
    
    def _fix_comparison_operators(self, str_expr):
        """
        Substitui ocorrências inválidas de '=' por '==' em uma string de expressão.
        Garante que apenas comparações sejam ajustadas, evitando múltiplos '==' consecutivos.
        """
        import re
        # Substitui '=' por '==' apenas quando não for parte de '==' ou '===' e evita duplicação
        return re.sub(r'(?<![=!<>])=(?![=])', '==', str_expr).replace('== ==', '==')

    def _parse_aggregate_call(self, match) -> Dict:
        """
        Analisa uma chamada de função de agregação e extrai seus componentes.
        
        Args:
            match: Match object da regex contendo os grupos capturados
            
        Returns:
            Dicionário com informações sobre a função de agregação
        """
        func_name = match.group(1)
        arg_expr = match.group(2).strip() if match.group(2) else ""
        filter_expr = match.group(3).strip() if match.group(3) else ""
        filter_expr = self._fix_comparison_operators(filter_expr)
    
        # Extrai variáveis do argumento principal
        arg_vars = self.extract_variables(arg_expr)
        
        # Extrai variáveis do filtro
        filter_vars = self.extract_variables(filter_expr)
        
        # Monta a função completa como string
        full_func = f"{func_name}({arg_expr}"
        if filter_expr:
            full_func += f", {filter_expr}"
        full_func += ")"
        
        return {
            "formula": full_func,
            "vars": arg_vars,
            "filter": filter_expr,
            "filter_vars": filter_vars
        }
    
    def balance_parentheses(self, expression: str, start_idx: int) -> Tuple[int, str]:
        """
        Finds the index of the corresponding closing parenthesis and extracts the subexpression.
        
        Args:
            expression: The complete expression
            start_idx: Index of the opening parenthesis
            
        Returns:
            Tuple with the index of the closing parenthesis and the subexpression
        """
        if start_idx >= len(expression) or expression[start_idx] != '(':
            return -1, ""
        
        logger.debug(f"Balancing parentheses starting at index {start_idx} in: {expression[start_idx:start_idx+20]}...")
        
        stack = []
        for i in range(start_idx, len(expression)):
            if expression[i] == '(':
                stack.append('(')
            elif expression[i] == ')':
                if stack:
                    stack.pop()
                    if not stack:  # Balanced parentheses
                        subexpr = expression[start_idx+1:i]
                        logger.debug(f"Balanced parentheses: closing at index {i}, extracted: {subexpr[:20]}...")
                        return i, subexpr
        
        logger.warning(f"Unbalanced parentheses starting at index {start_idx} in: {expression[start_idx:]}")
        return -1, ""  # Unbalanced parentheses
    
    def find_top_level_commas(self, expr: str) -> List[int]:
        """
        Finds positions of commas at the top level (not inside parentheses).
        
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
            elif char == ')':
                paren_level -= 1
            elif char == ',' and paren_level == 0:
                logger.debug(f"Found top-level comma at position {i}")
                comma_positions.append(i)
        
        logger.debug(f"Found {len(comma_positions)} top-level commas")
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
        logger.debug(f"Analisando fórmula: {formula}")
        
        if not formula:
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
                    
                    # Build the aggregation object
                    # Include aggregation function without the internal filter
                    base_func = f"{found_func}({arg_expr})"
                    full_func = f"{found_func}({content})"
                    
                    logger.debug(f"Base function: {base_func}")
                    logger.debug(f"Full function: {full_func}")

                    filter_expr = self._fix_comparison_operators(filter_expr)

                    aggr_obj = {
                        "base": base_func,  # Aggregation without filter
                        "vars": arg_vars,
                        "global": (not "_node" in base_func),
                        "filter": filter_expr,
                        "filter_vars": filter_vars
                    }
                    
                    aggregations.append(aggr_obj)
                    logger.debug(f"Added aggregation function: {found_func}")
                    
                    pos = closing_paren_pos + 1
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
        
        # Process the aggregation functions found
        logger.debug("Processing aggregation functions")
        for aggr in aggregations:
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
        
        # Extract non-aggregated variables
        logger.debug("Extracting non-aggregated variables")
        other_vars = self.extract_non_aggregated_variables(
            formula_str, unique_aggr_vars, unique_filter_vars
        )
        
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
        for item in data:
            extract_formulas(item, results_dict)
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
    
    This function extracts formulas from the data structure, parses each formula to identify
    its components, and then orders the formulas based on their dependencies.
    
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
            logger.debug(f"Parsing formula '{formula_path}': {f.get('value', '')[:50]}...")
            f["parsed"] = parse_formula(f["value"])
            formula_count += 1
    
    logger.info(f"Successfully parsed {formula_count} formulas")

    # Order formulas based on dependencies
    logger.info("Ordering formulas based on dependencies")
    ordered_results = get_ordered_formulas(results)
    logger.info("Formula ordering complete")

    return ordered_results

# Function for direct module testing
if __name__ == "__main__":
    # Configure logging for console output

    logger = get_logger("Formula Parser")
    
    input_path = os.path.join(os.path.dirname(__file__), "tree_data.json")
    output_path = os.path.join(os.path.dirname(__file__), "extracted_formulas.json")

    logger.info(f"Loading data from {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)    
        logger.info(f"Successfully loaded data from {input_path}")
        
        logger.info("Parsing and ordering formulas")
        results = parse_formulas(data)
        logger.info(f"Successfully parsed and ordered {len(results)} formula groups")

        logger.info(f"Writing results to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)        
        logger.info(f"Successfully wrote results to {output_path}")
        
        print(f"Processed formulas saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error processing formulas: {e}", exc_info=True)
        print(f"Error: {e}")
    
    logger.info("Formula parser completed")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filters Module
-------------
This module contains functions to filter and extract variables from tree data based on parsed formulas.
"""

import json
import re
from typing import List, Dict, Any, Union, Optional, Tuple

class FormulaVariableFilter:
    """
    Class to filter and extract variables from tree data based on parsed formulas.
    """
    
    def __init__(self, tree_data: Dict[str, Any]):
        """
        Initialize the filter with tree data.
        
        Args:
            tree_data: The hierarchical tree data structure
        """
        self.tree_data = tree_data
        
    def _find_variable_value(self, var_path: str, id_data: Dict[str, Any]) -> Optional[Any]:
        """
        Find the value of a variable in the given id data.
        
        Args:
            var_path: The path of the variable to find (e.g., e00099v)
            id_data: The data associated with a specific ID
            
        Returns:
            The value of the variable, or None if not found
        """
        # Find node values recursively
        def find_value_recursive(data):
            if isinstance(data, dict):
                if data.get("path") == var_path and "value" in data:
                    return data["value"]
                
                # Check fields
                fields = data.get("fields", [])
                for field in fields:
                    if field.get("path") == var_path and "value" in field:
                        return field["value"]
                
                # Check nested data
                if "data" in data:
                    for item in data["data"]:
                        result = find_value_recursive(item)
                        if result is not None:
                            return result
            
            elif isinstance(data, list):
                for item in data:
                    result = find_value_recursive(item)
                    if result is not None:
                        return result
            
            return None
        
        return find_value_recursive(id_data)

    def _find_all_values(self, var_path: str, data: Dict[str, Any]) -> List[Any]:
        """
        Find all values of a variable in the entire tree.
        
        Args:
            var_path: The path of the variable to find (e.g., e00099v)
            data: The data structure to search in
            
        Returns:
            A list of all values found
        """
        values = []
        
        def collect_values_recursive(node):
            if isinstance(node, dict):
                if node.get("path") == var_path and "value" in node:
                    values.append(node["value"])
                
                # Check fields
                fields = node.get("fields", [])
                for field in fields:
                    if field.get("path") == var_path and "value" in field:
                        values.append(field["value"])
                
                # Check nested data
                if "data" in node:
                    for item in node["data"]:
                        collect_values_recursive(item)
            
            elif isinstance(node, list):
                for item in node:
                    collect_values_recursive(item)
        
        collect_values_recursive(data)
        return values

    def _find_filtered_values(self, var_path: str, filter_expr: str, 
                              filter_vars: List[str], id_data: Dict[str, Any]) -> List[Any]:
        """
        Find values of a variable that match the given filter expression.
        
        Args:
            var_path: The path of the variable to find values for
            filter_expr: The filter expression (e.g., "e00083v == 'Não'")
            filter_vars: The variables used in the filter expression
            id_data: The data associated with a specific ID
            
        Returns:
            A list of values that match the filter
        """
        values = []
        
        # Process simple equality filter like "e00083v == 'Não'"
        equality_pattern = re.compile(r'(\w+)\s*==\s*[\'\"]([^\'\"]+)[\'\"]')
        # Process contains filter like "contains(e00083v, 'Sim')"
        contains_pattern = re.compile(r'contains\((\w+),\s*[\'\"]([^\'\"]+)[\'\"]\)')
        
        def evaluate_filter(node):
            # Extract filter conditions
            match = None
            filter_var = None
            expected_value = None
            is_contains = False
            
            if match := equality_pattern.search(filter_expr):
                filter_var = match.group(1)
                expected_value = match.group(2)
            elif match := contains_pattern.search(filter_expr):
                filter_var = match.group(1)
                expected_value = match.group(2)
                is_contains = True
            
            if not match:
                return True  # No filter condition found, include all values
            
            # Get the filter variable value from the current node
            value = None
            if isinstance(node, dict):
                # Check fields
                fields = node.get("fields", [])
                for field in fields:
                    if field.get("path") == filter_var:
                        value = field.get("value")
                        break
            
            # Evaluate the filter condition
            if value is None:
                return False
            
            if is_contains:
                return expected_value in str(value)
            else:
                return str(value) == expected_value
        
        def collect_filtered_values(node):
            if isinstance(node, dict):
                # Check if this node matches the filter
                if evaluate_filter(node):
                    # Find the target variable value
                    for field in node.get("fields", []):
                        if field.get("path") == var_path and "value" in field:
                            values.append(field["value"])
                
                # Recursively process child nodes
                for child in node.get("data", []):
                    collect_filtered_values(child)
            
            elif isinstance(node, list):
                for item in node:
                    collect_filtered_values(item)
        
        collect_filtered_values(id_data)
        return values

    def extract_variables_for_formula(self, formula: Dict[str, Any], id_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract variables for a specific formula and ID.
        
        Args:
            formula: The formula definition with path, value, and parsed information
            id_obj: The ID object to extract variables for
            
        Returns:
            Dictionary with variable values
        """
        # Find the ID data in the tree
        id_value = id_obj["id"]
        id_data = self._find_id_data(id_value)
        
        if not id_data:
            return {}
        
        result = {
            "path": formula["path"],
            "vars": {}
        }
        
        # Process aggregation functions
        for aggr in formula.get("parsed", {}).get("aggr", []):
            var_path = aggr["vars"][0] if aggr["vars"] else None
            filter_expr = aggr["filter"]
            filter_vars = aggr["filter_vars"]
            
            if var_path:
                # If there's a filter, apply it to get filtered values
                if filter_expr:
                    values = self._find_filtered_values(var_path, filter_expr, filter_vars, id_data)
                else:
                    # Otherwise get all values for this ID
                    values = self._find_all_values(var_path, id_data)
                
                result["vars"][var_path] = values
        
        # Process regular variables (non-aggregated)
        for var_path in formula.get("parsed", {}).get("vars", []):
            # Get the first value found for this variable
            value = self._find_variable_value(var_path, id_data)
            if value is not None:
                result["vars"][var_path] = value
        
        return result

    def _find_id_data(self, id_value: str) -> Optional[Dict[str, Any]]:
        """
        Find the data associated with a specific ID in the tree.
        
        Args:
            id_value: The ID to search for
            
        Returns:
            The data associated with the ID, or None if not found
        """
        def find_id_recursive(data):
            if isinstance(data, dict):
                if data.get("id") == id_value:
                    return data
                
                # Check nested data
                if "data" in data:
                    for item in data["data"]:
                        result = find_id_recursive(item)
                        if result is not None:
                            return result
            
            elif isinstance(data, list):
                for item in data:
                    result = find_id_recursive(item)
                    if result is not None:
                        return result
            
            return None
        
        # Start with the "dados" section of the tree
        for section in self.tree_data.get("dados", []):
            result = find_id_recursive(section)
            if result is not None:
                return result
        
        return None

def load_tree_data(file_path: str) -> Dict[str, Any]:
    """
    Load the tree data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        The loaded tree data as a dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_formulas_with_variables(extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process extracted formulas and enrich them with variable values.
    
    Args:
        extracted_formulas: List of extracted formulas from formula_parser
        tree_data: The tree data loaded from JSON
        
    Returns:
        Enriched formulas with variable values for each ID
    """
    filter_engine = FormulaVariableFilter(tree_data)
    result = []
    
    for formula_group in extracted_formulas:
        group_result = {
            "path": formula_group["path"],
            "formulas": formula_group["formulas"],
            "ids": []
        }
        
        # Process each ID
        for id_obj in formula_group.get("ids", []):
            id_result = {
                "id": id_obj["id"],
                "formulas": []
            }
            
            # Process each formula for this ID
            for formula in formula_group["formulas"]:
                formula_vars = filter_engine.extract_variables_for_formula(formula, id_obj)
                id_result["formulas"].append(formula_vars)
            
            group_result["ids"].append(id_result)
        
        result.append(group_result)
    
    return result
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formula Processor Module
-----------------------
This module implements:
1. Loading tree_data.json
2. Extracting formulas using formula_parser.py
3. Processing variables through direct analysis of the tree structure
4. Saving the results to JSON file
"""
import os
import json
import re
from typing import Dict, List, Any, Optional
from filters.filters_paths import filter_tree_data
from formula_parser import parse_formulas

def load_tree_data(file_path: str) -> Dict[str, Any]:
    """
    Load tree data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the tree data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_node_by_id(tree_data: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a node in the tree data by its ID.
    
    Args:
        tree_data: The tree data to search in
        node_id: The ID to find
    
    Returns:
        The node dictionary if found, None otherwise
    """

    #####node = filter_tree_data(tree_data, "", []

    def search_recursive(data):
        if isinstance(data, dict):
            if data.get('id') == node_id:
                return data
            
            # Check in nested data
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    result = search_recursive(item)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                result = search_recursive(item)
                if result:
                    return result
        
        return None
    
    # Start search from dados section
    if 'dados' in tree_data:
        for section in tree_data['dados']:
            result = search_recursive(section)
            if result:
                return result
    
    return None

def extract_node_values(node: Dict[str, Any], var_path: str) -> Any:
    """
    Extract values for a specific variable path from a node.
    
    Args:
        node: The node to extract values from
        var_path: The variable path to find (e.g., e00001v)
    
    Returns:
        The value of the variable if found, None otherwise
    """
    # First, check direct fields
    if 'fields' in node and node['fields']:
        for field in node['fields']:
            if field.get('path') == var_path:
                return field.get('value')
    
    # If not found in direct fields, check nested data
    if 'data' in node and node['data']:
        for item in node['data']:
            if isinstance(item, dict):
                # If this subnode is specifically for this path
                if item.get('path') == var_path and 'data' in item and item['data']:
                    values = []
                    for subitem in item['data']:
                        if 'fields' in subitem and subitem['fields']:
                            values.append(subitem['fields'][0].get('value'))
                    return values
                
                # Otherwise recurse into this item
                result = extract_node_values(item, var_path)
                if result is not None:
                    return result
    
    return None

def filter_values_by_condition(node: Dict[str, Any], var_path: str, filter_expr: str, filter_vars: List[str]) -> List[Any]:
    """
    Filter values based on a condition expression.
    
    Args:
        node: The node to extract values from
        var_path: The variable path to find values for
        filter_expr: The filter expression (e.g., "e00083v == 'Não'")
        filter_vars: Variable paths referenced in the filter
    
    Returns:
        List of values that match the filter condition
    """
    filtered_values = []
    
    # Build a simple matcher for common filter patterns
    equality_match = re.match(r'(\w+)\s*==\s*[\'\"]([^\'\"]+)[\'\"]', filter_expr)
    contains_match = re.match(r'contains\((\w+),\s*[\'\"]([^\'\"]+)[\'\"]\)', filter_expr)
    
    # Function to check if a node matches the filter
    def node_matches_filter(n):
        if equality_match:
            filter_var = equality_match.group(1)
            expected_value = equality_match.group(2)
            
            actual_value = extract_node_values(n, filter_var)
            return actual_value == expected_value
        
        elif contains_match:
            filter_var = contains_match.group(1)
            substring = contains_match.group(2)
            
            actual_value = extract_node_values(n, filter_var)
            return substring in str(actual_value) if actual_value is not None else False
        
        # Default behavior for unrecognized patterns - accept all
        return True
    
    # Process if we're directly at a node with the target variable
    if 'fields' in node:
        for field in node['fields']:
            if field.get('path') == var_path and node_matches_filter(node):
                filtered_values.append(field.get('value'))
    
    # Recursively process subnodes if this isn't the target path
    if 'data' in node and node['data']:
        for subnode in node['data']:
            if isinstance(subnode, dict):
                # If subnode directly represents the variable we're filtering
                if subnode.get('path') == var_path and 'data' in subnode and subnode['data']:
                    for item in subnode['data']:
                        if 'fields' in item and item['fields'] and node_matches_filter(item):
                            filtered_values.append(item['fields'][0].get('value'))
                else:
                    # Otherwise recurse into subnodes
                    filtered_values.extend(filter_values_by_condition(subnode, var_path, filter_expr, filter_vars))
    
    return filtered_values

# def extract_variable_values(formula_data: Dict[str, Any], node: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Extract variable values for a formula based on its parsed structure.
    
#     Args:
#         formula_data: A formula object with path, value, and parsed information
#         node: The node to extract values from
        
#     Returns:
#         Dictionary with formula path and variable values
#     """
#     # Create result structure with formula path
#     result = {
#         "path": formula_data["path"],
#         "vars": {}
#     }
    
#     # Get parsed information
#     parsed = formula_data.get("parsed", {})
    
#     # Process regular variables (non-aggregated)
#     for var_path in parsed.get("vars", []):
#         value = extract_node_values(node, var_path)
#         if value is not None:
#             result["vars"][var_path] = value
    
#     # Process aggregation functions
#     for aggr in parsed.get("aggr", []):
#         var_path = aggr["vars"][0] if aggr["vars"] else None
#         filter_expr = aggr["filter"]
#         filter_vars = aggr.get("filter_vars", [])
        
#         if var_path:
#             if filter_expr:
#                 # For variables in aggregation functions with filter
#                 values = filter_values_by_condition(node, var_path, filter_expr, filter_vars)
#                 if values:
#                     result["vars"][var_path] = values
#             else:
#                 # If no filter, just get all values
#                 value = extract_node_values(node, var_path)
#                 if value is not None:
#                     if isinstance(value, list):
#                         result["vars"][var_path] = value
#                     else:
#                         result["vars"][var_path] = [value]
    
#     return result

# def process_formula_variables(extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
#     """
#     Process extracted formulas and enrich them with variable values for each ID.
    
#     Args:
#         extracted_formulas: List of formula groups with their formulas and IDs
#         tree_data: The full tree data object
        
#     Returns:
#         Enriched formulas with variable values for each ID
#     """
#     result = []
    
#     for formula_group in extracted_formulas:
#         # Create a new group object with the same structure
#         group_result = {
#             "path": formula_group["path"],
#             "formulas": formula_group["formulas"],
#             "ids": []
#         }
        
#         # Process each ID in the group
#         for id_obj in formula_group.get("ids", []):
#             id_value = id_obj["id"]
#             id_result = {
#                 "id": id_value,
#                 "formulas": []
#             }
            
#             # Find the node with this ID
#             node = find_node_by_id(tree_data, id_value)
            
#             if node:
#                 # For each formula, extract variable values
#                 for formula in formula_group["formulas"]:
#                     formula_vars = extract_variable_values(formula, node)
#                     id_result["formulas"].append(formula_vars)
            
#             # Add this ID's results to the group
#             group_result["ids"].append(id_result)
        
#         # Add the group to the final result
#         result.append(group_result)
    
#     return result

def process_formula_variables(extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process extracted formulas and enrich them with variable values for each ID.
    
    Args:
        extracted_formulas: List of formula groups with their formulas and IDs
        tree_data: The full tree data object
        
    Returns:
        Enriched formulas with variable values for each ID
    """
    result = []
    
    for formula_group in extracted_formulas:
        # Create a new group object with the same structure
        group_result = {
            "path": formula_group["path"],
            "formulas": formula_group["formulas"],
            "ids": []
        }
        
        # Process each ID in the group
        for id_obj in formula_group.get("ids", []):
            id_value = id_obj["id"]
            id_result = {
                "id": id_value,
                "formulas": []
            }
            
            # For each formula, extract variable values
            for formula in formula_group["formulas"]:
                
                # Paths vars, non-aggregated
                vars = formula.get("parsed", []).get("vars", [])
                node = filter_tree_data(tree_data, [f"first({v})" for v in vars], id_value)
                id_result["formulas"].append(n for n in node)

                # Aggr functions
                for aggr in formula.get("parsed", []).get("aggr", []):
                    vars = aggr["vars"]
                    filter_expr = aggr["filter"]
                    if filter_expr:
                        # For variables in aggregation functions with filter
                        node = filter_tree_data(tree_data, vars, id_value, filter_expr)
                    else:
                        # If no filter, just get all values
                        node = filter_tree_data(tree_data, vars, id_value)
                    id_result["formulas"].append(n for n in node)
            
            # Add this ID's results to the group
            group_result["ids"].append(id_result)
        
        # Add the group to the final result
        result.append(group_result)
    
    return result


def main():
    """
    Main function to process formulas with variables.
    """
    # Get the current directory for file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths for input and output files
    tree_data_path = os.path.join(current_dir, "tree_data.json")
    output_path = os.path.join(current_dir, "processed_formulas_with_variables.json")
    
    print(f"Loading tree data from {tree_data_path}...")
    try:
        tree_data = load_tree_data(tree_data_path)
        print(f"Successfully loaded tree data.")
    except Exception as e:
        print(f"Error loading tree data: {e}")
        return
    
    print("Extracting and parsing formulas...")
    try:
        extracted_formulas = parse_formulas(tree_data)
        print(f"Successfully extracted {len(extracted_formulas)} formula groups.")
    except Exception as e:
        print(f"Error extracting formulas: {e}")
        return
    
    print("Processing variables for formulas...")
    try:
        processed_formulas = process_formula_variables(extracted_formulas, tree_data)
        print(f"Successfully processed variables for {len(processed_formulas)} formula groups.")
    except Exception as e:
        print(f"Error processing variables: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"Saving results to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_formulas, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved results to {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")
        return
    
    print("Formula processing complete!")

if __name__ == "__main__":
    main()
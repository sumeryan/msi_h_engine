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
import copy
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

def process_formula_variables(extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process extracted formulas and enrich them with variable values for each ID.
    
    Args:
        extracted_formulas: List of formula groups with their formulas and IDs
        tree_data: The full tree data object
        
    Returns:
        Enriched formulas with variable values for each ID
    """

    group_result = []
   
    for formula_group in extracted_formulas:

        # Process each ID in the group
        for id_obj in formula_group.get("ids", []):

            id_value = id_obj["id"]
            
            formula_ids = {}

            # For each formula, extract variable values
            for formula in formula_group["formulas"]:

                print(f"Processing formula: {formula["path"]}: {formula['value']} for ID: {id_value}")

                # Create a new entry for this formula path if it doesn't exist
                formula_ids.setdefault(formula["path"], [])

                # Paths vars, non-aggregated
                vars = formula.get("parsed", []).get("vars", [])
                node = filter_tree_data(tree_data, [f"first({v})" for v in vars], id_value)
                for n in node:
                    formula_ids[formula["path"]].append(n)

                # Aggr functions
                for aggr in formula.get("parsed", []).get("aggr", []):
                    vars = aggr["vars"]
                    filter = aggr["filter"]

                    # Search for the variable in the tree data
                    if aggr["global"]:

                        if filter:
                            # For variables in aggregation functions with filter
                            # Global filter ignores the ID
                            node = filter_tree_data(tree_data, vars, filter_expr = filter)
                        else:
                            # If no filter, just get all values
                            node = filter_tree_data(tree_data, vars)
                        # Append all values to the formula_ids
                        for n in node:
                            formula_ids[formula["path"]].append(n)

                    # If not global, we need to filter the values in ID and subnodes
                    else:

                        if filter:
                            # For variables in aggregation functions with filter
                            node = filter_tree_data(tree_data, vars, id_value, filter, lock_node = True)
                        else:
                            # If no filter, just get all values
                            node = filter_tree_data(tree_data, vars, id_value, lock_node = True)
                        
                        for n in node:  
                            formula_ids[formula["path"]].append(n)

            # Temporarily store the results for this ID
            id_result = {
                "formulas": []
            }
            for key, value in formula_ids.items():
                id_result["formulas"].append({"formula": key, "data": copy.deepcopy(value)})

            # Add this ID's results to the group
            group_result.append({
                "entity": formula_group["path"],
                "id": id_value,
                "formula_data": copy.deepcopy(id_result)
            })
    
    return group_result

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
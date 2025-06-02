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
import os
import json
import copy
from typing import Dict, List, Any, Optional
from filters.filters_paths import filter_tree_data
from engine_parser import parse_formulas
from log.logger import get_logger
from variable_filter import FilterVariableExtractor

# Get a logger instance for this module
logger = get_logger("engine_pre_processor")

def load_tree_data(file_path: str) -> Dict[str, Any]:
    """
    Load tree data from a JSON file and parse it into a Python dictionary.
    
    This function reads a JSON file containing hierarchical tree data that will be
    used for formula variable extraction. It handles file I/O errors and JSON parsing
    errors, raising appropriate exceptions with detailed error messages.
    
    Args:
        file_path: Absolute or relative path to the JSON file containing tree data
        
    Returns:
        Dictionary containing the parsed tree data structure
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        Exception: For other unexpected errors during file reading or parsing
    """
    logger.info(f"Loading tree data from file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        logger.debug(f"Tree data loaded successfully: {len(tree_data)} top-level elements")
        return tree_data
    except FileNotFoundError:
        logger.error(f"Tree data file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading tree data: {e}")
        raise

def process_formula_variables(extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process extracted formulas and enrich them with variable values for each ID.
    
    This function is the core of the formula pre-processing. It takes the parsed formulas
    and for each formula and ID combination:
    1. Extracts simple variable references directly from the tree
    2. Processes aggregation functions, handling both global and local (ID-specific) contexts
    3. Combines the results into a structured output format
    
    The function handles two types of variable extraction:
    - Non-aggregated variables: Simple direct variable references
    - Aggregated variables: Variables used within aggregation functions (sum, avg, etc.)
      with optional filters and global/local scope
    
    Args:
        extracted_formulas: List of formula groups, each containing formulas and associated IDs
                           (output from the parse_formulas function)
        tree_data: The complete tree data structure (loaded from JSON)
        
    Returns:
        List of dictionaries containing processed formulas with their variable values
        for each ID. The structure includes entity, ID, and formula data with extracted
        variable values.
        
    Raises:
        Exception: For errors in variable extraction or tree data filtering
    """
    logger.info(f"Starting to process formula variables for {len(extracted_formulas)} formula groups")
    
    group_result = []
   
    for i, formula_group in enumerate(extracted_formulas):
        logger.debug(f"Processing formula group {i+1}/{len(extracted_formulas)}: {formula_group.get('path', 'unknown')}")
        
        # Process each ID in the group
        for id_obj in formula_group.get("ids", []):
            id_value = id_obj["id"]
            logger.debug(f"Processing ID: {id_value}")
            
            formula_ids = {}

            # For each formula, extract variable values
            for formula in formula_group["formulas"]:
                formula_path = formula["path"]
                formula_value = formula['value']
                logger.debug(f"Processing formula: {formula_path}: {formula_value} for ID: {id_value}")

                # Create a new entry for this formula path if it doesn't exist
                formula_ids.setdefault(formula["path"], [])

                # Process non-aggregated variables
                # These are direct variable references without aggregation functions
                vars = formula.get("parsed", []).get("vars", [])
                logger.debug(f"Extracting non-aggregated variables: {vars}")
                try:
                    # Apply "first" transformation to get only the first match for each variable
                    node = filter_tree_data(tree_data, [f"first({v})" for v in vars], id_value)
                    logger.debug(f"Found {len(node)} non-aggregated variable nodes")
                    for n in node:
                        formula_ids[formula["path"]].append({"non_aggr": n})
                except Exception as e:
                    logger.error(f"Error processing non-aggregated variables: {e}")
                    raise

                # Process aggregation functions (sum, avg, etc.)
                aggr_funcs = formula.get("parsed", []).get("aggr", [])
                logger.debug(f"Processing {len(aggr_funcs)} aggregation functions")
                
                for aggr in aggr_funcs:

                    vars = aggr["vars"]
                    filter_expr = aggr["filter"]
                    is_global = aggr["global"]

                    # Check if exits var fields in right side of filter expression
                    if filter_expr:
                        filter_vars = FilterVariableExtractor().extract_unique_variables(filter_expr)
                        if filter_vars:
                            logger.debug(f"Filter expression found: {filter_expr}")

                            new_filter_expr = FilterVariableExtractor().highlight_variables(filter_expr)

                            logger.debug(f"Get values for right variables: {filter_vars}")
                            try:
                                # Apply "first" transformation to get only the first match for each variable
                                for v in filter_vars:
                                    var_list = [f"first({v})"]
                                    node = filter_tree_data(tree_data, return_paths=var_list, record_id=id_value, lock_node=True)
                                    if node:
                                        n_value = node[0]["values"][0]
                                        # Check if the value is a number
                                        try:
                                            float(value)
                                        except (ValueError, TypeError):
                                            n_value = f"'{n_value}'"  # Enclose in quotes if not a number
                                        logger.debug(f"Found variable value {n_value}")
                                        new_filter_expr = new_filter_expr.replace(f"__{v}__", n_value)
                            except Exception as e:
                                logger.error(f"Error processing non-aggregated variables: {e}")
                                raise                
                            logger.debug(f"Updated filter expression: {new_filter_expr}")
                            filter_expr = new_filter_expr
                    
                    logger.debug(f"Processing aggregation function - vars: {vars}, filter: {filter_expr}, global: {is_global}")

                    # Search for the variable in the tree data
                    # Global aggregations search across the entire tree
                    if is_global:
                        logger.debug("Processing global aggregation")
                        try:
                            if filter_expr:
                                # For variables in aggregation functions with filter
                                # Global filter ignores the ID
                                logger.debug(f"Applying global filter: {filter_expr}")
                                node = filter_tree_data(tree_data, vars, filter_expr=filter_expr)
                            else:
                                # If no filter, just get all values
                                logger.debug("No filter applied, getting all values")
                                node = filter_tree_data(tree_data, vars)
                                
                            logger.debug(f"Found {len(node)} nodes for global aggregation")
                            # Append all values to the formula_ids
                            for n in node:
                                formula_ids[formula["path"]].append({"aggr": {"base": aggr["base"], "vars": n}})
                        except Exception as e:
                            logger.error(f"Error processing global aggregation: {e}")
                            raise

                    # Local aggregations only search within the current ID and its subnodes
                    else:
                        logger.debug("Processing local aggregation (ID-specific)")
                        try:
                            if filter_expr:
                                # For variables in aggregation functions with filter
                                logger.debug(f"Applying local filter with ID {id_value}: {filter_expr}")
                                node = filter_tree_data(tree_data, vars, id_value, filter_expr, lock_node=True)
                            else:
                                # If no filter, just get all values
                                logger.debug(f"No filter applied, getting all values for ID {id_value}")
                                node = filter_tree_data(tree_data, vars, id_value, lock_node=True)
                            
                            logger.debug(f"Found {len(node)} nodes for local aggregation")
                            for n in node:  
                                formula_ids[formula["path"]].append({"aggr": aggr["base"], "vars": n})
                        except Exception as e:
                            logger.error(f"Error processing local aggregation: {e}")
                            raise

            # Temporarily store the results for this ID
            logger.debug(f"Creating result for ID {id_value} with {len(formula_ids)} formulas")
            id_result = {
                "formulas": []
            }
            for key, value in formula_ids.items():
                id_result["formulas"].append({"formula": key, "data": copy.deepcopy(value)})

            # Add this ID's results to the group
            group_item = {
                "entity": formula_group["path"],
                "id": id_value,
                "formula_data": copy.deepcopy(id_result)
            }
            group_result.append(group_item)
            logger.debug(f"Added result for entity {formula_group['path']}, ID {id_value}")
    
    logger.info(f"Formula variable processing complete. Processed {len(group_result)} ID results")
    return group_result

def main():
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
    logger.info("Starting formula pre-processing")
    
    # Get the current directory for file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths for input and output files
    tree_data_path = "tree_data.json"
    extracted_formulas_path = "extracted_formulas.json"
    output_path = "processed_formulas_with_variables.json"
    
    logger.info(f"Using tree data path: {tree_data_path}")
    logger.info(f"Using output path: {output_path}")
    
    # Load tree data
    try:
        logger.info(f"Loading tree data from {tree_data_path}...")
        tree_data = load_tree_data(tree_data_path)
        logger.info(f"Successfully loaded tree data")
    except Exception as e:
        logger.error(f"Error loading tree data: {e}")
        return
    
    # Extract and parse formulas
    try:
        logger.info("Extracting and parsing formulas...")
        extracted_formulas = parse_formulas(tree_data)
        logger.info(f"Successfully extracted {len(extracted_formulas)} formula groups")
        
        logger.debug(f"Saving extracted formulas to {extracted_formulas_path}")
        with open(extracted_formulas_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_formulas, f, indent=4, ensure_ascii=False)
        logger.debug(f"Extracted formulas saved to {extracted_formulas_path}")

    except Exception as e:
        logger.error(f"Error extracting formulas: {e}")
        return
    
    # Process formula variables
    try:
        logger.info("Processing variables for formulas...")
        processed_formulas = process_formula_variables(extracted_formulas, tree_data)
        logger.info(f"Successfully processed variables for {len(processed_formulas)} formula groups")
    except Exception as e:
        logger.error(f"Error processing variables: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return
    
    # Save results
    try:
        logger.info(f"Saving processed results to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_formulas, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved results to {output_path}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return
    
    logger.info("Formula processing complete!")
    
if __name__ == "__main__":
    main()
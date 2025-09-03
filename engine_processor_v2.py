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
# from os import urandom
# from pydoc import classify_class_attrs
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
from pathlib import Path

class EngineProcessor(EngineLogger):

    def __init__(self):
        self.logger = get_logger("Engine - Processor")
        self.data_filter = tree_data_filter()

    def enrich_formulas_with_values(self, extracted_formulas: List[Dict[str, Any]], tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
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

        self.log_info(f"Starting to process formula variables for {len(extracted_formulas)} formula groups")
        
        group_result = []
    
        datetime = Timestamp.now()
        total_count_01 = 0
        total_count_02 = 0
        total_count_03 = 0
        count_01 = 0
        count_02 = 0
        count_03 = 0        

        # self.data_filter.clear_cache()

        total_count_01 = len(extracted_formulas)
        count_01 = 0
        for i, formula_group in enumerate(extracted_formulas):
            count_01 += 1
            self.log_debug(f"Processing formula group {i+1}/{len(extracted_formulas)}: {formula_group.get('path', 'unknown')}")
            
            # Process each ID in the group
            id_obj_count = 0
            total_count_02 = len(formula_group['ids'])
            count_02 = 0
            for id_obj in formula_group.get("ids", []):
                count_02 += 1
                self.log_debug(f"Processing ID object {id_obj_count + 1}/{len(formula_group['ids'])} for group {formula_group.get('path', 'unknown')}")
                id_obj_count += 1
                id_value = id_obj["id"]
                # self.log_debug(f"Processing ID: {id_value}")
                
                formula_ids = {}

                # For each formula, extract variable values
                formula_count = 0
                
                total_count_03 = len(formula_group['formulas'])
                count_03 = 0
                for formula in formula_group["formulas"]:
                    count_03 += 1
                    self.log_debug(f"Processing formula {formula_count + 1}/{len(formula_group['formulas'])} for ID {id_value}: {formula.get('path', 'unknown')}")
                    formula_count += 1
                    # formula_path = formula["path"]
                    # formula_value = formula['value']
                    # self.log_debug(f"Processing formula: {formula_path}: {formula_value} for ID: {id_value}")

                    # Create a new entry for this formula path if it doesn't exist
                    formula_ids.setdefault(formula["path"], [])

                    # Process non-aggregated variables
                    # These are direct variable references without aggregation functions
                    vars = formula.get("parsed", []).get("vars", [])
                    #self.log_debug(f"Extracting non-aggregated variables: {vars}")
                    if vars:
                        try:
                            # Apply "first" transformation to get only the first match for each variable
                            node = self.data_filter.filter_tree_data(
                                tree_data,
                                [f"first({v})" for v in vars], 
                                id_value, 
                                filter_expr=None)
                            #self.log_debug(f"Found {len(node)} non-aggregated variable nodes")
                            for n in node:
                                formula_ids[formula["path"]].append({"non_aggr": n})
                        except Exception as e:
                            self.log_error(f"Error processing non-aggregated variables: {e}")
                            raise

                    # Process aggregation functions (sum, avg, etc.)
                    aggr_funcs = formula.get("parsed", []).get("aggr", [])
                    #self.log_debug(f"Processing {len(aggr_funcs)} aggregation functions")
                    
                    for aggr in aggr_funcs:

                        vars = aggr["vars"]
                        filter_expr = aggr["filter"]
                        is_global = aggr["global"]

                        filter_aggr_expr = []

                        # Check if exits var fields in right side of filter expression
                        if filter_expr:
                            # Extract unique variables from the filter expression
                            filter_vars = FilterVariableExtractor().extract_unique_variables(filter_expr)
                            # If there are variables in the filter expression, we need to process them
                            if filter_vars:
                                # self.log_debug(f"Filter expression found: {filter_expr}")
                                # Highlight variables in the filter expression
                                new_filter_expr = FilterVariableExtractor().highlight_variables(filter_expr)
                                # self.log_debug(f"Get values for right variables: {filter_vars}")
                                try:
                                    # Apply "first" transformation to get only the first match for each variable
                                    for v in filter_vars:
                                        # Set function to get the first value of the variable
                                        var_list = [f"first({v})"]
                                        # self.log_debug(f"Searching for variable: {v} in tree data")
                                        # Search for the variable in the tree data
                                        node = self.data_filter.filter_tree_data(
                                            tree_data,
                                            return_paths=var_list,
                                            record_id=id_value,
                                            lock_node=True)
                                        if node:
                                            n_value = node[0]["values"][0]
                                            # Append the variable value to the filter aggregation expression
                                            filter_aggr_expr.append({v:n_value})
                                            # self.log_debug(f"Found variable value {n_value}")
                                            try:
                                                # Check if the value is a number
                                                float(n_value)
                                            except (ValueError, TypeError):
                                                # Enclose in quotes if not a number
                                                n_value = f"'{n_value}'"  
                                            # Replace the variable in the filter expression
                                            new_filter_expr = new_filter_expr.replace(f"__{v}__", n_value)
                                except Exception as e:
                                    self.log_error(f"Error processing non-aggregated variables: {e}")
                                    raise
                                # self.log_debug(f"Updated filter expression: {new_filter_expr}")
                                # Change the filter expression to the new one with values
                                filter_expr = new_filter_expr
                        
                        self.log_debug(f"Processing aggregation function - vars: {vars}, filter: {filter_expr}, global: {is_global}")

                        # Search for the variable in the tree data
                        # Global aggregations search across the entire tree
                        if is_global:
                            self.log_debug("Processing global aggregation")
                            try:
                                if filter_expr:
                                    # self.log_debug(f"Applying global filter: {filter_expr}")
                                    # For variables in aggregation functions with filter
                                    # Global filter ignores the ID
                                    node = self.data_filter.filter_tree_data(
                                        tree_data, 
                                        vars, 
                                        filter_expr=filter_expr)
                                else:
                                    # self.log_debug("No filter applied, getting all values")
                                    # If no filter, just get all values
                                    node = self.data_filter.filter_tree_data(
                                        tree_data, 
                                        vars)
                                # self.log_debug(f"Found {len(node)} nodes for global aggregation")
                                # Append all values to the formula_ids
                                for n in node:
                                    formula_ids[formula["path"]].append({"aggr": {"base": aggr["base"], "vars": n, "filter": filter_aggr_expr}})
                                # If no nodes found
                                if not node:
                                    formula_ids[formula["path"]].append({"aggr": {"base": aggr["base"], "vars": [], "filter": filter_aggr_expr}})
                            except Exception as e:
                                self.log_error(f"Error processing global aggregation: {e}")
                                raise

                        # Local aggregations only search within the current ID and its subnodes
                        else:
                            self.log_debug("Processing local aggregation (ID-specific)")
                            try:
                                if filter_expr:
                                    # self.log_debug(f"Applying local filter with ID {id_value}: {filter_expr}")
                                    # For variables in aggregation functions with filter
                                    node = self.data_filter.filter_tree_data(
                                        tree_data, 
                                        vars, 
                                        id_value, 
                                        filter_expr, 
                                        lock_node=True)
                                else:
                                    # self.log_debug(f"No filter applied, getting all values for ID {id_value}")
                                    # If no filter, just get all values
                                    node = self.data_filter.filter_tree_data(
                                        tree_data, 
                                        vars, 
                                        id_value, 
                                        lock_node=True)
                                # self.log_debug(f"Found {len(node)} nodes for local aggregation")
                                for n in node:  
                                    formula_ids[formula["path"]].append({"aggr": aggr["base"], "vars": n, "filter": filter_aggr_expr})
                                # If no nodes found
                                if not node:
                                    formula_ids[formula["path"]].append({"aggr": {"base": aggr["base"], "vars": [], "filter": filter_aggr_expr}})
                            except Exception as e:
                                self.log_error(f"Error processing local aggregation: {e}")
                                raise

                # Temporarily store the results for this ID
                # self.log_debug(f"Creating result for ID {id_value} with {len(formula_ids)} formulas")
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
                # self.log_debug(f"Added result for entity {formula_group['path']}, ID {id_value}")
        
        self.log_info(f"Formula variable processing complete. Processed {len(group_result)} ID results")
        return group_result

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

        # Pasta atual
        pasta = Path(".")
        for arquivo in pasta.glob("*.json"):
            arquivo.unlink()
            print(f"Arquivo {arquivo} excluído")    
        pasta = Path("./data")
        for arquivo in pasta.glob("*.json"):
            arquivo.unlink()
            print(f"Arquivo {arquivo} excluído")             

        def find_formula_group(structure):
            # Check if the structure is a list
            if isinstance(structure, list):
                for item in structure:
                    result = find_formula_group(item)
                    if result:
                        return result
            
            # Check if the structure is a dictionary
            elif isinstance(structure, dict):
                # Check if the dictionary has the key "grupoformulas"
                if "grupoformulas" in structure:
                    return structure["grupoformulas"]
                
                # If not, iterate through the dictionary values
                for value in structure.values():
                    result = find_formula_group(value)
                    if result:
                        return result
            
            # If nothing was found, return None
            return None

        def find_measurement(structure, path):
            # Check if the structure is a list
            if isinstance(structure, list):
                for item in structure:
                    result = find_measurement(item, path)
                    if result:
                        return result
            
            # Check if the structure is a dictionary
            elif isinstance(structure, dict):
                # Check if the dictionary has the key "grupoformulas"
                if "data" in structure:
                    if path in structure:
                        return structure["data"][0]["id"]
                
                # If not, iterate through the dictionary values
                for value in structure.values():
                    result = find_measurement(value, path)
                    if result:
                        return result
            
            # If nothing was found, return None
            return None        

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

        contracts = {'contracts':[{'boletimmedicao':'BM-CW33039-003','contrato':'019745f1-bc6d-7040-9aec-76654d38aa42'}]}
        
        for c in contracts['contracts']: # ['01987fd2-8753-7cd0-8662-f3a2eae9ad4a']:

            engine_results_converted = []

            # # Update highways and cities records
            ufrappe.update_cities(c['boletimmedicao'])

            ufrappe.update_measurement_records(c['boletimmedicao']) 
            ufrappe.update_hours_measurement_record(c['boletimmedicao'])
            ufrappe.update_measurement_productivity(c['boletimmedicao'])
            ufrappe.apply_measurement_performance_conditions(c['boletimmedicao'])
            ufrappe.apply_measurement_items_factor(c['boletimmedicao'])
            ufrappe.sumarize_measurement(c['boletimmedicao'])
            ufrappe.check_orphans_records(c['boletimmedicao'])

            self.log_info("=" * 80)
            self.log_info(f"Processing contract: {c['contrato']}\n\n")
            self.log_info("=" * 80)
            
            if use_cached_data:
                # Load cached contract data
                self.log_info(f"Using cached data for contract {c['contrato']}")

                # Reading contract data from cache from file contract_data_{c['contrato']}.json
                try:
                    with open(f"contract_data_{c['contrato']}.json", 'r', encoding='utf-8') as f:
                        contract_data = json.load(f)
                except FileNotFoundError:
                    use_cached_data = False

            contract_data = None
            if not use_cached_data:
                # Get contract data
                contract_data = entities_processor.get_data(c['contrato'])

                # Removida a gravacao para calculo geral
                # # Write contract data to a file for debugging
                # with open(f"contract_data_{c['contrato']}.json", 'w', encoding='utf-8') as f:
                #     json.dump(contract_data, f, indent=4, ensure_ascii=False)

            # Get contract formula group 
            find_contract = [item for item in contract_data['data'] if 'Contract' in item]

            # Check if contract data is found
            if not find_contract:
                self.log_error(f"No contract data found for {c['contrato']}. Skipping.")
                continue

            # Extract contract formula IDs
            contract_formula_id = None
            
            try: 
                contract_formula_id = find_formula_group(find_contract[0])               
            except Exception as e:
                self.log_error(f"Error extracting contract formula IDs for {c['contrato']}: {e}")
                continue

            if not contract_formula_id:
                self.log_error(f"No formula group IDs found for contract {c['contrato']}. Skipping.")
                continue   

            # Filter formulas based on group
            contract_formula = [f for f in formulas if f.get("name") in contract_formula_id]  

            # Build engine data
            data_builder = engine_entities.engine_data.EngineDataBuilder(
                contract_data['hierarchical'], 
                contract_formula, 
                contract_data['data'], 
                "data",
                compact_mode=True
            )
            #Create data tree for the contract
            engine_data_tree = data_builder.build()
            
            # Removida a gravacao para calculo geral
            # with open(f"data_tree_{c['contrato']}.json", 'w', encoding='utf-8') as f:
            #     json.dump(engine_data_tree, f, indent=4, ensure_ascii=False)        

            # Parse formulas
            parser = engine_parser.FormulaParser()
            extract_formulas = parser.parse_formulas(engine_data_tree)

            # Removida a gravacao para calculo geral
            # # Save the parsed formulas to a file
            # with open(f"extract_formulas_{c['contrato']}.json", 'w', encoding='utf-8') as f:
            #     json.dump(extract_formulas, f, indent=4, ensure_ascii=False)        

            classifier = FormulaExecutionClassifier(extract_formulas)
            classifier_groups = classifier.get_execution_order()

            for g in classifier_groups:

                group_formulas = {}

                for formula_path in extract_formulas:
                    for formula in formula_path["formulas"]:
                        if formula["path"] in classifier_groups[g]:
                            fp = formula_path["path"]
                            if fp not in group_formulas:
                                group_formulas[fp] = {
                                    'path': fp,
                                    'formulas': [],
                                    'ids': formula_path["ids"]
                                }
                            group_formulas[fp]['formulas'].append(formula)

                group_extract_formulas = []
                for gp, gv in group_formulas.items():
                    group_extract_formulas.append({
                        "path": gp,
                        "formulas": gv["formulas"],
                        "ids": gv["ids"]
                    })

                # Process formula variables
                enrich_formulas = self.enrich_formulas_with_values(group_extract_formulas, engine_data_tree)

                # Removida a gravacao para calculo geral
                # with open(f"enrich_formulas_{g}_{k}.json", 'w', encoding='utf-8') as f:
                #     json.dump(enrich_formulas, f, indent=4, ensure_ascii=False)                 

                engine = engine_eval.EngineEval()

                self.log_info("Starting formula evaluation")

                engine_results = engine.eval_formula(enrich_formulas, group_extract_formulas, engine_data_tree)
                    
                # Print summary of results
                success_count = sum(1 for entity in engine_results for fr in entity["results"] if fr["status"] == "success")
                error_count = sum(1 for entity in engine_results for fr in entity["results"] if fr["status"] == "error")
                engine.log_info(f"Formula evaluation complete. Successful: {success_count}, Errors: {error_count}")
                if error_count > 0:
                    str_errors = []
                    for r in engine_results:
                        for error in r["results"]:
                            if error["status"] == "error":
                                str_erro = f"Error in formula: {error['path']}, Id: {r['id']}, Error: {error['error']}"
                                str_errors.append(str_erro)
                                engine.log_info(str_erro)
                    if len(str_errors)>0:
                        ufrappe.write_errors(c['boletimmedicao'], str_errors)
                        
                # Convert numpy types to native Python types before saving
                _engine_results = engine.convert_numpy_types(engine_results)
                engine_results_converted.extend(_engine_results)

                # Removida a gravacao para calculo geral
                # # Write the results to a JSON file
                with open(f"engine_result_g{g}_{c['contrato']}.json", 'w', encoding='utf-8') as f:
                    json.dump(_engine_results, f, indent=4, ensure_ascii=False)

                # Select the first formula to update
                for to_update_formula in group_extract_formulas:

                    # Update tree_data and database
                    utree = update_tree.UpdateTreeData(
                        engine_data_tree, 
                        to_update_formula, 
                        _engine_results
                    )
                    engine_data_tree = utree.update_tree()

                # with open(f"data_tree_{c['contrato']}_{i}.json", 'w', encoding='utf-8') as f:
                #     json.dump(engine_data_tree, f, indent=4, ensure_ascii=False)                           

            # Select the first formula to update
            for to_update_formula in extract_formulas:
                # Save data to Frappe
                ufrappe.update(engine_results_converted, to_update_formula)       

            ufrappe.sumarize_measurement(c['boletimmedicao'])
            ufrappe.update_reidi_measurement_record(c['boletimmedicao'])
            ufrappe.create_measurement_items_balance(c['boletimmedicao'])
            ufrappe.create_measurement_sap_orders_records(c['boletimmedicao'])
            print(c['boletimmedicao'])
            print('...')

        ufrappe.update_sap_orders_balance()

if __name__ == "__main__":
    processor = EngineProcessor()
    try:
        processor.calculate_measurements(use_cached_data=True)
    except Exception as e:
        processor.log_error(f"An error occurred during formula processing: {e}")
        raise
    finally:
        processor.log_info("Formula processing completed.") 
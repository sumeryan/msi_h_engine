"""
Powered by Renoir
Created by igor.goncalves@renoirgroup.com

This module implements a filtering mechanism for hierarchical data in a tree structure.
It provides a custom query language that supports comparison operators, logical
operators, and special functions for querying hierarchical data structures.

The implementation uses PLY (Python Lex-Yacc) to parse filter expressions
and convert them into an abstract syntax tree (AST) that can be evaluated against
the tree data.

Main features:

- Support for comparison operators (==, !=, >=, <=, >, <)
- Logical operators (and, or)
- Special functions (contains, first, last, firstc, lastc)
- Support for filtering on specific nodes through record identifier
- Navigation in nested data structures with specific paths
- Hierarchical evaluation of conditions in nested data structures
"""
import os
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jmespath  # Used to navigate JSON data using path expressions
import re
import ply.lex as lex  # Lexical analyzer for tokenizing expressions
import ply.yacc as yacc  # Syntactic analyzer for parsing expressions
from typing import Dict, Any, Optional, List, Union, Callable
import hashlib
import json
from typing import Any
# Import the logger
from log.logger import get_logger


# Get a logger instance for this module
logger = get_logger("filters")
logger.info("Filters module initialized")

class tree_data_filter:
    """
    Class that implements a parser and evaluator of filter expressions for hierarchical data.
    
    Supports operations:
    - Comparisons: ==, !=, >=, <=, >, <
    - Logical: and, or
    - Functions: contains(), first(), last(), firstc(), lastc()
    
    This class uses PLY (Python Lex-Yacc) to parse filter expressions and
    convert them into an abstract syntax tree (AST) representation that can
    be evaluated against structured data.
    """

    # Definition of tokens used in lexical analysis
    tokens = (
        'IDENTIFIER', 'NUMBER', 'STRING', 'BOOLEAN',
        'EQUALS', 'NOTEQUALS', 'GREATEREQUAL', 'LESSEQUAL', 'GREATER', 'LESS',
        'AND', 'OR', 'LPAREN', 'RPAREN', 'COMMA',
        'CONTAINS', 'FIRST', 'LAST', 'FIRSTC', 'LASTC',
    )

    # Rules for simple tokens (operators and symbols)
    t_EQUALS = r'=='
    t_NOTEQUALS = r'!='
    t_GREATEREQUAL = r'>='
    t_LESSEQUAL = r'<='
    t_GREATER = r'>'
    t_LESS = r'<'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','

    # Definition for identifiers (field names, keywords)
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9_]*'
        # Check if the identifier is a special keyword
        if t.value == 'and':
            t.type = 'AND'
        elif t.value == 'or':
            t.type = 'OR'
        elif t.value == 'True' or t.value == 'False':
            t.type = 'BOOLEAN'
        elif t.value == 'contains':
            t.type = 'CONTAINS'
        elif t.value == 'first':
            t.type = 'FIRST'
        elif t.value == 'last':
            t.type = 'LAST'
        elif t.value == 'firstc':
            t.type = 'FIRSTC'
        elif t.value == 'lastc':
            t.type = 'LASTC'
        return t

    # Definition for integer numbers
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)  # Convert the value to integer
        return t

    # Definition for strings (delimited by single quotes)
    def t_STRING(self, t):
        r"'[^']*'"
        # Remove quotes from the beginning and end to get the actual string value
        t.value = t.value[1:-1]
        return t

    # Characters to be ignored by the lexical analyzer
    t_ignore = ' \t'

    # Handling lexical errors (unrecognized characters)
    def t_error(self, t):
        error_msg = f"Illegal character '{t.value[0]}' at position {t.lexpos}"
        logger.error(error_msg)
        print(error_msg)  # Keep original behavior for backward compatibility
        logger.debug(f"Skipping illegal character and continuing lexical analysis")
        t.lexer.skip(1)  # Skip the unrecognized character

    # Operator precedence (from lowest to highest)
    precedence = (
        ('left', 'OR'),              # OR has the lowest precedence
        ('left', 'AND'),             # AND has intermediate precedence
        ('left', 'EQUALS', 'NOTEQUALS', 'GREATEREQUAL', 'LESSEQUAL', 'GREATER', 'LESS'),  # Comparisons have high precedence
    )

    # ----- PRODUCTION RULES FOR SYNTACTIC ANALYSIS -----

    # Expression with binary operator (==, !=, >=, <=, >, <, and, or)
    def p_expression_binop(self, p):
        '''expression : expression EQUALS expression
                      | expression NOTEQUALS expression
                      | expression GREATEREQUAL expression
                      | expression LESSEQUAL expression
                      | expression GREATER expression
                      | expression LESS expression
                      | expression AND expression
                      | expression OR expression'''
        # Create an AST node for binary operator: (type, operator, left_operand, right_operand)
        p[0] = ('binop', p[2], p[1], p[3])

    # Expression grouped between parentheses
    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        # Create an AST node for grouped expression: (type, expression)
        p[0] = ('group', p[2])

    # Function contains(x, y) - checks if x contains y
    def p_expression_contains(self, p):
        'expression : CONTAINS LPAREN expression COMMA expression RPAREN'
        # Create an AST node for contains function: (type, container, item)
        p[0] = ('contains', p[3], p[5])

    # Function first(x) - returns the first value for the path x
    def p_expression_first(self, p):
        'expression : FIRST LPAREN expression RPAREN'
        # Create an AST node for first function: (type, path)
        p[0] = ('first', p[3])

    # Function last(x) - returns the last value for the path x
    def p_expression_last(self, p):
        'expression : LAST LPAREN expression RPAREN'
        # Create an AST node for last function: (type, path)
        p[0] = ('last', p[3])

    # Function firstc(x) - returns the first value for the path x by most recent creation date
    def p_expression_firstc(self, p):
        'expression : FIRSTC LPAREN expression RPAREN'
        # Create an AST node for firstc function: (type, path)
        p[0] = ('firstc', p[3])

    # Function lastc(x) - returns the first value for the path x by oldest creation date
    def p_expression_lastc(self, p):
        'expression : LASTC LPAREN expression RPAREN'
        # Create an AST node for lastc function: (type, path)
        p[0] = ('lastc', p[3])

    # Identifier (field name)
    def p_expression_identifier(self, p):
        'expression : IDENTIFIER'
        # Create an AST node for identifier: (type, name)
        p[0] = ('identifier', p[1])

    # Integer number
    def p_expression_number(self, p):
        'expression : NUMBER'
        # Create an AST node for number: (type, value)
        p[0] = ('number', p[1])

    # String (text between quotes)
    def p_expression_string(self, p):
        'expression : STRING'
        # Create an AST node for string: (type, value)
        p[0] = ('string', p[1])

    # Boolean value (True/False)
    def p_expression_boolean(self, p):
        'expression : BOOLEAN'
        # Create an AST node for boolean: (type, value)
        p[0] = ('boolean', p[1])

    # Handling syntactic errors
    def p_error(self, p):
        if p:
            error_msg = f"Syntax error at '{p.value}' (token type: {p.type}, position: {p.lexpos})"
            logger.error(error_msg)
            print(error_msg)  # Keep original behavior for backward compatibility
            logger.debug(f"Parser state at error: {self.parser.state}")
        else:
            error_msg = "Syntax error at the end of expression (unexpected end of input)"
            logger.error(error_msg)
            print(error_msg)  # Keep original behavior for backward compatibility
            logger.debug("No token information available for this syntax error")

    def __init__(self):
        """
        Initializes the filter expression parser.
        """
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)
        self.result_cache = {}
        # self.filtered_nodes = []

    def clear_cache(self):
        self.result_cache = {}
    
    def _create_cache_hash(self, filter_expr: str, lock_node: bool, return_paths: Dict) -> str:
        """
        Creates a hash from the filter parameters to use as cache key.
        
        Args:
            tree_data: Tree data structure
            return_paths: List of paths to return
            record_id: Record ID to filter
            filter_expr: Filter expression
            lock_node: Lock node flag
            
        Returns:
            Hash string to use as cache key
        """
        # Create a dictionary with all parameters
        params = {
            'expr': filter_expr,
            'lock': lock_node,
            'return_paths': return_paths
        }
        
        # Convert parameters to JSON string for consistent serialization
        params_str = json.dumps(params, sort_keys=True)
        
        # Create hash from parameters and tree_data structure
        # Use only the structure/keys of tree_data, not the full content for better performance
        combined_str = f"{params_str}"
        
        # Generate SHA256 hash
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()

    def _extract_tree_structure(self, tree_data: Dict) -> Any:
        """
        Extracts a lightweight structure representation of the tree data for cache key generation.
        
        Args:
            tree_data: Full tree data structure
            
        Returns:
            Simplified structure representation
        """
        def extract_node_structure(node):
            if isinstance(node, dict):
                structure = {}
                if 'id' in node:
                    structure['id'] = node['id']
                if 'fields' in node and node['fields']:
                    structure['fields'] = [field.get('path') for field in node['fields'] if field.get('path')]
                if 'data' in node and node['data']:
                    structure['data'] = [extract_node_structure(child) for child in node['data']]
                return structure
            elif isinstance(node, list):
                return [extract_node_structure(item) for item in node]
            return node
        
        tree_structure = extract_node_structure(tree_data)

        return tree_structure
        
    def parse(self, expression: str):
        """
        Parses the conditional expression and returns the syntax tree (AST).
        
        Args:
            expression: String containing the filter expression to be analyzed
            
        Returns:
            Abstract syntax tree representing the expression
        """
        #logger.debug(f"Parsing expression: {expression}")
        ast = self.parser.parse(expression)
        # if ast:
        #     logger.debug(f"Expression parsed successfully: {expression}")
        # else:
        #     logger.warning(f"Failed to parse expression: {expression}")
        return ast
    
    def convert_to_python_function(self, expression: str) -> Callable:
        """
        Converts a conditional expression to a Python function that can be
        used to filter records.
        
        Args:
            expression: Conditional expression (ex: "e00001v == 1")
            
        Returns:
            A Python function that accepts a record and returns True/False
            
        Raises:
            ValueError: If the expression cannot be parsed
        """

        # Parse the expression to generate the AST
        ast = self.parse(expression)
        if ast is None:
            error_msg = f"Could not parse the expression: {expression}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create a filter function that evaluates the AST for each record
        def filter_function(record, tree_data):
            # record_id = record.get('id', 'unknown')
            # ogger.debug(f"Evaluation result for record {record_id}: {result}")
            result = self._evaluate_ast(ast, record, tree_data)
            return result
        
        # logger.info(f"Successfully created filter function for expression: {expression}")
        return filter_function
    
    def _evaluate_ast(self, ast_node, record, tree_data):
        """
        Evaluates an AST of a conditional expression for a specific record.
        Uses recursion to check sublevels of the hierarchy.
        
        This is the main function for expression evaluation that handles the complexity
        of data hierarchy, ensuring that conditions are checked not only at the
        current level but also at nested levels.
        
        Args:
            ast_node: AST node to be evaluated
            record: Record to be filtered
            tree_data: Complete tree data for special functions
            
        Returns:
            Evaluation result (True/False)
        """
        if record is None:
            return False
            
        node_type = ast_node[0]  # Get the AST node type
        
        if node_type == 'binop':
            op = ast_node[1]  # Operator (==, !=, >=, <=, >, <, and, or)
            
            # Special handling for logical operators to support hierarchy
            if op == 'and':
                # First, check if the left condition is satisfied at the current level
                left_result = self._evaluate_condition(ast_node[2], record, tree_data)
                if not left_result:
                    return False
                
                # If the left side is not satisfied at the current level, no need to check the right
                # In this case, recursively check subnodes for the complete condition (and)
                #if not left_result:
                #    return self._check_recursive(ast_node, record, tree_data)
                
                # If the left side is satisfied, check the right side at the current level
                right_result = self._evaluate_condition(ast_node[3], record, tree_data)
                if not right_result:
                    return False
                
                # If both sides are satisfied at the current level, return true
                #if not right_result:
                #    return self._check_recursive(ast_node, record, tree_data)

                # self.filtered_nodes.append(record)
                return True
            
            elif op == 'or':
                # Evaluate the left side at the current level first
                left_result = self._evaluate_condition(ast_node[2], record, tree_data)
                
                # If the left side is true, we don't need to evaluate the right
                if left_result:
                    #self.filtered_nodes.append(record)
                    return True
                
                # If the left side is false, the result depends on the right side at the current level
                right_result = self._evaluate_condition(ast_node[3], record, tree_data)
                if right_result:
                    #self.filtered_nodes.append(record)
                    return True
                    
                # If both sides are false at the current level, recursively check subnodes
                # return self._check_recursive(ast_node, record, tree_data)
                return False
            
            # For comparison operators at the current level
            left = self._evaluate_condition(ast_node[2], record, tree_data)
            right = self._evaluate_condition(ast_node[3], record, tree_data)
            
            # Safe handling for comparison operators
            try:
                operator_result = False
                if op == '==':
                    operator_result = left == right
                elif op == '!=':
                    operator_result = left != right
                elif op == '>=':
                    operator_result = left >= right
                elif op == '<=':
                    operator_result = left <= right
                elif op == '>':
                    operator_result = left > right
                elif op == '<':
                    operator_result = left < right
                return operator_result 
                # if operator_result:
                #     # self.filtered_nodes.append(record)
                #     return True
            except (TypeError, ValueError):
                # If there is a type or value error in the comparison, consider it as false
                # This can occur when comparing incompatible types
                return False
                
        # For non-binop nodes, just evaluate the condition at the current level
        return self._evaluate_condition(ast_node, record, tree_data)
    
    def _evaluate_condition(self, ast_node, record, tree_data):
        """
        Evaluates a condition on a specific record.
        
        Args:
            ast_node: AST node to be evaluated
            record: Record to be filtered
            tree_data: Complete tree data for special functions
            
        Returns:
            Evaluation result (True/False, or node value for identifiers, numbers, etc.)
        """
        node_type = ast_node[0]
        
        if node_type == 'binop':
            op = ast_node[1]
            
            # For simple logical operators (without hierarchy)
            if op == 'and':
                # Short-circuit evaluation for AND
                left_result = self._evaluate_condition(ast_node[2], record, tree_data)
                if not left_result:
                    return False
                return self._evaluate_condition(ast_node[3], record, tree_data)
                
            elif op == 'or':
                # Short-circuit evaluation for OR
                left_result = self._evaluate_condition(ast_node[2], record, tree_data)
                if left_result:
                    return True
                return self._evaluate_condition(ast_node[3], record, tree_data)
                
            # For comparison operators
            left = self._evaluate_condition(ast_node[2], record, tree_data)
            right = self._evaluate_condition(ast_node[3], record, tree_data)
            
            # Safe handling for comparison operators
            try:
                if op == '==':
                    return left == right
                elif op == '!=':
                    return left != right
                elif op == '>=':
                    return left >= right
                elif op == '<=':
                    return left <= right
                elif op == '>':
                    return left > right
                elif op == '<':
                    return left < right
            except (TypeError, ValueError):
                # Safe handling for comparisons between incompatible types
                return False
            
        elif node_type == 'group':
            # Evaluate the expression inside the parentheses
            return self._evaluate_condition(ast_node[1], record, tree_data)
            
        elif node_type == 'contains':
            # Function contains(x, y) - checks if y is contained in x
            container = self._evaluate_condition(ast_node[1], record, tree_data)
            item = self._evaluate_condition(ast_node[2], record, tree_data)
            # Check if the container is valid
            if container is None:
                return False
            # Convert to string to check inclusion
            return str(item) in str(container)
            
        elif node_type == 'first':
            # Function first(x) - returns the first value for the path x
            path = self._get_path_from_ast(ast_node[1])
            # Get the first value for the path in the tree data
            if path and tree_data and 'data' in tree_data:
                result = self._find_first_value_for_path(path, tree_data['data'])
                # In the filter context, consider True if the value in the current record matches the first value
                if 'fields' in record and record['fields'] is not None:
                    for field in record['fields']:
                        if field.get('path') == path and field.get('value') == result:
                            return True
                return False  # This record does not match the first value
            return False
            
        elif node_type == 'last':
            # Function last(x) - returns the last value for the path x
            path = self._get_path_from_ast(ast_node[1])
            # Get the last value for the path in the tree data
            if path and tree_data and 'data' in tree_data:
                result = self._find_last_value_for_path(path, tree_data['data'])
                # In the filter context, consider True if the value in the current record matches the last value
                if 'fields' in record and record['fields'] is not None:
                    for field in record['fields']:
                        if field.get('path') == path and field.get('value') == result:
                            return True
                return False  # This record does not match the last value
            return False
            
        elif node_type == 'firstc':
            # Function firstc(x) - returns the first value by most recent creation date
            path = self._get_path_from_ast(ast_node[1])
            # Get the first value whose "creation" date for the path is the most recent
            if path and tree_data and 'data' in tree_data:
                result = self._find_firstc_value_for_path(path, tree_data['data'])
                # In the filter context, consider True if the value in the current record matches the result
                if 'fields' in record and record['fields'] is not None:
                    for field in record['fields']:
                        if field.get('path') == path and field.get('value') == result:
                            return True
                return False  # This record does not match the result
            return False
            
        elif node_type == 'lastc':
            # Function lastc(x) - returns the first value by oldest creation date
            path = self._get_path_from_ast(ast_node[1])
            # Get the first value whose "creation" date for the path is the oldest
            if path and tree_data and 'data' in tree_data:
                result = self._find_lastc_value_for_path(path, tree_data['data'])
                # In the filter context, consider True if the value in the current record matches the result
                if 'fields' in record and record['fields'] is not None:
                    for field in record['fields']:
                        if field.get('path') == path and field.get('value') == result:
                            return True
                return False  # This record does not match the result
            return False
            
        elif node_type == 'identifier':

            # Look for the field value in the current record
            if 'fields' in record and record['fields'] is not None:
                for field in record['fields']:
                    if field.get('path') == ast_node[1]:
                        return field.get('value')
            
            # If not found at the current level, look in subnodes
            if 'data' in record and record['data'] is not None:
                for subnode in record['data']:
                    # Look in nodes that represent specific properties
                    if isinstance(subnode, dict) and 'path' in subnode and subnode['path'] == ast_node[1] and 'data' in subnode and subnode['data']:
                        for data_item in subnode['data']:
                            if 'fields' in data_item and data_item['fields']:
                                return data_item['fields'][0].get('value')
                    
                    # Look in fields of generic subnodes
                    elif isinstance(subnode, dict) and 'fields' in subnode and subnode['fields']:
                        for field in subnode['fields']:
                            if field.get('path') == ast_node[1]:
                                return field.get('value')
            
            return None
            
        elif node_type == 'numeric':
            # Return the numeric value
            return ast_node[1]

        elif node_type == 'float':
            # Return the numeric value
            return ast_node[1]

        elif node_type == 'number':
            # Return the numeric value
            return ast_node[1]
            
        elif node_type == 'string':
            # Return the string value
            return ast_node[1]
            
        elif node_type == 'boolean':
            # Convert string "True"/"False" to boolean
            return ast_node[1] == 'True'
            
        return None
    
    # def _check_recursive(self, ast_node, record, tree_data):
    #     """
    #     Recursively checks if any subnode satisfies the complete condition.
    #     This function is crucial for hierarchical evaluation of conditions.
        
    #     Args:
    #         ast_node: AST node to be evaluated
    #         record: Current record being checked
    #         tree_data: Complete tree data
            
    #     Returns:
    #         True if any subnode satisfies the condition, False otherwise
    #     """
    #     # If the record has no subnodes, return false
    #     # if not isinstance(record, dict) or 'data' not in record or not record['data']:
    #     #     return False

    #     evaluated_return = False

    #     if 'data' in record and record['data']:
            
    #         # Check in each subnode
    #         for subnode in record['data']:
    #             self._evaluate_ast(ast_node, subnode, tree_data)
    #             self._check_recursive(ast_node, subnode, tree_data)

    #     # # Check in each subnode
    #     # for subnode in record['data']:
    #     #     if isinstance(subnode, dict):

    #     #         # Deep check
    #     #         if 'data' in record and subnode['data']:
    #     #             for deep_subnode in subnode['data']:
    #     #                 self._check_recursive(ast_node, deep_subnode, tree_data)
                    
    #     #         # Check if the subnode satisfies the condition
    #     #         if self._evaluate_ast(ast_node, subnode, tree_data):
    #     #             return True
                
    #     #         # # Recursively check the subnodes of the current subnode
    #     #         # if self._check_recursive(ast_node, subnode, tree_data):
    #     #         #     return True
                    
    #     return False
    
    # def _check_subnodes_for_condition(self, ast_node, record, tree_data):
    #     """
    #     Checks if any subnode satisfies a specific condition.
    #     Unlike _check_recursive, this function checks only a part
    #     of the condition, not the complete condition.
        
    #     Args:
    #         ast_node: AST node representing the condition to check
    #         record: Current record being checked
    #         tree_data: Complete tree data
            
    #     Returns:
    #         True if any subnode satisfies the condition, False otherwise
    #     """
    #     # If the record has no subnodes, return false
    #     if not isinstance(record, dict) or 'data' not in record or not record['data']:
    #         return False
            
    #     # Check in each subnode
    #     for subnode in record['data']:
    #         if isinstance(subnode, dict):
    #             # Check if the subnode satisfies the condition
    #             if self._evaluate_condition(ast_node, subnode, tree_data):
    #                 return True
    #             # Recursively check the subnodes of the current subnode
    #             if self._check_subnodes_for_condition(ast_node, subnode, tree_data):
    #                 return True
                    
    #     return False
    
    def _get_path_from_ast(self, ast_node):
        """
        Extracts the path from an AST node (for functions like first, last, etc.)
        
        Args:
            ast_node: AST node containing a path identifier
            
        Returns:
            Path string if the node is an identifier, None otherwise
        """
        if ast_node[0] == 'identifier':
            return ast_node[1]
        return None

    def _find_value_for_path(self, path, data_nodes):
        """
        Finds value for a given path in the tree data.
        
        Args:
            path: Path to be searched (ex: "e00001v")
            data_nodes: List of data nodes to be searched
            
        Returns:
            The list value found for the path or None if not found
        """
        # Variable to store the values
        # Uses a list to allow modification inside the nested function
        values = []
        
        # Traverse the data nodes recursively
        def search_nodes(nodes):

            # Ignore if not a list
            if not nodes or not isinstance(nodes, list):
                return None
                
            for node in nodes:

                # If the node is a list, search recursively
                if isinstance(node, list):
                    search_nodes(node)

                # Check if the node has fields
                if isinstance(node, dict) and 'fields' in node and node['fields'] is not None:
                    for field in node['fields']:
                        if field.get('path') == path:
                            values.append(field.get('value'))
                
                # Search in subnodes recursively
                if isinstance(node, dict) and 'data' in node and node['data']:
                    # First, try to search directly in the data list
                    for data_item in node['data']:
                            
                        if isinstance(data_item, dict) and 'path' in data_item and data_item['path'] == path and 'data' in data_item and data_item['data']:
                            # If found a node with the correct path, return the first value
                            sub_node = data_item['data'][0]
                            if 'fields' in sub_node and sub_node['fields']:
                                values.append(sub_node['fields'][0].get('value'))
                    
                    # If not found, search recursively in all subnodes
                    search_nodes(node['data'])
                        
                # If the node is a dictionary with nested subnodes
                elif isinstance(node, dict) and 'data' in node and isinstance(node['data'], list):
                    search_nodes(node['data'])

            # Check if we found any values
            if not values:
                return [None]
            
            return values
            
        return_values = search_nodes(data_nodes)
        return return_values

    def _find_first_value_for_path(self, path, data_nodes):
        """
        Finds the first value for a given path in the tree data.
        
        Args:
            path: Path to be searched (ex: "e00001v")
            data_nodes: List of data nodes to be searched
            
        Returns:
            The first value found for the path or None if not found
        """
        # Variable to store the first value found
        # Uses a list to allow modification inside the nested function
        first_value = [None]

        def set_default_value(value, value_type):
            if not value == None:
                return value
            else:
                if value_type == "numeric":
                    return 0.0
                elif value_type == "key":
                    return ''
                elif value_type == "string":
                    return ''
                else:
                    return ''
        
        # Traverse the data nodes recursively
        def search_nodes(nodes):
            # If we already found a value, we don't need to continue searching
            if first_value[0] is not None:
                return first_value[0]
                
            if not nodes or not isinstance(nodes, list):
                return None
                
            for node in nodes:
                # If we already found a value, we can exit the loop
                if first_value[0] is not None:
                    break
                    
                # Check if the node has fields
                if 'fields' in node and node['fields'] is not None:
                    for field in node['fields']:
                        if field.get('path') == path:
                            value_type = field.get('type')
                            first_value[0] = field.get('value')
                            return set_default_value(first_value[0], value_type)
                
                # Search in subnodes recursively
                if first_value[0] is None and 'data' in node and node['data']:
                    # First, try to search directly in the data list
                    for data_item in node['data']:
                        if first_value[0] is not None:
                            break
                            
                        if isinstance(data_item, dict) and 'path' in data_item and data_item['path'] == path and 'data' in data_item and data_item['data']:
                            # If found a node with the correct path, return the first value
                            sub_node = data_item['data'][0]
                            if 'fields' in sub_node and sub_node['fields']:
                                value_type = sub_node['fields'][0].get('type')
                                first_value[0] = sub_node['fields'][0].get('value')
                                return set_default_value(first_value[0], value_type)
                    
                    # If not found, search recursively in all subnodes
                    if first_value[0] is None:
                        result = search_nodes(node['data'])
                        if result is not None:
                            return result
                        
                # If the node is a dictionary with nested subnodes
                elif first_value[0] is None and 'data' in node and isinstance(node['data'], list):
                    result = search_nodes(node['data'])
                    if result is not None:
                        return result
                        
            return first_value[0]
            
        return search_nodes(data_nodes)
        
    def _find_last_value_for_path(self, path, data_nodes):
        """
        Finds the last value for a given path in the tree data.
        
        Args:
            path: Path to be searched (ex: "e00001v")
            data_nodes: List of data nodes to be searched
            
        Returns:
            The last value found for the path or None if not found
        """
        last_value = None
        
        # Traverse the data nodes recursively
        def search_nodes(nodes):
            nonlocal last_value
            
            if not nodes or not isinstance(nodes, list):
                return None
                
            # Traverse the list in reverse order to find the last value first
            # This optimizes the search when there are many nodes
            for node in reversed(nodes):
                # Check if the node has fields
                if 'fields' in node and node['fields'] is not None:
                    for field in node['fields']:
                        if field.get('path') == path:
                            last_value = field.get('value')
                
                # Search in subnodes recursively, in reverse order
                if 'data' in node and node['data']:
                    # Check specific subnodes for the path
                    for data_item in reversed(node['data']):
                        if isinstance(data_item, dict) and 'path' in data_item and data_item['path'] == path and 'data' in data_item and data_item['data']:
                            # If found a node with the correct path, check the last value
                            sub_nodes = data_item['data']
                            if sub_nodes:
                                sub_node = sub_nodes[-1]  # Take the last subnode
                                if 'fields' in sub_node and sub_node['fields']:
                                    last_value = sub_node['fields'][0].get('value')
                    
                    # Search recursively in all subnodes, in reverse order
                    search_nodes(node['data'])
                        
                # If the node is a dictionary with nested subnodes
                elif 'data' in node and isinstance(node['data'], list):
                    search_nodes(node['data'])
        
        # Start the search in the data nodes
        search_nodes(data_nodes)
        return last_value
        
    def _find_firstc_value_for_path(self, path, data_nodes):
        """
        Finds the first value for a given path in the tree data,
        where the "creation" date is the most recent.
        
        Args:
            path: Path to be searched (ex: "e00001v")
            data_nodes: List of data nodes to be searched
            
        Returns:
            The value of the first node with the specified path whose creation date is the most recent
        """
        # List to store the found nodes with their creation dates
        found_nodes = []
        
        # Traverse the data nodes recursively
        def search_nodes(nodes):
            if not nodes or not isinstance(nodes, list):
                return
                
            for node in nodes:
                # Check if the node has fields and creation date
                if 'fields' in node and node['fields'] is not None and 'creation' in node:
                    for field in node['fields']:
                        if field.get('path') == path:
                            # Store the value, creation date, and node
                            found_nodes.append({
                                'value': field.get('value'),
                                'creation': node.get('creation'),
                                'node': node
                            })
                
                # Search in subnodes recursively
                if 'data' in node and node['data']:
                    # Check specific subnodes for the path
                    for data_item in node['data']:
                        if isinstance(data_item, dict) and 'path' in data_item and data_item['path'] == path and 'data' in data_item and data_item['data']:
                            # For each subnode corresponding to the path, check its data
                            for sub_node in data_item['data']:
                                if 'fields' in sub_node and sub_node['fields'] and 'creation' in sub_node:
                                    # Store the value, creation date, and node
                                    found_nodes.append({
                                        'value': sub_node['fields'][0].get('value'),
                                        'creation': sub_node.get('creation'),
                                        'node': sub_node
                                    })
                    
                    # Search recursively in all subnodes
                    search_nodes(node['data'])
                        
                # If the node is a dictionary with nested subnodes
                elif 'data' in node and isinstance(node['data'], list):
                    search_nodes(node['data'])
        
        # Start the search in the data nodes
        search_nodes(data_nodes)
        
        # If no node was found, return None
        if not found_nodes:
            return None
        
        # Sort the found nodes by creation date (most recent first)
        sorted_nodes = sorted(found_nodes, key=lambda x: x['creation'], reverse=True)
        
        # Return the value of the node with the most recent creation date
        return sorted_nodes[0]['value'] if sorted_nodes else None
        
    def _find_lastc_value_for_path(self, path, data_nodes):
        """
        Finds the first value for a given path in the tree data,
        where the "creation" date is the oldest.
        
        Args:
            path: Path to be searched (ex: "e00001v")
            data_nodes: List of data nodes to be searched
            
        Returns:
            The value of the first node with the specified path whose creation date is the oldest
        """
        # List to store the found nodes with their creation dates
        found_nodes = []
        
        # Traverse the data nodes recursively
        def search_nodes(nodes):
            if not nodes or not isinstance(nodes, list):
                return
                
            for node in nodes:
                # Check if the node has fields and creation date
                if 'fields' in node and node['fields'] is not None and 'creation' in node:
                    for field in node['fields']:
                        if field.get('path') == path:
                            # Store the value, creation date, and node
                            found_nodes.append({
                                'value': field.get('value'),
                                'creation': node.get('creation'),
                                'node': node
                            })
                
                # Search in subnodes recursively
                if 'data' in node and node['data']:
                    # Check specific subnodes for the path
                    for data_item in node['data']:
                        if isinstance(data_item, dict) and 'path' in data_item and data_item['path'] == path and 'data' in data_item and data_item['data']:
                            # For each subnode corresponding to the path, check its data
                            for sub_node in data_item['data']:
                                if 'fields' in sub_node and sub_node['fields'] and 'creation' in sub_node:
                                    # Store the value, creation date, and node
                                    found_nodes.append({
                                        'value': sub_node['fields'][0].get('value'),
                                        'creation': sub_node.get('creation'),
                                        'node': sub_node
                                    })
                    
                    # Search recursively in all subnodes
                    search_nodes(node['data'])
                        
                # If the node is a dictionary with nested subnodes
                elif 'data' in node and isinstance(node['data'], list):
                    search_nodes(node['data'])
        
        # Start the search in the data nodes
        search_nodes(data_nodes)
        
        # If no node was found, return None
        if not found_nodes:
            return None
        
        # Sort the found nodes by creation date (oldest first - without reverse=True)
        sorted_nodes = sorted(found_nodes, key=lambda x: x['creation'])
        
        # Return the value of the node with the oldest creation date
        return sorted_nodes[0]['value'] if sorted_nodes else None
    
    def filter_tree_data(
            self, 
            tree_data: Dict, 
            return_paths: List[str], 
            record_id: Optional[str] = None, 
            filter_expr: Optional[str] = None, 
            lock_node: Optional[bool] = False) -> Union[List[Dict], Dict[str, Any]]:
        # logger.info(f"===== Starting filter operation =====")
        """
        Filters tree data using a custom conditional expression.
        
        This is the main API function for filtering hierarchical data. It converts the
        provided conditional expression into a Python function and uses it to filter
        the tree data, with support for special functions and hierarchical filtering.
        
        Args:
            tree_data: Tree data in JSON format
            filter_expr: Conditional expression (ex: "e00001v == 1 and e00002v != True")
            return_paths: Optional list of paths to extract values from filtered records.
                        If provided, the function returns a dictionary mapping each path
                        to its corresponding values from the filtered records.
            record_id: Optional record ID to limit the search
            lock_node: Optional flag to lock the search on the record ID
            
        Returns:
            If return_paths is None:
                List of filtered records that match the expression
            If return_paths is provided:
                Dictionary mapping each path to the list of values extracted from filtered records
        """

        filter_function = None

        def filter_global(records):
            # logger.debug(f"Performing global recursive filter on {len(records) if isinstance(records, list) else 'non-list'} records")
            
            g_filtered_records = []
            
            # Apply the filter function to each record
            for record in records:
                
                #if 'id' in record and 'fields' in record and isinstance(record, dict):
                if record.get('fields',[]):
                    # logger.debug(f"Evaluating record with ID: {record.get('id')} path {record.get('fields')[0]['path']}")
                    if filter_function is not None and filter_function(record, tree_data):
                        g_filtered_records.append(record)

                if isinstance(record, dict) and 'data' in record and record['data']:
                    g_filtered_records.extend(filter_global(record["data"]))
                    # f_record = filter_global(record["data"])
                    # if f_record:
                    #     if self.filtered_nodes:
                    #         g_filtered_records.append(self.filtered_nodes)
                    #     else:
                    #         g_filtered_records.append(record)

            return g_filtered_records

        def use_cache(filter_expr: str, lock_node: bool, return_paths: Dict):
            # Cria chave do cache
            cache_hash = self._create_cache_hash(filter_expr, lock_node, return_paths)
            return self.result_cache.get(cache_hash, None)    

        def set_cache(filter_expr: str, lock_node: bool, return_paths: Dict, value):
            # Cria chave do cache
            cache_hash = self._create_cache_hash(filter_expr, lock_node, return_paths)
            self.result_cache[cache_hash] = value

        if filter_expr:
            logger.info(f"Starting filter operation with expression: {filter_expr}")
        if record_id:
            logger.info(f"Filtering with record_id: {record_id}")
        if return_paths:
            logger.info(f"Extracting values for paths: {return_paths}")
        
        # Initialize the expression converter
        # logger.debug("Creating tree_data_filter instance for parsing and evaluating expressions")
        #converter = tree_data_filter()
        
        # Convert the expression to a Python filter function
        if filter_expr:
            try:
                #logger.debug("Converting filter expression to Python function")
                #filter_function = converter.convert_to_python_function(filter_expr)
                filter_function = self.convert_to_python_function(filter_expr)
                #logger.debug("Filter function created successfully")
            except Exception as e:
                error_msg = f"Error converting expression '{filter_expr}': {str(e)}"
                logger.error(error_msg)
                print(error_msg)  # Keep original behavior for backward compatibility
                return []
        
        values_return = []

        # If we have a record_id, we need to check if the path (path_expr) is internal to that record
        if record_id:
            # logger.debug(f"Looking for record with ID: {record_id}")

            # Find the record and childs with the specified ID
            record_node = self._find_record_by_id(tree_data, record_id)

            # If the record is found, first we can limit the search to this record and its children
            if record_node:

                # logger.info(f"Found record with ID: {record_id}")

                # The path seems to be internal to the record, so we limit the search to this record
                # and its children
                records = self._extract_records_from_node(record_node)
                # logger.debug(f"Extracted {len(records)} records from node with ID: {record_id}")
                
                # Apply the filter function to each record
                if filter_expr:
                    filtered_records = []
                    for record in records:
                        if isinstance(record, dict) and filter_function(record, tree_data):
                            filtered_records.append(record)
                else:
                    filtered_records = records

                # logger.info(f"Found {len(filtered_records)} matching records in record with ID: {record_id}")
                # logger.debug(f"Extracting values for {len(return_paths)} paths from filtered records")

                # Extract values for specified paths if return_paths is provided
                result = self._extract_values_for_paths(filtered_records, return_paths)
                
                # logger.info(f"Extracted values for {len(result)} paths")

                # Check if the paths are internal to the record
                for path in return_paths:                        
                    if len(result[path])>0:
                        values_return.append({"path": path, "values": result[path]})

                # If the path doesn't seem to be internal, we continue with the global search below
                for path in values_return:
                    return_paths.remove(path["path"])

                # All paths are internal to the record, so we return the values
                if return_paths == []:
                    # logger.info(f"All paths processed internally to record {record_id}, returning {len(values_return)} results")
                    return values_return

                # Aggr function with _node, lock search on the record
                if lock_node:
                    for path in return_paths:
                        values_return.append({"path": path, "values": []})                   
                    return values_return

        # If we get here, we're not limiting the search to a specific record
        # or the path_expr is not inside the record_id, so we ignore the record_id
        # logger.debug("Performing global search without record_id restriction")

        # CACHE
        # Check if the paths are internal to the record
        cache_value = use_cache(filter_expr, lock_node, return_paths)
        if cache_value:
            return cache_value

        # # If the path doesn't seem to be internal, we continue with the global search below
        # for path in values_return:
        #     return_paths.remove(path["path"])
                    
        # if return_paths == []:
        #     return values_return
        # # CACHE

        # Get all records from the tree data
        # records = []
        # data_nodes = tree_data.get('data', [])
        records = tree_data.get('data', [])
        
        # Traverse the tree data to extract all records, only first level
        # for node in data_nodes:
        #     if 'data' in node:
        #         nodes_data = node['data']
        #         if isinstance(nodes_data, list):
        #             records.extend(nodes_data)

        # logger.debug(f"Found {len(records)} records to filter")

        # Apply the filter function to each record
        if filter_expr:
            self.filtered_nodes = []
            r_global = filter_global(records)
            if isinstance(r_global, dict) and 'data' in r_global:
                filtered_records = r_global['data']
            elif isinstance(r_global, list):
                filtered_records = r_global
            else:
                filtered_records = []
            # for record in records:
            #     if isinstance(record, dict) and filter_function(record, tree_data):
            #         filtered_records.append(record)            
        else:
            filtered_records = records
        
        # logger.info(f"Filter applied: found {len(filtered_records)} matching records out of {len(records)}")
        
        # Extract values for specified paths if return_paths is provided
        # logger.debug(f"Extracting values for {len(return_paths)} paths from filtered records")
        result = self._extract_values_for_paths(filtered_records, return_paths)
        # logger.info(f"Extracted values for {len(result)} paths")

        for path in return_paths:                        
            if len(result[path])>0:
                # set_cache(path, filter_expr, lock_node, result[path])
                values_return.append({"path": path, "values": result[path]})

        # CACHE
        # Check if the paths are internal to the record
        set_cache(filter_expr, lock_node, return_paths, values_return)

        return values_return

    def _extract_values_for_paths(self, records: List[Dict], paths: List[str]) -> Dict[str, List[Any]]:
        """
        Extracts values for specified paths from a list of records.
        
        Args:
            records: List of filtered records to extract values from
            paths: List of paths to extract values for
            
        Returns:
            Dictionary mapping each path to a list of values extracted from the records
        """
        # logger.debug(f"Extracting values for {len(paths)} paths from {len(records)} records")
        result = {path: [] for path in paths}
        converter = tree_data_filter()
        
        for path in paths:
            
            # Initialize the result for the path
            result[path] = []

            # logger.debug(f"Processing path: {path}")

            # Handle special functions (first, last, firstc, lastc)
            if path.startswith("first(") and path.endswith(")"):

                # Extract the field path from first(...)
                field_path = path[6:-1]
                # logger.debug(f"Extracting first value for field: {field_path}")
                value = converter._find_first_value_for_path(field_path, records)
                result[path] = [value] if value is not None else []
                # if value:
                #     logger.debug(f"First value for {field_path}: {value}")
                # else:
                #     logger.warning(f"Cannot extract first value: {field_path} not found")
                if not value:
                    logger.warning(f"Cannot extract first value: {field_path} not found")

                continue
                
            elif path.startswith("last(") and path.endswith(")"):
                # Extract the field path from last(...)
                field_path = path[5:-1]
                # logger.debug(f"Extracting last value for field: {field_path}")
                value = converter._find_last_value_for_path(field_path, records)
                result[path] = [value] if value is not None else []
                # if value:
                #     logger.debug(f"Last value for {field_path}: {value}")            
                # else:
                #     logger.warning(f"Cannot extract last value: {field_path} not found")
                # if not value:
                #     logger.debug(f"Last value for {field_path}: {value}")            
                continue
                
            elif path.startswith("firstc(") and path.endswith(")"):
                # Extract the field path from firstc(...)
                field_path = path[7:-1]
                # logger.debug(f"Extracting first value by creation date for field: {field_path}")
                value = converter._find_firstc_value_for_path(field_path, records)
                result[path] = [value] if value is not None else []
                # if value:
                #     logger.debug(f"First value by creation date for {field_path}: {value}")
                # else:
                #     logger.warning(f"Cannot extract firstc value: {field_path} not found")
                # if not value:
                #     logger.warning(f"Cannot extract firstc value: {field_path} not found")

                continue
                
            elif path.startswith("lastc(") and path.endswith(")"):
                # Extract the field path from lastc(...)
                field_path = path[6:-1]
                # logger.debug(f"Extracting last value by creation date for field: {field_path}")
                value = converter._find_lastc_value_for_path(field_path, records)
                result[path] = [value] if value is not None else []
                # if value:
                #     logger.debug(f"Last value by creation date for {field_path}: {value}")
                # else:
                #     logger.warning(f"Cannot extract lastc value: {field_path} not found")
                # if not value:
                #     logger.warning(f"Cannot extract lastc value: {field_path} not found")                
                continue
            
            # Regular field path
            # logger.debug(f"Extracting values for regular path: {path}")
            values = converter._find_value_for_path(path, records)
            result[path] = values if values is not None else []
            # if values:
            #     logger.debug(f"Last value by creation date for {path}: {values}")
            # else:
            #     logger.warning(f"Cannot extract lastc value: {path} not found")        
            # if not values:
            #     logger.warning(f"Cannot extract lastc value: {path} not found")               
        
        # logger.debug(f"Extraction complete. Result has {len(result)} paths")

        return result

    def _find_record_by_id(self, tree_data: Dict, record_id: str) -> Optional[Dict]:
        """
        Finds a specific record by ID in the tree data.
        
        This function recursively searches the entire tree data for a node that has
        the specified ID. Useful for limiting the search to a specific record in
        hierarchical queries.
        
        Args:
            tree_data: Tree data in JSON format
            record_id: ID of the record to find
            
        Returns:
            The found record node or None if not found
        """
        def search_nodes(nodes):
            """Internal recursive function to search for a node by ID"""
            if not nodes or not isinstance(nodes, list):
                return None
                
            for node in nodes:
                # Check if this is the node we're looking for
                if isinstance(node, dict) and node.get('id') == record_id:
                    return node
                
                # Search in subnodes
                if isinstance(node, dict) and 'data' in node and node['data']:
                    result = search_nodes(node['data'])
                    if result:
                        return result
            
            return None
        
        # Start the search from the root level
        if 'data' in tree_data:
            return search_nodes(tree_data['data'])
        
        return None

    def _extract_records_from_node(self, node: Dict) -> List[Dict]:
        """
        Extracts all records (including subnodes) from a specific node.
        
        This function is useful for extracting an entire branch of the tree starting from
        a specific node, including the node itself and all its descendants.
        
        Args:
            node: Node from which to extract records
            
        Returns:
            List of records extracted from the node and its subnodes
        """
        records = [node]  # Include the node itself
        
        def extract_recursive(current_node, collected_records):
            """Internal recursive function to extract all nodes from a branch"""
            # If the node has nested data, add them too
            if isinstance(current_node, dict) and 'data' in current_node and current_node['data']:
                for subnode in current_node['data']:
                    if isinstance(subnode, dict):
                        collected_records.append(subnode)
                        extract_recursive(subnode, collected_records)
        
        # Start the recursive extraction
        extract_recursive(node, records)
        
        return records
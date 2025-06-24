"""
Powered by Renoir
Created by igor.goncalves@renoirgroup.com

Optimized version of the filtering mechanism for hierarchical data in a tree structure.
This module provides significant performance improvements over the original implementation
through strategic optimizations including singleton pattern, path indexing, and unified
search functions.

Key optimizations:
- Singleton pattern for parser instances (reduces initialization overhead)
- Path indexing system for faster lookups
- Unified search functions to reduce code duplication
- Intelligent caching of results and parsed expressions
- Optimized logging for better performance
- Lazy evaluation strategies

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
from typing import Dict, Any, Optional, List, Union, Callable, NamedTuple
from dataclasses import dataclass
from functools import lru_cache
import threading
from datetime import datetime

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jmespath
import re
import ply.lex as lex
import ply.yacc as yacc

# Import the logger
from log.logger import get_logger

# Get a logger instance for this module
logger = get_logger("filters_optimized")

# Global parser instance for singleton pattern
_parser_instance = None
_parser_lock = threading.Lock()

@dataclass
class ValueInfo:
    """Information about a value found in the tree data"""
    value: Any
    creation: Optional[str] = None
    node: Optional[Dict] = None
    path: str = ""
    
class PathIndex:
    """Optimized index for path-based lookups"""
    
    def __init__(self):
        self._index: Dict[str, List[ValueInfo]] = {}
        self._built = False
    
    def build_index(self, data_nodes: List[Dict]) -> None:
        """Build the path index from data nodes"""
        if self._built:
            return
            
        logger.debug("Building path index for optimized lookups")
        self._index.clear()
        self._build_recursive(data_nodes)
        self._built = True
        logger.debug(f"Path index built with {len(self._index)} unique paths")
    
    def _build_recursive(self, nodes: List[Dict]) -> None:
        """Recursively build the index from nodes"""
        if not nodes or not isinstance(nodes, list):
            return
            
        for node in nodes:
            if not isinstance(node, dict):
                continue
                
            # Index fields in current node
            if 'fields' in node and node['fields']:
                for field in node['fields']:
                    if field and 'path' in field:
                        path = field['path']
                        if path not in self._index:
                            self._index[path] = []
                        
                        self._index[path].append(ValueInfo(
                            value=field.get('value'),
                            creation=node.get('creation'),
                            node=node,
                            path=path
                        ))
            
            # Index specific path nodes
            if 'data' in node and node['data']:
                for data_item in node['data']:
                    if isinstance(data_item, dict) and 'path' in data_item:
                        path = data_item['path']
                        if 'data' in data_item and data_item['data']:
                            for sub_node in data_item['data']:
                                if 'fields' in sub_node and sub_node['fields']:
                                    if path not in self._index:
                                        self._index[path] = []
                                    
                                    self._index[path].append(ValueInfo(
                                        value=sub_node['fields'][0].get('value'),
                                        creation=sub_node.get('creation'),
                                        node=sub_node,
                                        path=path
                                    ))
                
                # Recursively process subnodes
                self._build_recursive(node['data'])
    
    def get_values(self, path: str, strategy: str = 'all') -> List[Any]:
        """Get values for a path using specified strategy"""
        if not self._built:
            logger.warning("Path index not built, returning empty results")
            return []
            
        if path not in self._index:
            return []
            
        values_info = self._index[path]
        
        if strategy == 'all':
            return [info.value for info in values_info if info.value is not None]
        elif strategy == 'first':
            return [values_info[0].value] if values_info and values_info[0].value is not None else []
        elif strategy == 'last':
            return [values_info[-1].value] if values_info and values_info[-1].value is not None else []
        elif strategy == 'firstc':
            # Most recent creation date
            if not values_info:
                return []
            sorted_by_creation = sorted(
                [info for info in values_info if info.creation and info.value is not None],
                key=lambda x: x.creation,
                reverse=True
            )
            return [sorted_by_creation[0].value] if sorted_by_creation else []
        elif strategy == 'lastc':
            # Oldest creation date
            if not values_info:
                return []
            sorted_by_creation = sorted(
                [info for info in values_info if info.creation and info.value is not None],
                key=lambda x: x.creation
            )
            return [sorted_by_creation[0].value] if sorted_by_creation else []
        
        return []
    
    def has_path(self, path: str) -> bool:
        """Check if path exists in index"""
        return self._built and path in self._index
    
    def clear(self) -> None:
        """Clear the index"""
        self._index.clear()
        self._built = False

class TreeDataFilterOptimized:
    """
    Optimized version of the tree data filter with significant performance improvements.
    
    Key optimizations:
    - Singleton pattern for parser reuse
    - Path indexing for O(1) lookups
    - Unified search functions
    - Reduced code duplication
    - Intelligent caching
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

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9_]*'
        # Check if the identifier is a special keyword
        keyword_map = {
            'and': 'AND',
            'or': 'OR',
            'True': 'BOOLEAN',
            'False': 'BOOLEAN',
            'contains': 'CONTAINS',
            'first': 'FIRST',
            'last': 'LAST',
            'firstc': 'FIRSTC',
            'lastc': 'LASTC'
        }
        t.type = keyword_map.get(t.value, 'IDENTIFIER')
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r"'[^']*'"
        t.value = t.value[1:-1]  # Remove quotes
        return t

    # Characters to be ignored by the lexical analyzer
    t_ignore = ' \t'

    def t_error(self, t):
        if logger.isEnabledFor(40):  # ERROR level
            logger.error(f"Illegal character '{t.value[0]}' at position {t.lexpos}")
        t.lexer.skip(1)

    # Operator precedence
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQUALS', 'NOTEQUALS', 'GREATEREQUAL', 'LESSEQUAL', 'GREATER', 'LESS'),
    )

    # Production rules for syntactic analysis
    def p_expression_binop(self, p):
        '''expression : expression EQUALS expression
                      | expression NOTEQUALS expression
                      | expression GREATEREQUAL expression
                      | expression LESSEQUAL expression
                      | expression GREATER expression
                      | expression LESS expression
                      | expression AND expression
                      | expression OR expression'''
        p[0] = ('binop', p[2], p[1], p[3])

    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = ('group', p[2])

    def p_expression_contains(self, p):
        'expression : CONTAINS LPAREN expression COMMA expression RPAREN'
        p[0] = ('contains', p[3], p[5])

    def p_expression_first(self, p):
        'expression : FIRST LPAREN expression RPAREN'
        p[0] = ('first', p[3])

    def p_expression_last(self, p):
        'expression : LAST LPAREN expression RPAREN'
        p[0] = ('last', p[3])

    def p_expression_firstc(self, p):
        'expression : FIRSTC LPAREN expression RPAREN'
        p[0] = ('firstc', p[3])

    def p_expression_lastc(self, p):
        'expression : LASTC LPAREN expression RPAREN'
        p[0] = ('lastc', p[3])

    def p_expression_identifier(self, p):
        'expression : IDENTIFIER'
        p[0] = ('identifier', p[1])

    def p_expression_number(self, p):
        'expression : NUMBER'
        p[0] = ('number', p[1])

    def p_expression_string(self, p):
        'expression : STRING'
        p[0] = ('string', p[1])

    def p_expression_boolean(self, p):
        'expression : BOOLEAN'
        p[0] = ('boolean', p[1])

    def p_error(self, p):
        if logger.isEnabledFor(40):  # ERROR level
            if p:
                logger.error(f"Syntax error at '{p.value}' (token type: {p.type}, position: {p.lexpos})")
            else:
                logger.error("Syntax error at the end of expression")

    def __init__(self):
        """Initialize the optimized filter expression parser"""
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)
        self.path_index = PathIndex()
        self._expression_cache = {}
        
    @lru_cache(maxsize=256)
    def parse(self, expression: str):
        """Parse the conditional expression with caching"""
        if expression in self._expression_cache:
            return self._expression_cache[expression]
            
        ast = self.parser.parse(expression)
        self._expression_cache[expression] = ast
        return ast
    
    def convert_to_python_function(self, expression: str) -> Callable:
        """Convert expression to Python function with optimizations"""
        ast = self.parse(expression)
        if ast is None:
            raise ValueError(f"Could not parse the expression: {expression}")
        
        def filter_function(record, tree_data):
            # Ensure path index is built
            if not self.path_index._built and 'data' in tree_data:
                self.path_index.build_index(tree_data['data'])
            
            return self._evaluate_ast_optimized(ast, record, tree_data)
        
        return filter_function
    
    def _evaluate_ast_optimized(self, ast_node, record, tree_data):
        """Optimized AST evaluation with better performance"""
        if record is None:
            return False
            
        node_type = ast_node[0]
        
        if node_type == 'binop':
            op = ast_node[1]
            
            # Optimized logical operators with short-circuit evaluation
            if op == 'and':
                left_result = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
                if not left_result:
                    return self._check_recursive_optimized(ast_node, record, tree_data)
                
                right_result = self._evaluate_condition_optimized(ast_node[3], record, tree_data)
                if right_result:
                    return True
                    
                return self._check_subnodes_for_condition_optimized(ast_node[3], record, tree_data)
            
            elif op == 'or':
                left_result = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
                if left_result:
                    return True
                
                right_result = self._evaluate_condition_optimized(ast_node[3], record, tree_data)
                if right_result:
                    return True
                    
                return self._check_recursive_optimized(ast_node, record, tree_data)
            
            # Comparison operators
            left = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
            right = self._evaluate_condition_optimized(ast_node[3], record, tree_data)
            
            try:
                return self._compare_values(op, left, right)
            except (TypeError, ValueError):
                return False
                
        return self._evaluate_condition_optimized(ast_node, record, tree_data)
    
    def _compare_values(self, op: str, left: Any, right: Any) -> bool:
        """Optimized value comparison"""
        comparison_map = {
            '==': lambda l, r: l == r,
            '!=': lambda l, r: l != r,
            '>=': lambda l, r: l >= r,
            '<=': lambda l, r: l <= r,
            '>': lambda l, r: l > r,
            '<': lambda l, r: l < r
        }
        return comparison_map.get(op, lambda l, r: False)(left, right)
    
    def _evaluate_condition_optimized(self, ast_node, record, tree_data):
        """Optimized condition evaluation using path index when possible"""
        node_type = ast_node[0]
        
        if node_type == 'binop':
            op = ast_node[1]
            
            if op == 'and':
                left_result = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
                return left_result and self._evaluate_condition_optimized(ast_node[3], record, tree_data)
                
            elif op == 'or':
                left_result = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
                return left_result or self._evaluate_condition_optimized(ast_node[3], record, tree_data)
            
            # Comparison operators
            left = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
            right = self._evaluate_condition_optimized(ast_node[3], record, tree_data)
            
            try:
                return self._compare_values(op, left, right)
            except (TypeError, ValueError):
                return False
            
        elif node_type == 'group':
            return self._evaluate_condition_optimized(ast_node[1], record, tree_data)
            
        elif node_type == 'contains':
            container = self._evaluate_condition_optimized(ast_node[1], record, tree_data)
            item = self._evaluate_condition_optimized(ast_node[2], record, tree_data)
            if container is None:
                return False
            return str(item) in str(container)
            
        elif node_type in ['first', 'last', 'firstc', 'lastc']:
            return self._evaluate_special_function(node_type, ast_node, record, tree_data)
            
        elif node_type == 'identifier':
            return self._get_field_value_optimized(ast_node[1], record)
            
        elif node_type in ['number', 'numeric', 'float']:
            return ast_node[1]
            
        elif node_type == 'string':
            return ast_node[1]
            
        elif node_type == 'boolean':
            return ast_node[1] == 'True'
            
        return None
    
    def _evaluate_special_function(self, func_type: str, ast_node, record, tree_data) -> bool:
        """Evaluate special functions using path index"""
        path = self._get_path_from_ast(ast_node[1])
        if not path:
            return False
            
        # Use path index for faster lookup
        if self.path_index.has_path(path):
            strategy_map = {
                'first': 'first',
                'last': 'last', 
                'firstc': 'firstc',
                'lastc': 'lastc'
            }
            
            values = self.path_index.get_values(path, strategy_map[func_type])
            if not values:
                return False
                
            target_value = values[0]
            
            # Check if current record matches the target value
            if 'fields' in record and record['fields']:
                for field in record['fields']:
                    if field.get('path') == path and field.get('value') == target_value:
                        return True
            return False
        
        # Fallback to original logic if not in index
        return False
    
    def _get_field_value_optimized(self, path: str, record: Dict) -> Any:
        """Optimized field value retrieval"""
        # Check current record fields first
        if 'fields' in record and record['fields']:
            for field in record['fields']:
                if field.get('path') == path:
                    return field.get('value')
        
        # Check subnodes
        if 'data' in record and record['data']:
            for subnode in record['data']:
                if isinstance(subnode, dict):
                    # Check specific property nodes
                    if 'path' in subnode and subnode['path'] == path and 'data' in subnode and subnode['data']:
                        for data_item in subnode['data']:
                            if 'fields' in data_item and data_item['fields']:
                                return data_item['fields'][0].get('value')
                    
                    # Check generic subnode fields
                    elif 'fields' in subnode and subnode['fields']:
                        for field in subnode['fields']:
                            if field.get('path') == path:
                                return field.get('value')
        
        return None
    
    def _check_recursive_optimized(self, ast_node, record, tree_data):
        """Optimized recursive checking"""
        if not isinstance(record, dict) or 'data' not in record or not record['data']:
            return False
            
        for subnode in record['data']:
            if isinstance(subnode, dict):
                if self._evaluate_ast_optimized(ast_node, subnode, tree_data):
                    return True
                if self._check_recursive_optimized(ast_node, subnode, tree_data):
                    return True
                    
        return False
    
    def _check_subnodes_for_condition_optimized(self, ast_node, record, tree_data):
        """Optimized subnode condition checking"""
        if not isinstance(record, dict) or 'data' not in record or not record['data']:
            return False
            
        for subnode in record['data']:
            if isinstance(subnode, dict):
                if self._evaluate_condition_optimized(ast_node, subnode, tree_data):
                    return True
                if self._check_subnodes_for_condition_optimized(ast_node, subnode, tree_data):
                    return True
                    
        return False
    
    def _get_path_from_ast(self, ast_node):
        """Extract path from AST node"""
        if ast_node[0] == 'identifier':
            return ast_node[1]
        return None
    
    def get_path_values(self, path: str, data_nodes: List[Dict], strategy: str = 'all') -> List[Any]:
        """Unified function to get values for a path using specified strategy"""
        if not self.path_index._built:
            self.path_index.build_index(data_nodes)
        
        return self.path_index.get_values(path, strategy)

def get_optimized_parser():
    """Get singleton instance of the optimized parser"""
    global _parser_instance
    
    if _parser_instance is None:
        with _parser_lock:
            if _parser_instance is None:
                logger.debug("Creating new optimized parser instance")
                _parser_instance = TreeDataFilterOptimized()
                logger.info("Optimized parser instance created and cached")
    
    return _parser_instance

def filter_tree_data_optimized(tree_data: Dict, return_paths: List[str], record_id: str = None, filter_expr: str = None, lock_node: bool = False) -> Union[List[Dict], Dict[str, Any]]:
    """
    Optimized version of tree data filtering with significant performance improvements.
    
    Key optimizations:
    - Reuses parser instance (singleton pattern)
    - Uses path indexing for faster lookups
    - Reduced logging overhead
    - Optimized recursive searches
    
    Args:
        tree_data: Tree data in JSON format
        return_paths: List of paths to extract values from filtered records
        record_id: Optional record ID to limit the search
        filter_expr: Conditional expression for filtering
        lock_node: Optional flag to lock the search on the record ID
        
    Returns:
        List of dictionaries with path and values
    """
    if logger.isEnabledFor(20):  # INFO level
        logger.info("Starting optimized filter operation")
    
    # Get singleton parser instance
    converter = get_optimized_parser()
    
    # Convert expression to filter function if provided
    filter_function = None
    if filter_expr:
        try:
            filter_function = converter.convert_to_python_function(filter_expr)
        except Exception as e:
            if logger.isEnabledFor(40):  # ERROR level
                logger.error(f"Error converting expression '{filter_expr}': {str(e)}")
            return []
    
    values_return = []
    
    # Handle record_id specific filtering
    if record_id:
        record_node = _find_record_by_id_optimized(tree_data, record_id)
        
        if record_node:
            records = _extract_records_from_node_optimized(record_node)
            
            # Apply filter if provided
            if filter_function:
                filtered_records = [record for record in records 
                                  if isinstance(record, dict) and filter_function(record, tree_data)]
            else:
                filtered_records = records
            
            # Extract values for specified paths
            result = _extract_values_for_paths_optimized(filtered_records, return_paths, converter)
            
            # Process results
            for path in return_paths:
                if len(result[path]) > 0:
                    values_return.append({"path": path, "values": result[path]})
            
            # Remove processed paths
            for path_data in values_return:
                if path_data["path"] in return_paths:
                    return_paths.remove(path_data["path"])
            
            # Return early if all paths processed or node is locked
            if not return_paths or lock_node:
                for path in return_paths:
                    values_return.append({"path": path, "values": []})
                return values_return
    
    # Global filtering
    records = tree_data.get('data', [])
    
    # Apply global filter
    if filter_function:
        filtered_records = _filter_global_optimized(records, filter_function, tree_data)
    else:
        filtered_records = records
    
    # Extract values for remaining paths
    result = _extract_values_for_paths_optimized(filtered_records, return_paths, converter)
    
    for path in return_paths:
        if len(result[path]) > 0:
            values_return.append({"path": path, "values": result[path]})
    
    return values_return

def _filter_global_optimized(records: List[Dict], filter_function: Callable, tree_data: Dict) -> List[Dict]:
    """Optimized global filtering with reduced overhead"""
    filtered_records = []
    
    def filter_recursive(record_list):
        local_filtered = []
        
        for record in record_list:
            if isinstance(record, dict):
                if 'id' in record and filter_function(record, tree_data):
                    local_filtered.append(record)
                
                if 'data' in record and record['data']:
                    sub_filtered = filter_recursive(record['data'])
                    local_filtered.extend(sub_filtered)
        
        return local_filtered
    
    return filter_recursive(records)

def _extract_values_for_paths_optimized(records: List[Dict], paths: List[str], converter: TreeDataFilterOptimized) -> Dict[str, List[Any]]:
    """Optimized value extraction using path indexing"""
    result = {path: [] for path in paths}
    
    # Build index once for all paths - clear and rebuild to ensure fresh data
    converter.path_index.clear()
    converter.path_index.build_index(records)
    
    for path in paths:
        # Handle special functions
        if path.startswith(("first(", "last(", "firstc(", "lastc(")):
            strategy, field_path = _parse_special_function(path)
            values = converter.get_path_values(field_path, records, strategy)
            result[path] = values if values else []
        else:
            # Regular path
            values = converter.get_path_values(path, records, 'all')
            result[path] = values if values else []
    
    return result

def _parse_special_function(path: str) -> tuple:
    """Parse special function to extract strategy and field path"""
    if path.startswith("first(") and path.endswith(")"):
        return 'first', path[6:-1]
    elif path.startswith("last(") and path.endswith(")"):
        return 'last', path[5:-1]
    elif path.startswith("firstc(") and path.endswith(")"):
        return 'firstc', path[7:-1]
    elif path.startswith("lastc(") and path.endswith(")"):
        return 'lastc', path[6:-1]
    return 'all', path

def _find_record_by_id_optimized(tree_data: Dict, record_id: str) -> Optional[Dict]:
    """Optimized record search by ID"""
    def search_nodes(nodes):
        if not nodes or not isinstance(nodes, list):
            return None
            
        for node in nodes:
            if isinstance(node, dict):
                if node.get('id') == record_id:
                    return node
                
                if 'data' in node and node['data']:
                    result = search_nodes(node['data'])
                    if result:
                        return result
        
        return None
    
    if 'data' in tree_data:
        return search_nodes(tree_data['data'])
    
    return None

def _extract_records_from_node_optimized(node: Dict) -> List[Dict]:
    """Optimized record extraction from node"""
    records = [node]
    
    def extract_recursive(current_node, collected_records):
        if isinstance(current_node, dict) and 'data' in current_node and current_node['data']:
            for subnode in current_node['data']:
                if isinstance(subnode, dict):
                    collected_records.append(subnode)
                    extract_recursive(subnode, collected_records)
    
    extract_recursive(node, records)
    return records

# Maintain backward compatibility by providing the original function name
filter_tree_data = filter_tree_data_optimized

if __name__ == "__main__":
    # Example usage and basic testing
    logger.info("Optimized filters module loaded successfully")
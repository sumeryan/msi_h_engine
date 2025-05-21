"""
ASTEval module for safe formula evaluation with NumPy support.

This module provides a standardized way to initialize and configure an asteval
Interpreter instance with numpy support for safe formula evaluation.

Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""
import numpy as np
import re
import log
import os
import json
from asteval import Interpreter

# Setup logging
logger = log.get_logger("Engine Asteval")

def create_interpreter(use_numpy=True, max_time=5.0, readonly=False):
    """
    Create an asteval Interpreter with optional NumPy support and safety features.
    
    Args:
        use_numpy: Whether to include NumPy functions in the interpreter
        max_time: Maximum execution time in seconds
        readonly: Whether to run in readonly mode (safer)
        
    Returns:
        Configured asteval Interpreter instance
    """
    # Start with a minimal set of safe builtins
    safe_builtins = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'complex': complex,
        'dict': dict,
        'enumerate': enumerate,
        'float': float,
        'format': format,
        'int': int,
        'isinstance': isinstance,
        'len': len,
        'list': list,
        'max': max,
        'min': min,
        'pow': pow,
        'range': range,
        'round': round,
        'set': set,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'zip': zip
    }
    
    # Add math functions
    math_funcs = {
        'sqrt': np.sqrt if use_numpy else __import__('math').sqrt,
        'sin': np.sin if use_numpy else __import__('math').sin,
        'cos': np.cos if use_numpy else __import__('math').cos,
        'tan': np.tan if use_numpy else __import__('math').tan,
        'asin': np.arcsin if use_numpy else __import__('math').asin,
        'acos': np.arccos if use_numpy else __import__('math').acos,
        'atan': np.arctan if use_numpy else __import__('math').atan,
        'log': np.log if use_numpy else __import__('math').log,
        'log10': np.log10 if use_numpy else __import__('math').log10,
        'exp': np.exp if use_numpy else __import__('math').exp
    }
    
    # Add NumPy functions if requested
    numpy_funcs = {}
    if use_numpy:
        numpy_funcs = {
            'np': np,
            'array': np.array,
            'mean': np.mean,
            'median': np.median,
            'std': np.std,
            'var': np.var,
            'percentile': np.percentile,
            'sum': np.sum,
            'prod': np.prod,
            'cumsum': np.cumsum,
            'cumprod': np.cumprod,
            'absolute': np.absolute,
            'minimum': np.minimum,
            'maximum': np.maximum,
            'dot': np.dot
        }
    
    # Create custom userfunctions for aggregations
    def safe_avg(vals):
        """Calculate average of values safely"""
        if not vals:
            return 0
        return sum(vals) / len(vals)
    
    def safe_count(vals):
        """Count non-None values"""
        return sum(1 for v in vals if v is not None)
    
    # Aggregation functions
    aggregation_funcs = {
        'avg': safe_avg,
        'average': safe_avg,
        'count': safe_count
    }
    
    # Combine all functions
    all_symbols = {}
    all_symbols.update(safe_builtins)
    all_symbols.update(math_funcs)
    all_symbols.update(numpy_funcs)
    all_symbols.update(aggregation_funcs)
    
    # Define which AST nodes should be blocked for security
    blocked_nodes = ['Import', 'ImportFrom', 'Exec', 'Eval', 
                    'Attribute', 'Call', 'ClassDef', 'FunctionDef',
                    'Delete', 'Assert', 'Raise', 'Try', 'TryExcept',
                    'TryFinally', 'With', 'AsyncFunctionDef', 'AsyncWith',
                    'Global', 'Nonlocal']
    
    # If in readonly mode, block more nodes for extra safety
    if readonly:
        blocked_nodes.extend(['Assign', 'AugAssign', 'AnnAssign'])
    
    # Create the interpreter with our configuration
    interpreter = Interpreter(
        usersyms=all_symbols,
        use_numpy=use_numpy,
        readonly=readonly,
        max_time=max_time,
        no_if=False,  # Allow if-else expressions for formula logic
        builtins_readonly=True,  # Prevent overwriting builtins
        blocked_nodes=blocked_nodes
    )
    
    logger.info(f"Created asteval interpreter: numpy={use_numpy}, max_time={max_time}s, readonly={readonly}")
    
    return interpreter

# # def evaluate_formula(formula, variables=None, use_numpy=True, max_time=5.0):
#     """
#     Evaluate a formula string using asteval with the provided variables.

#     Args:
#         formula: Formula string to evaluate
#         variables: Dictionary of variables to use in evaluation
#         use_numpy: Whether to include NumPy functions
#         max_time: Maximum execution time in seconds

#     Returns:
#         Result of formula evaluation
#     """
#     # Create interpreter
#     interpreter = create_interpreter(use_numpy=use_numpy, max_time=max_time)

#     # Add variables to interpreter's symbol table
#     if variables:
#         for name, value in variables.items():
#             interpreter.symtable[name] = value
#             if isinstance(value, list) and len(value) < 10:
#                 logger.debug(f"Variable {name} = {value}")
#             elif isinstance(value, list):
#                 logger.debug(f"Variable {name} = list with {len(value)} items")

#     # Log the formula being sent to the interpreter
#     logger.info(f"Sending formula to evaluator: '{formula}'")

#     # Print variable types for debugging
#     var_types = {name: type(value).__name__ for name, value in variables.items() if name in formula}
#     logger.debug(f"Variable types in formula: {var_types}")

#     # Evaluate the formula
#     try:
#         result = interpreter.eval(formula)

#         # Check for errors in the interpreter
#         if len(interpreter.error) > 0:
#             error_msg = interpreter.error[0].get_error()
#             logger.error(f"Error evaluating formula '{formula}': {error_msg}")
#             return None

#         # Log the result
#         if isinstance(result, (list, np.ndarray)) and len(str(result)) > 100:
#             logger.info(f"Result type: {type(result).__name__}, length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
#         else:
#             logger.info(f"Result: {result}")

#         return result
#     except Exception as e:
#         logger.error(f"Exception evaluating formula '{formula}': {str(e)}")
#         return None

def eval_formula(entities_eval, formulas):
    
    def get_formula(path):
        for f0 in formulas:
            for f1 in f0["formulas"]:
                if f1["path"] == path:
                    return f1
    
    def get_aggr(base, formula):
        for aggr in formula["parsed"]["aggr"]:
            if aggr["base"] == base:
                return aggr

    def find_vars_position(formular):
        pattern = r'e\d{5}v'
        matches = re.finditer(pattern, formular)
        
        # Retorna uma lista de tuplas (índice_inicial, índice_final, texto_encontrado)
        return [(match.start(), match.end(), match.group()) for match in matches]

    counter = 0

    for entity in entities_eval:
        
        for id_eval in entity["formula_data"]["formulas"]:

            aeval = create_interpreter(use_numpy=True, max_time=5.0, readonly=False)
            
            # Get the formula
            formula = get_formula(id_eval["formula"])
            formula_str = formula["value"]

            # first processes aggregation functions
            for i, value in enumerate(id_eval["data"]):
                if "aggr" in value:
                    # Get the aggregation function
                    aggr = get_aggr(value["aggr"]["base"], formula)
                    for v in aggr["vars"]:
                        counter += 1
                        new_var = f"{v}_{counter}"
                        formula_str = formula_str.replace(aggr["base"], aggr["eval"].replace(v, new_var))

                        # Add the variable to the interpreter
                        aeval.symtable[new_var] = value["values"][0]

            # Other variables
            for i, value in enumerate(id_eval["data"]):
                if "non_aggr" in value:
                    # Get the aggregation function
                    counter += 1
                    pattern = r'e\d{5}v'
                    matches = re.search(pattern, value["non_aggr"]["path"])
                    var = matches.group()
                    new_var = f"{var}_{counter}"
                    formula_str = formula_str.replace(var, new_var)

                    # Add the variable to the interpreter
                    aeval.symtable[new_var] = np.array(value["non_aggr"]["values"])

            result = aeval(formula_str)
            if result is None:
                print(f"Error evaluating formula: {formula_str}")
                continue
            print(f"Formula: {formula_str} => Result: {result}")

    return None
    

if __name__ == "__main__":

    # Get the current directory for file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths for input and output files
    formulas_json = os.path.join(current_dir, "extracted_formulas.json")
    entities_eval_json = os.path.join(current_dir, "processed_formulas_with_variables.json")

    with open(formulas_json, 'r', encoding='utf-8') as f:
        formulas = json.load(f)    

    with open(entities_eval_json, 'r', encoding='utf-8') as f:
        entities_eval = json.load(f)    

    eval_formula(entities_eval, formulas)
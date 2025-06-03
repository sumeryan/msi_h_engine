"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

ASTEval module for safe formula evaluation with NumPy support.

This module provides a standardized way to initialize and configure an asteval
Interpreter instance with numpy support for safe formula evaluation. It handles
secure parsing and evaluation of mathematical formulas with variable substitution
while preventing malicious code execution.

The module includes:
- Configuration of a restricted execution environment
- Safe mathematical and statistical functions
- Support for NumPy array operations
- Custom aggregation functions for data analysis
- Comprehensive formula evaluation with error handling

"""
import numpy as np
import re
import log
import os
import json
from asteval import Interpreter

# Setup logging
logger = log.get_logger("Engine Eval")

# Helper function for aligned logging
def log_info(message, indent=0):
    """Log info message with proper indentation."""
    prefix = "  " * indent
    logger.info(f"{prefix}{message}")

def log_debug(message, indent=0):
    """Log debug message with proper indentation."""
    prefix = "  " * indent
    logger.debug(f"{prefix}{message}")

def log_error(message, indent=0):
    """Log error message with proper indentation."""
    prefix = "  " * indent
    logger.error(f"{prefix}{message}")

def log_warning(message, indent=0):
    """Log warning message with proper indentation."""
    prefix = "  " * indent
    logger.warning(f"{prefix}{message}")

def convert_numpy_types(obj):
    """
    Convert numpy data types to Python native types for JSON serialization.
    
    This function recursively converts numpy integers, floats, and arrays
    to their Python equivalents to ensure JSON serialization compatibility.
    
    Args:
        obj: The object to convert (can be dict, list, numpy type, etc.)
        
    Returns:
        The converted object with all numpy types replaced by Python native types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def create_interpreter(use_numpy=True, max_time=5.0, readonly=False):
    """
    Create an asteval Interpreter with optional NumPy support and safety features.
    
    This function initializes a restricted Python expression evaluator with 
    carefully selected safe functions. It prevents access to potentially dangerous
    operations while providing rich mathematical functionality.
    
    Args:
        use_numpy (bool): Whether to include NumPy functions in the interpreter. Default is True.
        max_time (float): Maximum execution time in seconds to prevent infinite loops. Default is 5.0.
        readonly (bool): Whether to run in readonly mode (blocks assignment operations for added safety). Default is False.
        
    Returns:
        Interpreter: Configured asteval Interpreter instance ready for safe formula evaluation
    """
    logger.debug(f"Creating interpreter with params: use_numpy={use_numpy}, max_time={max_time}, readonly={readonly}")
    
    # Start with a minimal set of safe builtins
    numpy_functions = {
        # Funções matemáticas básicas
        'sum': np.sum,            # Soma de elementos
        'mean': np.mean,          # Média aritmética
        'average': np.average,    # Média ponderada
        'median': np.median,      # Mediana
        'std': np.std,            # Desvio padrão
        'var': np.var,            # Variância
        'min': np.min,            # Valor mínimo
        'max': np.max,            # Valor máximo
        'argmin': np.argmin,      # Índice do valor mínimo
        'argmax': np.argmax,      # Índice do valor máximo
        
        # Operações estatísticas
        'percentile': np.percentile,  # Percentil
        'quantile': np.quantile,      # Quantil
        'cov': np.cov,                # Covariância
        'corrcoef': np.corrcoef,      # Coeficiente de correlação
        
        # Operações de agregação
        'prod': np.prod,          # Produto dos elementos
        'cumsum': np.cumsum,      # Soma acumulativa
        'cumprod': np.cumprod,    # Produto acumulativo
        
        # Funções trigonométricas
        'sin': np.sin,            # Seno
        'cos': np.cos,            # Cosseno
        'tan': np.tan,            # Tangente
        'arcsin': np.arcsin,      # Arco seno
        'arccos': np.arccos,      # Arco cosseno
        'arctan': np.arctan,      # Arco tangente
        
        # Funções exponenciais e logarítmicas
        'exp': np.exp,            # Exponencial
        'log': np.log,            # Logaritmo natural
        'log10': np.log10,        # Logaritmo base 10
        'log2': np.log2,          # Logaritmo base 2
        'sqrt': np.sqrt,          # Raiz quadrada
        
        # Funções de arredondamento
        'round': np.round,        # Arredondamento
        'floor': np.floor,        # Arredondamento para baixo
        'ceil': np.ceil,          # Arredondamento para cima
        'trunc': np.trunc,        # Truncamento
        
        # Funções lógicas
        'all': np.all,            # Verifica se todos são verdadeiros
        'any': np.any,            # Verifica se algum é verdadeiro
        
        # Manipulação de arrays
        'concatenate': np.concatenate,  # Concatenar arrays
        'stack': np.stack,              # Empilhar arrays
        'vstack': np.vstack,            # Empilhar verticalmente
        'hstack': np.hstack,            # Empilhar horizontalmente
        'reshape': np.reshape,          # Remodelar arrays
        'transpose': np.transpose,      # Transpor arrays
        
        # Operações condicionais
        'where': np.where,        # Operador condicional
        'select': np.select,      # Seleção condicional
        
        # Outras funções úteis
        'unique': np.unique,      # Valores únicos
        'diff': np.diff,          # Diferenças entre elementos adjacentes
        'gradient': np.gradient,  # Gradiente
        'clip': np.clip,          # Recortar valores
        'absolute': np.absolute,  # Valor absoluto (alias: np.abs)
        'abs': np.abs,            # Valor absoluto
    }
    
    logger.debug(f"Configured {len(numpy_functions)} safe builtin functions")

    # Funções que permaneceriam inalteradas:
    default_functions = {
        'bin': bin,          # Representação binária
        'bool': bool,        # Conversão para booleano
        'bytearray': bytearray,  # Criar bytearray
        'bytes': bytes,      # Criar bytes
        'chr': chr,          # Converter inteiro para caractere Unicode
        'complex': complex,  # Criar número complexo
        'dict': dict,        # Criar dicionário
        'divmod': divmod,    # Divisão e módulo
        'enumerate': enumerate,  # Enumerar sequência
        'filter': filter,    # Filtrar sequência
        'float': float,      # Conversão para ponto flutuante
        'format': format,    # Formatação de string
        'frozenset': frozenset,  # Criar frozenset
        'hash': hash,        # Calcular hash
        'hex': hex,          # Representação hexadecimal
        'id': id,            # Identificador único
        'int': int,          # Conversão para inteiro
        'isinstance': isinstance,  # Verificar tipo
        'issubclass': issubclass,  # Verificar herança
        'len': len,          # Tamanho da sequência
        'list': list,        # Criar lista
        'map': map,          # Mapear função
        'oct': oct,          # Representação octal
        'ord': ord,          # Converter caractere para inteiro
        'pow': pow,          # Potenciação (embora np.power seja uma alternativa)
        'range': range,      # Gerar sequência
        'reversed': reversed,  # Inverter sequência
        'set': set,          # Criar conjunto
        'slice': slice,      # Criar objeto slice
        'sorted': sorted,    # Ordenar
        'str': str,          # Conversão para string
        'tuple': tuple,      # Criar tupla
        'type': type,        # Obter tipo
        'zip': zip,          # Combinar sequências
        'True': True,        # Constante booleana
        'False': False,      # Constante booleana
        'None': None,        # Constante nula
    }

    logger.debug(f"Configured {len(default_functions)} safe builtin functions")
       
    # Combine all functions
    all_symbols = {}
    all_symbols.update(numpy_functions)
    all_symbols.update(default_functions)
    
    logger.debug(f"Total available symbols in interpreter: {len(all_symbols)}")
    
    # Define which AST nodes should be blocked for security
    blocked_nodes = ['Import', 'ImportFrom', 'Exec', 'Eval', 
                    'Attribute', 'Call', 'ClassDef', 'FunctionDef',
                    'Delete', 'Assert', 'Raise', 'Try', 'TryExcept',
                    'TryFinally', 'With', 'AsyncFunctionDef', 'AsyncWith',
                    'Global', 'Nonlocal']
    
    logger.debug(f"Base blocked nodes: {len(blocked_nodes)}")
    
    # If in readonly mode, block more nodes for extra safety
    if readonly:
        blocked_nodes.extend(['Assign', 'AugAssign', 'AnnAssign'])
        logger.debug(f"Added assignment nodes to blocked list in readonly mode")
    
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
    
    logger.info(f"Created asteval interpreter: numpy={use_numpy}, max_time={max_time}s, readonly={readonly}, {len(all_symbols)} symbols available")
    
    return interpreter

def evaluate_formula(formula, variables=None, use_numpy=True, max_time=5.0):
    """
    Evaluate a formula string using asteval with the provided variables.

    This function creates a secure evaluation environment, populates it with
    the provided variables, and evaluates the given formula with comprehensive
    error handling and logging.

    Args:
        formula (str): Formula string to evaluate
        variables (dict): Dictionary of variables to use in evaluation
        use_numpy (bool): Whether to include NumPy functions
        max_time (float): Maximum execution time in seconds

    Returns:
        Any: Result of formula evaluation, or None if evaluation fails
    """
    logger.info(f"Evaluating formula: '{formula}'")
    
    # Create interpreter
    interpreter = create_interpreter(use_numpy=use_numpy, max_time=max_time)
    logger.debug("Interpreter created successfully")

    # Add variables to interpreter's symbol table
    if variables:
        for name, value in variables.items():
            interpreter.symtable[name] = value

    # Evaluate the formula
    try:
        logger.debug(f"Starting formula evaluation: '{formula}'")
        result = interpreter.eval(formula)
        logger.debug("Formula evaluation completed")

        # Check for errors in the interpreter
        if len(interpreter.error) > 0:
            error_msg = interpreter.error[0].get_error()
            logger.error(f"Error evaluating formula '{formula}': {error_msg}")
            return None

        # Log the result
        if isinstance(result, (list, np.ndarray)) and len(str(result)) > 100:
            logger.info(f"Result type: {type(result).__name__}, shape/length: {getattr(result, 'shape', len(result) if hasattr(result, '__len__') else 'N/A')}")
        else:
            logger.info(f"Result: {result} (type: {type(result).__name__})")

        return result
    except Exception as e:
        logger.error(f"Exception evaluating formula '{formula}': {str(e)}", exc_info=True)
        return None

def find_vars_position(formula_str):
    """
    Find positions of variable patterns in a formula string.
    
    Identifies all occurrences of variables matching the pattern 'eXXXXXv'
    where XXXXX is a 5-digit number.
    
    Args:
        formula_str (str): The formula string to search in
        
    Returns:
        list: List of tuples (start_index, end_index, matched_text)
    """
    logger.debug(f"Finding variable positions in formula: '{formula_str}'")
    pattern = r'e\d{5}v'
    matches = re.finditer(pattern, formula_str)
    
    positions = [(match.start(), match.end(), match.group()) for match in matches]
    logger.debug(f"Found {len(positions)} variables in formula")
    return positions

def get_formula(formulas, path):
    """
    Find a formula by its path in the formulas collection.
    
    Args:
        formulas (list): List of formula collections
        path (str): Path identifier of the formula to find
        
    Returns:
        dict: The formula object if found, None otherwise
    """
    logger.debug(f"Searching for formula with path: {path}")
    
    for f0 in formulas:
        for f1 in f0["formulas"]:
            if f1["path"] == path:
                logger.debug(f"Found formula: {f1['path']}")
                return f1
                
    logger.warning(f"Formula with path {path} not found")
    return None

def get_aggr(formula, base):
    """
    Get aggregation information for a base variable from a formula.
    
    Args:
        formula (dict): The formula object
        base (str): Base identifier of the aggregation
        
    Returns:
        dict: Aggregation information if found, None otherwise
    """
    logger.debug(f"Searching for aggregation with base: {base}")
    
    if "parsed" not in formula or "aggr" not in formula["parsed"]:
        logger.warning(f"No parsed aggregations found in formula")
        return None
        
    for aggr in formula["parsed"]["aggr"]:
        if aggr["base"] == base:
            logger.debug(f"Found aggregation: {aggr}")
            return aggr
            
    logger.warning(f"Aggregation with base {base} not found")
    return None

def eval_formula(entities_eval, formulas):
    """
    Evaluate formulas for multiple entities with their associated data.
    
    This function processes a collection of entities, evaluates their formulas
    by substituting variables with values, and returns the evaluation results.
    It handles both regular variables and aggregation functions.
    
    Args:
        entities_eval (list): List of entities with formula data
        formulas (list): Collection of formula definitions
        
    Returns:
        list: Results of formula evaluations for each entity
    """
    log_info("=" * 80)
    log_info(f"STARTING BATCH FORMULA EVALUATION")
    log_info("=" * 80)
    results = []
    counter = 0

    for entity_idx, entity in enumerate(entities_eval):
        log_info(f"ENTITY [{entity_idx+1}/{len(entities_eval)}] - ID: {entity.get('id', f'entity_{entity_idx}')}")
        log_info("-" * 60)
        entity_results = {"entity_id": entity.get("id", f"entity_{entity_idx}"), "formula_results": []}
        
        if "formula_data" not in entity or "formulas" not in entity["formula_data"]:
            log_warning(f"⚠ Entity {entity_idx} has no formula data - SKIPPING", indent=1)
            continue
            
        for id_eval in entity["formula_data"]["formulas"]:
            log_info(f"FORMULA: {id_eval['formula']}", indent=0)
            log_info("." * 40, indent=0)
            
            # Create a fresh interpreter for each formula evaluation
            aeval = create_interpreter(use_numpy=True, max_time=5.0, readonly=False)
            
            # Get the formula
            formula = get_formula(formulas, id_eval["formula"])
            if not formula:
                log_error(f"✗ FORMULA NOT FOUND: {id_eval['formula']}", indent=1)
                continue
                
            formula_str = formula["value"]
    
            log_info(f"Expression: '{formula_str}'", indent=1)
            
            # Track variable replacements for debugging
            var_replacements = {}
            
            # First process aggregation functions
            if "data" not in id_eval:
                log_warning(f"⚠ NO DATA for formula: {id_eval['formula']}", indent=1)
                continue
            
            # Process aggregation variables first
            for i, value in enumerate(id_eval["data"]):
                if "aggr" in value:
                    log_info(f"→ Processing AGGREGATION variable", indent=2)
                    log_debug(f"Base: {value['aggr']['base'] if 'base' in value['aggr'] else 'N/A'}", indent=3)
                    
                    # Get the aggregation function
                    aggr = get_aggr(formula, value["aggr"]["base"])
                    if not aggr:
                        log_warning(f"Aggregation not found for base: {value['aggr']['base']}", indent=3)
                        continue
                        
                    # Process each variable in the aggregation
                    for v in aggr["vars"]:
                        counter += 1
                        new_var = f"{v}_{counter}"
                        old_formula = formula_str
                        formula_str = formula_str.replace(aggr["base"], aggr["eval"].replace(v, new_var))
                        
                        if old_formula != formula_str:
                            log_info(f"Replaced: {aggr['base']} → {new_var}", indent=3)
                            var_replacements[aggr["base"]] = aggr["eval"].replace(v, new_var)
                        
                        # Add the variable to the interpreter
                        aggregation_var = value["aggr"]["vars"]
                        if "values" in aggregation_var and len(aggregation_var["values"]) > 0:
                            aeval.symtable[new_var] = np.array(aggregation_var["values"])
                            log_info(f"Added: {new_var} = array[{len(aggregation_var['values'])} values]", indent=3)
                            log_debug(f"Values: {aggregation_var['values']}")
                        else:
                            log_warning(f"No values found for aggregation variable {v}", indent=3)
                            aeval.symtable[new_var] = np.array([0])  # Default value

            # Process other (non-aggregation) variables
            for i, value in enumerate(id_eval["data"]):
                if "non_aggr" in value:
                    log_info(f"→ Processing REGULAR variable", indent=2)
                    log_debug(f"Path: {value['non_aggr']['path']}", indent=3)
                    
                    counter += 1
                    pattern = r'e\d{5}v'
                    matches = re.search(pattern, value["non_aggr"]["path"])
                    
                    if not matches:
                        log_warning(f"No variable pattern found in path: {value['non_aggr']['path']}", indent=3)
                        continue
                        
                    var = matches.group()
                    new_var = f"{var}_{counter}"
                    old_formula = formula_str
                    formula_str = formula_str.replace(var, new_var)
                    
                    if old_formula != formula_str:
                        var_replacements[var] = new_var
                    
                    # Add the variable to the interpreter
                    if "values" in value["non_aggr"]:
                        aeval.symtable[new_var] = value["non_aggr"]["values"][0]
                        log_info(f"Added: {new_var}", indent=3)
                                               
                    else:
                        log_warning(f"No values found for non-aggregation variable {var}", indent=3)
                        aeval.symtable[new_var] = 0  # Empty array

            # Log all variable replacements
            log_info(f"Final expression: '{formula_str}'", indent=2)
            if var_replacements:
                for old, new in var_replacements.items():
                    log_info(f"{old} → {new}", indent=3)
            
            # Execute the formula
            try:
                log_info(">>> EXECUTING FORMULA <<<", indent=1)
                log_info(f"Path: {id_eval['formula']}", indent=2)
                log_info(f"Expression: '{formula_str}'", indent=2)
                
                # Regular expression without assignment
                result = aeval(formula_str)
                
                # Check for errors
                if result is None or (hasattr(aeval, 'error') and aeval.error):
                    if hasattr(aeval, 'error') and aeval.error:
                        error_msg = str(aeval.error[0])
                        error_details = str(aeval.error[1]) if len(aeval.error) > 1 else ""
                    else:
                        error_msg = "Unknown error"
                        error_details = ""
                    
                    log_error(f"✗ ERROR - Formula: {id_eval['formula']}", indent=1)
                    log_error(f"Expression: '{formula_str}'", indent=2)
                    log_error(f"Error: {error_msg}", indent=2)
                    if error_details:
                        log_error(f"Details: {error_details}", indent=2)
                    
                    # Debug: print available symbols
                    log_debug(f"Available symbols: {list(aeval.symtable.keys())}", indent=2)
                    entity_results["formula_results"].append({
                        "formula_path": id_eval["formula"],
                        "status": "error",
                        "error": error_msg
                    })
                    continue
                
                # Log and store successful result
                if isinstance(result, np.ndarray):
                    log_info(f"✓ SUCCESS - Formula: {id_eval['formula']}", indent=1)
                    log_info(f"Result type: numpy.ndarray", indent=2)
                    log_info(f"Shape: {result.shape}", indent=2)
                    log_info(f"Sample values (first 5): {result.flatten()[:5].tolist() if result.size > 0 else []}", indent=2)
                else:
                    log_info(f"✓ SUCCESS - Formula: {id_eval['formula']}", indent=1)
                    log_info(f"Result: {result}", indent=2)

                entity_results["formula_results"].append({
                    "formula_path": id_eval["formula"],
                    "status": "success",
                    "update": formula["update"],
                    "result": result.tolist() if isinstance(result, np.ndarray) else result,
                })
                
            except Exception as e:
                log_error(f"✗ EXCEPTION - Formula: {id_eval['formula']}", indent=1)
                log_error(f"Expression: '{formula_str}'", indent=2)
                log_error(f"Exception: {str(e)}", indent=2)
                entity_results["formula_results"].append({
                    "formula_path": id_eval["formula"],
                    "status": "error",
                    "update": formula["update"],
                    "error": str(e)
                })
        
        results.append(entity_results)

    log_info("=" * 80)
    log_info(f"BATCH EVALUATION COMPLETED")
    log_info(f"Total entities processed: {len(results)}")
    log_info("=" * 80)
    return results

if __name__ == "__main__":
    """
    Main entry point for formula evaluation when script is run directly.
    
    Loads formula and entity data from JSON files and evaluates formulas.
    """
    logger.info("Starting formula evaluation from main")

    # Get the current directory for file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.debug(f"Current directory: {current_dir}")

    # Paths for input and output files
    formulas_json = "extracted_formulas.json"
    entities_eval_json = "processed_formulas_with_variables.json"
    engine_result_json = "engine_result.json"
    
    logger.info(f"Loading formula definitions from: {formulas_json}")
    logger.info(f"Loading entity data from: {entities_eval_json}")

    try:
        with open(formulas_json, 'r', encoding='utf-8') as f:
            logger.debug(f"Reading formulas file: {formulas_json}")
            formulas = json.load(f)
            logger.info(f"Loaded {len(formulas)} formula collections")
    except Exception as e:
        logger.error(f"Error loading formulas file: {str(e)}", exc_info=True)
        formulas = []

    try:
        with open(entities_eval_json, 'r', encoding='utf-8') as f:
            logger.debug(f"Reading entities evaluation file: {entities_eval_json}")
            entities_eval = json.load(f)
            logger.info(f"Loaded {len(entities_eval)} entities for evaluation")
    except Exception as e:
        logger.error(f"Error loading entities evaluation file: {str(e)}", exc_info=True)
        entities_eval = []

    # Evaluate formulas
    if formulas and entities_eval:
        logger.info("Starting formula evaluation")
        results = eval_formula(entities_eval, formulas)
        
        # Print summary of results
        success_count = sum(1 for entity in results for fr in entity["formula_results"] if fr["status"] == "success")
        error_count = sum(1 for entity in results for fr in entity["formula_results"] if fr["status"] == "error")
        
        logger.info(f"Formula evaluation complete. Successful: {success_count}, Errors: {error_count}")
    else:
        logger.error("Cannot perform evaluation: missing formula definitions or entity data")

    # Convert numpy types to native Python types before saving
    results_converted = convert_numpy_types(results)
    
    with open(engine_result_json, 'w', encoding='utf-8') as f:
        json.dump(results_converted, f, indent=4, ensure_ascii=False)
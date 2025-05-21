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
        logger.debug(f"Adding {len(variables)} variables to interpreter")
        for name, value in variables.items():
            interpreter.symtable[name] = value
            if isinstance(value, list) and len(value) < 10:
                logger.debug(f"Variable {name} = {value}")
            elif isinstance(value, list):
                logger.debug(f"Variable {name} = list with {len(value)} items")
            elif isinstance(value, np.ndarray):
                logger.debug(f"Variable {name} = numpy.ndarray with shape {value.shape}")
            else:
                logger.debug(f"Variable {name} = {value} (type: {type(value).__name__})")

    # Print variable types for debugging
    if variables:
        var_types = {name: type(value).__name__ for name, value in variables.items() if name in formula}
        logger.debug(f"Variable types in formula: {var_types}")

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
    logger.info(f"Starting batch formula evaluation for {len(entities_eval)} entities")
    results = []
    counter = 0

    for entity_idx, entity in enumerate(entities_eval):
        logger.info(f"Processing entity {entity_idx+1}/{len(entities_eval)}")
        entity_results = {"entity_id": entity.get("id", f"entity_{entity_idx}"), "formula_results": []}
        
        if "formula_data" not in entity or "formulas" not in entity["formula_data"]:
            logger.warning(f"Entity {entity_idx} has no formula data, skipping")
            continue
            
        for id_eval in entity["formula_data"]["formulas"]:
            logger.debug(f"Processing formula path: {id_eval['formula']}")
            
            # Create a fresh interpreter for each formula evaluation
            aeval = create_interpreter(use_numpy=True, max_time=5.0, readonly=False)
            logger.debug("Created interpreter for formula evaluation")
            
            # Get the formula
            formula = get_formula(formulas, id_eval["formula"])
            if not formula:
                logger.error(f"Formula not found: {id_eval['formula']}")
                continue
                
            formula_str = formula["value"]
            logger.info(f"Evaluating formula: '{formula_str}'")
            
            # Track variable replacements for debugging
            var_replacements = {}
            
            # First process aggregation functions
            if "data" not in id_eval:
                logger.warning(f"No data found for formula: {id_eval['formula']}")
                continue
                
            logger.debug(f"Processing {len(id_eval['data'])} data items")
            
            # Process aggregation variables first
            for i, value in enumerate(id_eval["data"]):
                if "aggr" in value:
                    logger.debug(f"Processing aggregation: {value['aggr']}")
                    
                    # Get the aggregation function
                    aggr = get_aggr(formula, value["aggr"]["base"])
                    if not aggr:
                        logger.warning(f"Aggregation not found for base: {value['aggr']['base']}")
                        continue
                        
                    logger.debug(f"Found aggregation definition: {aggr}")
                    
                    # Process each variable in the aggregation
                    for v in aggr["vars"]:
                        counter += 1
                        new_var = f"{v}_{counter}"
                        old_formula = formula_str
                        formula_str = formula_str.replace(aggr["base"], aggr["eval"].replace(v, new_var))
                        
                        if old_formula != formula_str:
                            logger.debug(f"Replaced aggregation base '{aggr['base']}' with expression containing '{new_var}'")
                            var_replacements[aggr["base"]] = aggr["eval"].replace(v, new_var)
                        
                        # Add the variable to the interpreter
                        if "values" in value and len(value["values"]) > 0:
                            aeval.symtable[new_var] = np.array(value["values"])
                            logger.debug(f"Added variable {new_var} = {value['values'][0]}")
                        else:
                            logger.warning(f"No values found for aggregation variable {v}")
                            aeval.symtable[new_var] = np.array([0])  # Default value

            # Process other (non-aggregation) variables
            for i, value in enumerate(id_eval["data"]):
                if "non_aggr" in value:
                    logger.debug(f"Processing non-aggregation variable: {value['non_aggr']}")
                    
                    counter += 1
                    pattern = r'e\d{5}v'
                    matches = re.search(pattern, value["non_aggr"]["path"])
                    
                    if not matches:
                        logger.warning(f"No variable pattern found in path: {value['non_aggr']['path']}")
                        continue
                        
                    var = matches.group()
                    new_var = f"{var}_{counter}"
                    old_formula = formula_str
                    formula_str = formula_str.replace(var, new_var)
                    
                    if old_formula != formula_str:
                        logger.debug(f"Replaced variable '{var}' with '{new_var}'")
                        var_replacements[var] = new_var
                    
                    # Add the variable to the interpreter
                    if "values" in value["non_aggr"]:
                        aeval.symtable[new_var] = value["non_aggr"]["values"][0]
                        logger.debug(f"Added variable {new_var} = numpy.array with {len(value['non_aggr']['values'])} values")
                    else:
                        logger.warning(f"No values found for non-aggregation variable {var}")
                        aeval.symtable[new_var] = 0  # Empty array

            # Log all variable replacements
            logger.debug(f"Formula after variable substitution: '{formula_str}'")
            logger.debug(f"Variable replacements: {var_replacements}")
            
            # Execute the formula
            try:
                logger.info(f"Executing formula: '{formula_str}'")
                result = aeval(formula_str)
                
                # Check for errors
                if result is None or (hasattr(aeval, 'error') and aeval.error):
                    error_msg = str(aeval.error[0]) if hasattr(aeval, 'error') and aeval.error else "Unknown error"
                    logger.error(f"Error evaluating formula '{formula_str}': {error_msg}")
                    entity_results["formula_results"].append({
                        "formula_path": id_eval["formula"],
                        "status": "error",
                        "error": error_msg
                    })
                    continue
                
                # Log and store successful result
                if isinstance(result, np.ndarray):
                    logger.info(f"Formula result: numpy.ndarray with shape {result.shape}")
                else:
                    logger.info(f"Formula result: {result}")
                    
                entity_results["formula_results"].append({
                    "formula_path": id_eval["formula"],
                    "status": "success",
                    "result": result.tolist() if isinstance(result, np.ndarray) else result
                })
                
            except Exception as e:
                logger.error(f"Exception evaluating formula '{formula_str}': {str(e)}", exc_info=True)
                entity_results["formula_results"].append({
                    "formula_path": id_eval["formula"],
                    "status": "error",
                    "error": str(e)
                })
        
        results.append(entity_results)
        
    logger.info(f"Completed batch formula evaluation. Processed {len(results)} entities.")
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
    formulas_json = os.path.join(current_dir, "extracted_formulas.json")
    entities_eval_json = os.path.join(current_dir, "processed_formulas_with_variables.json")
    
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
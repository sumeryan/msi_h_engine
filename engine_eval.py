"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""
from ast import expr
import numpy as np
import re
import log
import os
import json
from engine_logger import EngineLogger
from asteval import Interpreter
from update_tree import UpdateTreeData
from update_frappe import UpdateFrappe

class EngineEval(EngineLogger):
    """
    EngineEval class for managing formula evaluation with asteval.
    
    This class provides methods to create an interpreter, evaluate formulas,
    and handle variable substitutions in a secure manner.
    
    Attributes:
        use_numpy (bool): Whether to include NumPy functions in the interpreter.
        max_time (float): Maximum execution time for formula evaluation.
        readonly (bool): Whether to run in readonly mode (blocks assignment operations).
    """
    
    def __init__(self):
        self.logger = log.get_logger("Engine")

    def convert_numpy_types(self, obj):
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
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        return obj

    def create_interpreter(self, use_numpy=True, max_time=5.0, readonly=False):
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
        
        # Combine all functions
        all_symbols = {}
        all_symbols.update(numpy_functions)
        all_symbols.update(default_functions)
        
        # Define which AST nodes should be blocked for security
        blocked_nodes = ['Import', 'ImportFrom', 'Exec', 'Eval', 
                        'Attribute', 'Call', 'ClassDef', 'FunctionDef',
                        'Delete', 'Assert', 'Raise', 'Try', 'TryExcept',
                        'TryFinally', 'With', 'AsyncFunctionDef', 'AsyncWith',
                        'Global', 'Nonlocal']
        
        # If in readonly mode, block more nodes for extra safety
        if readonly:
            blocked_nodes.extend(['Assign', 'AugAssign', 'AnnAssign'])
            self.log_debug(f"Added assignment nodes to blocked list in readonly mode")
        
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
        
        # logger.info(f"Created asteval interpreter: numpy={use_numpy}, max_time={max_time}s, readonly={readonly}, {len(all_symbols)} symbols available")
        
        return interpreter

    def evaluate_formula(self, formula, variables=None, use_numpy=True, max_time=5.0):
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
        self.log_info(f"Evaluating formula: '{formula}'")
        
        # Create interpreter
        interpreter = self.create_interpreter(use_numpy=use_numpy, max_time=max_time)
        self.log_debug("Interpreter created successfully")

        # Add variables to interpreter's symbol table
        if variables:
            for name, value in variables.items():
                interpreter.symtable[name] = value

        # Evaluate the formula
        try:
            self.log_debug(f"Starting formula evaluation: '{formula}'")
            result = interpreter.eval(formula)
            self.log_debug("Formula evaluation completed")

            # Check for errors in the interpreter
            if len(interpreter.error) > 0:
                error_msg = interpreter.error[0].get_error()
                self.log_error(f"Error evaluating formula '{formula}': {error_msg}")
                return None

            # Log the result
            if isinstance(result, (list, np.ndarray)) and len(str(result)) > 100:
                self.log_info(f"Result type: {type(result).__name__}, shape/length: {getattr(result, 'shape', len(result) if hasattr(result, '__len__') else 'N/A')}")
            else:
                self.log_info(f"Result: {result} (type: {type(result).__name__})")

            return result
        except Exception as e:
            self.log_error(f"Exception evaluating formula '{formula}': {str(e)}", exc_info=True)
            return None

    def find_vars_position(self, formula_str):
        """
        Find positions of variable patterns in a formula string.
        
        Identifies all occurrences of variables matching the pattern 'eXXXXXv'
        where XXXXX is a 5-digit number.
        
        Args:
            formula_str (str): The formula string to search in
            
        Returns:
            list: List of tuples (start_index, end_index, matched_text)
        """
        self.log_debug(f"Finding variable positions in formula: '{formula_str}'")
        pattern = r'e\d{5}v'
        matches = re.finditer(pattern, formula_str)
        
        positions = [(match.start(), match.end(), match.group()) for match in matches]
        self.log_debug(f"Found {len(positions)} variables in formula")
        return positions

    def get_formula(self, formulas, path):
        """
        Find a formula by its path in the formulas collection.
        
        Args:
            formulas (list): List of formula collections
            path (str): Path identifier of the formula to find
            
        Returns:
            dict: The formula object if found, None otherwise
        """
        
        for f0 in formulas:
            for f1 in f0["formulas"]:
                if f1["path"] == path:
                    self.log_debug(f"Found: {f1['path']}")
                    return f1
                    
        self.log_warning(f"Formula with path {path} not found")
        return None

    def get_aggr(self, formula, base):
        """
        Get aggregation information for a base variable from a formula.
        
        Args:
            formula (dict): The formula object
            base (str): Base identifier of the aggregation
            
        Returns:
            dict: Aggregation information if found, None otherwise
        """
        
        if "parsed" not in formula or "aggr" not in formula["parsed"]:
            self.log_warning(f"No parsed aggregations found in formula")
            return None
            
        for aggr in formula["parsed"]["aggr"]:
            if aggr["base"] == base:
                self.log_debug(f"Found aggregation: {base}", indent=1)
                return aggr
                
        self.log_warning(f"Aggregation with base {base} not found")
        return None

    def simple_reference_substitution(self, formula, references):
        """
        Substitutes references (e.g., e00002v, e00002v_4) with their corresponding values in the formula.
        
        Args:
            formula (str): The Python formula containing coded references
            references (dict): Dictionary with references and their values
        
        Returns:
            str: The formula with references replaced
        """
        # Find all references in the formula (like e00002v or e00002v_4)
        pattern = re.compile(r'e\d{5}v(?:_\d+)?')
        found_references = pattern.findall(formula)
        
        # For each reference found, substitute with the corresponding value
        processed_str = formula
        
        for ref in found_references:
            # Extract the base key (for example, e00002v from e00002v_4)
            base_key = ref.split('_')[0]
            
            # Check if the key exists in the references dictionary
            if base_key in references:
                # Replace the reference with the value
                # Here we'll replace with a temporary placeholder to avoid affecting subsequent substitutions
                value = str(references[base_key])
                processed_str = re.sub(rf'\b{re.escape(ref)}\b', value, processed_str)
    
        return processed_str        

    def eval_formula(self, entities_eval, formulas, data_tree):
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
        self.log_info(f"Starting batch evaluation of formulas")
        
        results = []
        counter = 0

        references = data_tree.get("referencia", {})[0]

        for entity_idx, entity in enumerate(entities_eval):
            self.log_info("=" * 80)
            self.log_info(f"Entity [{entity_idx+1}/{len(entities_eval)}] - Id: {entity.get('id', f'entity_{entity_idx}')}")
            self.log_info("=" * 80)
            entity_results = {"id": entity.get("id", f"entity_{entity_idx}"), "results": []}
            
            if "formula_data" not in entity or "formulas" not in entity["formula_data"]:
                self.log_warning(f"Entity {entity_idx} has no formula data - Skipping")
                continue
                
            for id_eval in entity["formula_data"]["formulas"]:
    
                print("\n")
                print("\n")
                self.log_info(f"Evaluating formula: {id_eval['formula']}", indent=1)
                self.log_info("." * 80, indent=0)
                
                # Create a fresh interpreter for each formula evaluation
                aeval = self.create_interpreter(use_numpy=True, max_time=5.0, readonly=False)

                # Load data tree into the interpreter's symbol table
                aeval.symtable["data_tree"] = data_tree
                
                # Get the formula
                formula = self.get_formula(formulas, id_eval["formula"])
                if not formula:
                    self.log_error(f"Formula not found: {id_eval['formula']}", indent=1)
                    continue
                    
                formula_str = formula["value"].replace("return ", "")
                formula_str += "\n"  # Ensure the formula ends with a newline
                self.log_info(f"Id:{entity.get('id')}")

                # Track variable replacements for debugging
                var_replacements = {}
                
                # First process aggregation functions
                if "data" not in id_eval:
                    self.log_warning(f"No data for formula: {id_eval['formula']}", indent=1)
                    continue

                print("\n")
                
                # Process aggregation variables first
                for i, value in enumerate(id_eval["data"]):
                    if "aggr" in value:
                        
                        # Get the aggregation function
                        aggr = self.get_aggr(formula, value["aggr"]["base"])
                        if not aggr:
                            self.log_warning(f"Aggregation not found for base: {value['aggr']['base']}", indent=3)
                            continue
                            
                        # Process each variable in the aggregation
                        for v in aggr["vars"]:
                            counter += 1
                            new_var = f"{v}_{counter}"
                            old_formula = formula_str
                            formula_str = formula_str.replace(aggr["base"], aggr["eval"].replace(v, new_var))
                            
                            if old_formula != formula_str:
                                self.log_info(f"Replaced: {aggr['base']} → {new_var}", indent=3)
                                var_replacements[aggr["base"]] = aggr["eval"].replace(v, new_var)
                            
                            # Add the variable to the interpreter
                            aggregation_var = value["aggr"]["vars"]
                            if "values" in aggregation_var and len(aggregation_var["values"]) > 0:
                                if aggregation_var["values"][0] is None:
                                    self.log_warning(f"None value, using 0.0")
                                    aeval.symtable[new_var] = np.array([0.0])
                                else:
                                    aeval.symtable[new_var] = np.array(aggregation_var["values"])
                                self.log_info(f"Added: {new_var} = array[{len(aggregation_var['values'])} values]", indent=3)
                                self.log_debug(f"Values: {aggregation_var['values']}")
                            else:
                                self.log_warning(f"No values, using: 0.0")
                                aeval.symtable[new_var] = np.array([0.0])  # Default value
                            
                            print("\n")

                # Process other (non-aggregation) variables
                for i, value in enumerate(id_eval["data"]):
                    if "non_aggr" in value:
                        self.log_debug(f"Path: {value['non_aggr']['path']}", indent=3)
                        
                        counter += 1
                        pattern = r'e\d{5}v'
                        matches = re.search(pattern, value["non_aggr"]["path"])
                        
                        if not matches:
                            self.log_warning(f"No variable pattern found in path: {value['non_aggr']['path']}", indent=3)
                            continue
                            
                        var = matches.group()
                        new_var = f"{var}_{counter}"
                        old_formula = formula_str
                        formula_str = formula_str.replace(var, new_var)
                        
                        if old_formula != formula_str:
                            var_replacements[var] = new_var
                        
                        # Add the variable to the interpreter
                        if "values" in value["non_aggr"]:
                            if value["non_aggr"]["values"][0] is None:
                                self.log_warning(f"None value, using 0.0")
                                aeval.symtable[new_var] =  0.0
                            else:
                                aeval.symtable[new_var] = value["non_aggr"]["values"][0]
                            self.log_info(f"Added: {new_var}", indent=3)
                            self.log_debug(f"Value: {value['non_aggr']['values'][0]}")                        
                        else:
                            self.log_warning(f"No values, using: 0.0")
                            aeval.symtable[new_var] = 0.0  # Empty array

                        print("\n")

                # print(aeval.symtable)

                # Execute the formula
                try:
                    self.log_info("Executing formula")
                    self.log_info(f"Expression:", indent=1)
                    print("\n")
                    print(formula_str)
                    print("\n")
                    print(self.simple_reference_substitution(formula_str, references))
                    print("\n")
                    
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
                        
                        self.log_error(f"ERROR - Formula: {id_eval['formula']}", indent=1)
                        self.log_error(f"Expression: '{formula_str}'", indent=2)
                        self.log_error(f"Error: {error_msg}", indent=2)
                        if error_details:
                            self.log_error(f"Details: {error_details}", indent=2)
                        
                        # Debug: print available symbols
                        self.log_debug(f"Available symbols: {list(aeval.symtable.keys())}", indent=2)
                        entity_results["results"].append({
                            "path":  self.simple_reference_substitution(id_eval["formula"], references),
                            "status": "error",
                            "error": error_msg
                        })
                        continue
                    
                    # Log and store successful result
                    if isinstance(result, np.ndarray):
                        self.log_info(f"Success - Formula: {id_eval['formula']}", indent=1)
                        self.log_info(f"Result type: numpy.ndarray", indent=2)
                        self.log_info(f"Shape: {result.shape}", indent=2)
                        self.log_info(f"Sample values (first 5): {result.flatten()[:5].tolist() if result.size > 0 else []}", indent=2)
                        self.log_info(f"Result: {result.tolist()}")
                    else:
                        self.log_info(f"Success - Formula: {id_eval['formula']}", indent=1)
                        self.log_info(f"Result: {result}", indent=2)

                    entity_results["results"].append({
                        "path": id_eval["formula"],
                        "status": "success",
                        "result": result.tolist() if isinstance(result, np.ndarray) else result,
                    })
                    
                except Exception as e:
                    self.log_error(f"EXCEPTION - Formula: {id_eval['formula']}", indent=1)
                    self.log_error(f"Expression: '{formula_str}'", indent=2)
                    self.log_error(f"Exception: {str(e)}", indent=2)
                    entity_results["results"].append({
                        "path": self.simple_reference_substitution(id_eval["formula"], references),
                        "status": "error",
                        "error": str(e)
                    })
            
            results.append(entity_results)

        self.log_info("=" * 80)
        self.log_info(f"BATCH EVALUATION COMPLETED")
        self.log_info(f"Total entities processed: {len(results)}")
        self.log_info("=" * 80)
        return results

if __name__ == "__main__":
    """
    Main entry point for formula evaluation when script is run directly.
    
    Loads formula and entity data from JSON files and evaluates formulas.
    """

    engine = EngineEval()

    engine.log_info("Starting formula evaluation from main")

    # Load tree data
    tree_data_path = "tree_data.json"
    with open(tree_data_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    # Get the current directory for file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    engine.log_debug(f"Current directory: {current_dir}")

    # Paths for input and output files
    formulas_json = "extracted_formulas.json"
    entities_eval_json = "processed_formulas_with_variables.json"
    engine_result_json = "engine_result.json"
    
    engine.log_info(f"Loading formula definitions from: {formulas_json}")
    engine.log_info(f"Loading entity data from: {entities_eval_json}")

    try:
        with open(formulas_json, 'r', encoding='utf-8') as f:
            engine.log_debug(f"Reading formulas file: {formulas_json}")
            formulas = json.load(f)
            engine.log_info(f"Loaded {len(formulas)} formula collections")
    except Exception as e:
        engine.log_error(f"Error loading formulas file: {str(e)}")
        formulas = []

    try:
        with open(entities_eval_json, 'r', encoding='utf-8') as f:
            engine.log_debug(f"Reading entities evaluation file: {entities_eval_json}")
            entities_eval = json.load(f)
            engine.log_info(f"Loaded {len(entities_eval)} entities for evaluation")
    except Exception as e:
        engine.log_error(f"Error loading entities evaluation file: {str(e)}")
        entities_eval = []

    # Evaluate formulas
    if formulas and entities_eval:
        engine.log_info("Starting formula evaluation")
        results = engine.eval_formula(entities_eval, formulas)
        
        # Print summary of results
        success_count = sum(1 for entity in results for fr in entity["results"] if fr["status"] == "success")
        error_count = sum(1 for entity in results for fr in entity["results"] if fr["status"] == "error")
        
        engine.log_info(f"Formula evaluation complete. Successful: {success_count}, Errors: {error_count}")
    else:
        engine.log_error("Cannot perform evaluation: missing formula definitions or entity data")

    # Convert numpy types to native Python types before saving
    results_converted = engine.convert_numpy_types(results)

    with open(engine_result_json, 'w', encoding='utf-8') as f:
        json.dump(results_converted, f, indent=4, ensure_ascii=False)

    # Update tree_data and database
    update_tree = UpdateTreeData(tree_data, formulas[0], results_converted)
    tree_data = update_tree.update_tree()
    

    update_frappe = UpdateFrappe(results_converted, formulas[0])
    update_frappe.update()

    with open("tree_data_updated.json", 'w', encoding='utf-8') as f:
        json.dump(tree_data, f, indent=4, ensure_ascii=False)
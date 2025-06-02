import re
from typing import List, Dict, Tuple, Optional

class FilterVariableExtractor:
    """
    A class to extract variables in the format e00000v that appear 
    to the right of comparison operators in expressions.
    """
    
    def __init__(self, variable_pattern: str = r'[eE]\d{5}[vV]'):
        """
        Initialize the VariableExtractor with a specific variable pattern.
        
        Args:
            variable_pattern: Regular expression pattern for variables to extract.
                              Default is e followed by 5 digits followed by v (case insensitive).
        """
        self.variable_pattern = variable_pattern
        # Pattern to match comparison operators followed by the variable pattern
        self.comparison_pattern = r'(?:[=!<>]=?|<|>)\s*(' + variable_pattern + r')'
    
    def extract_variables(self, expression: str) -> List[Dict[str, any]]:
        """
        Extract variables to the right of comparison operators from an expression.
        
        Args:
            expression: The string expression to analyze.
            
        Returns:
            A list of dictionaries containing variable information:
            - variable: The matched variable text
            - start_pos: Starting position in the expression
            - end_pos: Ending position in the expression
        """
        results = []
        
        for match in re.finditer(self.comparison_pattern, expression):
            # Group 1 contains the captured variable
            variable = match.group(1)
            
            # Get the start and end positions of the variable (not the operator)
            start_pos = match.start(1)
            end_pos = match.end(1)
            
            results.append({
                'variable': variable,
                'start_pos': start_pos,
                'end_pos': end_pos,
            })
            
        return results
    
    def extract_unique_variables(self, expression: str) -> List[str]:
        """
        Extract unique variable names to the right of comparison operators.
        
        Args:
            expression: The string expression to analyze.
            
        Returns:
            A list of unique variable names.
        """
        matches = self.extract_variables(expression)
        unique_vars = list(set(match['variable'] for match in matches))
        return unique_vars
    
    def process_multiple_expressions(self, expressions: List[str]) -> Dict[int, List[Dict[str, any]]]:
        """
        Process multiple expressions and extract variables from each.
        
        Args:
            expressions: A list of string expressions to analyze.
            
        Returns:
            A dictionary mapping expression indices to lists of variable information.
        """
        results = {}
        
        for i, expression in enumerate(expressions):
            results[i] = self.extract_variables(expression)
            
        return results
    
    def find_variable_positions(self, text: str, variable: str) -> List[Tuple[int, int]]:
        """
        Find all positions of a specific variable in text.
        
        Args:
            text: The text to search in.
            variable: The variable to search for.
            
        Returns:
            A list of tuples with (start_position, end_position).
        """
        positions = []
        pattern = r'(?:[=!<>]=?|<|>)\s*(' + re.escape(variable) + r')'
        
        for match in re.finditer(pattern, text):
            positions.append((match.start(1), match.end(1)))
            
        return positions

    def highlight_variables(self, expression: str, 
                            prefix: str = '[[', suffix: str = ']]') -> str:
        """
        Create a highlighted version of the expression with matched variables marked.
        
        Args:
            expression: The expression to highlight.
            prefix: The string to insert before each variable.
            suffix: The string to insert after each variable.
            
        Returns:
            A string with variables highlighted.
        """
        # Extract variables with their positions
        variables = self.extract_variables(expression)
        
        # Sort by start position in reverse order to avoid shifting positions
        variables.sort(key=lambda x: x['start_pos'], reverse=True)
        
        # Create a mutable list of characters
        chars = list(expression)
        
        # Insert markers
        for var_info in variables:
            chars.insert(var_info['end_pos'], suffix)
            chars.insert(var_info['start_pos'], prefix)
            
        # Join back to a string
        return ''.join(chars)
    

# Example usage
if __name__ == "__main__":
    # Create an instance of the extractor
    extractor = FilterVariableExtractor()
    
    # Sample expressions
    expressions = [
        "e00040v == e00028v",
        "e00040v == e00028v and e00028v == 'Não' and e00027v>10",
        "e00028v == 'Não' and e00040v < e00028v",
        "e00028v == 'Não' and (e00040v != e00028v or Ex. e00050v == 100)",
        "e00028v == 'Não' and (e00040v == 100 or Ex. e00050v == 100) and e00028v >= e00055v"
    ]
    
    # Process a single expression
    print("Variables in the first expression:")
    vars_exp1 = extractor.extract_variables(expressions[0])
    for var_info in vars_exp1:
        print(f"Variable: {var_info['variable']}, Position: {var_info['start_pos']}-{var_info['end_pos']}")
    
    # Get unique variables from an expression
    print("\nUnique variables in the second expression:")
    unique_vars = extractor.extract_unique_variables(expressions[1])
    print(unique_vars)
    
    # Process multiple expressions
    print("\nProcessing multiple expressions:")
    results = extractor.process_multiple_expressions(expressions)
    for exp_idx, vars_list in results.items():
        print(f"Expression {exp_idx}: {expressions[exp_idx]}")
        for var_info in vars_list:
            print(f"  Variable: {var_info['variable']}, Position: {var_info['start_pos']}-{var_info['end_pos']}")
    
    # Highlight variables in an expression
    print("\nHighlighted expression:")
    highlighted = extractor.highlight_variables(expressions[3])
    print(highlighted)
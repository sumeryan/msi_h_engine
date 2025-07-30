import json
from typing import Dict, List, Set
from collections import defaultdict


class FormulaExecutionClassifier:
    """
    Classifies formulas into execution groups based on DAG dependencies.
    
    Groups are determined dynamically based on dependency depth:
    - Group 1: Formulas with no internal dependencies (only depend on external inputs)
    - Group 2: Formulas that depend only on Group 1
    - Group 3: Formulas that depend on Groups 1-2
    - Group N: Formulas that depend on previous groups
    """
    
    def __init__(self, formulas_data: List[Dict]):
        self.formulas_data = formulas_data
        self.formula_paths: Set[str] = set()
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.execution_groups: Dict[str, int] = {}
        
        self._extract_formulas_and_dependencies()
    
    def _extract_formulas_and_dependencies(self):
        """Extracts all formulas and their dependencies from JSON."""
        for group in self.formulas_data:
            if 'formulas' in group:
                for formula in group['formulas']:
                    formula_path = formula['path']
                    self.formula_paths.add(formula_path)
                    
                    # Extract DAG dependencies
                    if 'parsed' in formula and 'dag_paths' in formula['parsed']:
                        for dep_path in formula['parsed']['dag_paths']:
                            # Only consider internal dependencies (calculated by other formulas)
                            if dep_path in self.formula_paths or self._is_calculated_formula(dep_path):
                                self.dependencies[formula_path].add(dep_path)
    
    def _is_calculated_formula(self, path: str) -> bool:
        """Checks if a path is calculated by some formula."""
        for group in self.formulas_data:
            if 'formulas' in group:
                for formula in group['formulas']:
                    if formula['path'] == path:
                        return True
        return False
    
    def _build_dependency_graph(self):
        """Rebuilds the dependency graph considering only calculated formulas."""
        self.dependencies.clear()
        
        for group in self.formulas_data:
            if 'formulas' in group:
                for formula in group['formulas']:
                    formula_path = formula['path']
                    
                    if 'parsed' in formula and 'dag_paths' in formula['parsed']:
                        for dep_path in formula['parsed']['dag_paths']:
                            # Only add if dependency is a calculated formula
                            if dep_path in self.formula_paths:
                                self.dependencies[formula_path].add(dep_path)
    
    def classify_execution_groups(self) -> Dict[str, int]:
        """
        Classifies formulas into execution groups using topological sorting.
        
        Returns:
            Dict mapping formula path to execution group (1-N)
        """
        self._build_dependency_graph()
        
        # Calculate in-degree (how many dependencies each formula has)
        in_degree = {path: 0 for path in self.formula_paths}
        
        for formula_path in self.formula_paths:
            in_degree[formula_path] = len(self.dependencies[formula_path])
        
        # Topological sorting by levels
        current_group = 1
        processed = set()
        
        while len(processed) < len(self.formula_paths):
            # Find formulas with no unprocessed dependencies
            current_level = []
            
            for path in self.formula_paths:
                if path not in processed:
                    # Check if all dependencies have been processed
                    deps_satisfied = all(
                        dep in processed or dep not in self.formula_paths 
                        for dep in self.dependencies[path]
                    )
                    
                    if deps_satisfied:
                        current_level.append(path)
            
            # If no formula found at current level, there's a cycle
            if not current_level:
                # Add remaining ones to the last group
                for path in self.formula_paths:
                    if path not in processed:
                        self.execution_groups[path] = current_group
                        processed.add(path)
                break
            
            # Assign current group to found formulas
            for path in current_level:
                self.execution_groups[path] = current_group
                processed.add(path)
            
            current_group += 1
        
        return self.execution_groups
    
    def get_execution_order(self) -> Dict[int, List[str]]:
        """
        Returns formulas grouped by execution order.
        
        Returns:
            Dict with groups (1-N) mapping to list of formula paths
        """
        if not self.execution_groups:
            self.classify_execution_groups()
        
        groups = defaultdict(list)
        for path, group in self.execution_groups.items():
            groups[group].append(path)
        
        return dict(groups)
    
    def print_execution_plan(self):
        """Prints the execution plan in a readable format."""
        execution_order = self.get_execution_order()
        
        print("=== FORMULA EXECUTION PLAN ===\n")
        
        for group_num in sorted(execution_order.keys()):
            formulas = execution_order[group_num]
            print(f"GROUP {group_num}: ({len(formulas)} formulas)")
            
            for formula_path in sorted(formulas):
                deps = self.dependencies.get(formula_path, set())
                internal_deps = [d for d in deps if d in self.formula_paths]
                
                if internal_deps:
                    print(f"  - {formula_path} (depends on: {', '.join(sorted(internal_deps))})")
                else:
                    print(f"  - {formula_path} (no internal dependencies)")
            
            print()
    
    def validate_dependencies(self) -> List[str]:
        """
        Validates if there are circular dependencies or graph problems.
        
        Returns:
            List of errors found
        """
        errors = []
        
        # Check circular dependencies using DFS
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependencies.get(node, set()):
                if neighbor in self.formula_paths:  # Only check internal dependencies
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for path in self.formula_paths:
            if path not in visited:
                if has_cycle(path, visited, set()):
                    errors.append(f"Circular dependency detected involving {path}")
        
        # All dependencies are validated during graph building
        
        return errors


def main():
    """Main function to test the classification."""
    # Load formulas.json file
    with open('formulas.json', 'r', encoding='utf-8') as f:
        formulas_data = json.load(f)
    
    # Create classifier
    classifier = FormulaExecutionClassifier(formulas_data)
    
    # Validate dependencies
    errors = classifier.validate_dependencies()
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    # Classify and print execution plan
    classifier.classify_execution_groups()
    classifier.print_execution_plan()
    
    # Return result
    return classifier.get_execution_order()


if __name__ == "__main__":
    execution_plan = main()
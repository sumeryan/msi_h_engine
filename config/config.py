"""
Global configurations for the hierarchical calculation engine.

Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com
"""
from typing import Dict, Any, Set
from pydantic import BaseModel

class EngineConfig(BaseModel):
    
    # Allowed safe agregate functions
    safe_aggr_functions: Set[str] = {
        "sum", "avg", "count", "max", "min", "abs", "len", "round", 
        "first", "last","firstc", "lastc",
        "sum_node", "avg_node", "count_node", "max_node", "min_node" 
    }

    # Allowed safe functions
    safe_custom_functions: Set[str] = {
        "contains"
    }

    # Blocked AST nodes
    blocked_ast_nodes: Set[str] = {
        "Import", "ImportFrom", "Exec", "Global", "Eval",
        "FunctionDef", "ClassDef", "AsyncFunctionDef"
    }


# Global configuration instance
default_config = EngineConfig()

def get_config() -> EngineConfig:
    """Returns the global configuration."""
    return default_config

def update_config(config_updates: Dict[str, Any]) -> None:
    """Updates the global configuration with the provided values."""
    for key, value in config_updates.items():
        if hasattr(default_config, key):
            setattr(default_config, key, value)
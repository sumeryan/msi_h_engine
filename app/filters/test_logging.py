"""
Test script to verify that the logging module is working correctly.
This script executes a few filter operations to generate log messages.
"""

import json
import sys
from log import get_logger
import formulas.filters.filters_paths as filters_paths

# Get a logger for this module
logger = get_logger("test_logging")

def main():
    """Main test function"""
    logger.info("Starting logging test")
    
    try:
        # Load test data
        logger.debug("Loading test data from tree_data.json")
        try:
            with open('tree_data.json', 'r') as f:
                tree_data = json.load(f)
            logger.info("Successfully loaded test data")
        except Exception as e:
            logger.error(f"Failed to load test data: {str(e)}")
            return 1
        
        # Test simple filter
        logger.info("Testing simple filter")
        filter_expr = "e00001v == 'Automovel'"
        results = filters_paths.filter_tree_data(tree_data, filter_expr)
        logger.info(f"Simple filter returned {len(results)} records")
        
        # Test filter with record_id
        logger.info("Testing filter with record_id")
        record_id = "01967343-b7d4-7e20-908c-c48e8cf68789"  # ID of a record with Automovel
        results = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id)
        logger.info(f"Filter with record_id returned {len(results)} records")
        
        # Test filter with return_paths
        logger.info("Testing filter with return_paths")
        paths_to_extract = ["e00001v", "e00009v"]
        results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract)
        logger.info(f"Filter with return_paths returned values for {len(results)} paths")
        
        # Test filter with special functions
        logger.info("Testing filter with special functions")
        filter_expr = "first(e00001v) == 'Automovel'"
        results = filters_paths.filter_tree_data(tree_data, filter_expr)
        logger.info(f"Filter with special function returned {len(results)} records")
        
        # Test filter with complex expression
        logger.info("Testing filter with complex expression")
        filter_expr = "e00001v == 'Automovel' or contains(e00001v, 'Caminhão')"
        results = filters_paths.filter_tree_data(tree_data, filter_expr)
        logger.info(f"Filter with complex expression returned {len(results)} records")
        
        logger.info("All tests completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
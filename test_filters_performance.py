#!/usr/bin/env python3
"""
Performance comparison test between original and optimized filters

This script tests both the original and optimized versions of the filters
to validate functionality and measure performance improvements.
"""

import time
import json
import sys
import os
from typing import Dict, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import both versions
from filters.filters_paths import filter_tree_data as filter_original, tree_data_filter as OriginalFilter
from filters.filters_paths_optimized import filter_tree_data_optimized, get_optimized_parser

def load_test_data() -> Dict:
    """Load test data from available JSON files"""
    test_files = [
        "data_tree_0196b01a-2163-7cb2-93b9-c8b1342e3a4e.json",
        "data/all_doctypes_data.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"Loading test data from: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle case where data is a list instead of dict
                if isinstance(data, list):
                    return {"data": data}
                return data
    
    # Create synthetic test data if no files found
    print("Creating synthetic test data...")
    return create_synthetic_test_data()

def create_synthetic_test_data() -> Dict:
    """Create synthetic test data for testing"""
    return {
        "data": [
            {
                "id": "test_001",
                "creation": "2024-01-01T10:00:00",
                "fields": [
                    {"path": "field1", "value": 100},
                    {"path": "field2", "value": "test_value"}
                ],
                "data": [
                    {
                        "id": "test_002", 
                        "creation": "2024-01-01T11:00:00",
                        "fields": [
                            {"path": "field3", "value": 200},
                            {"path": "field4", "value": "nested_value"}
                        ],
                        "data": [
                            {
                                "id": "test_003",
                                "creation": "2024-01-01T12:00:00", 
                                "fields": [
                                    {"path": "field5", "value": 300}
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "id": "test_004",
                "creation": "2024-01-02T10:00:00",
                "fields": [
                    {"path": "field1", "value": 150},
                    {"path": "field6", "value": "another_value"}
                ]
            }
        ]
    }

def test_functionality_compatibility(test_data: Dict):
    """Test that both versions produce the same results"""
    print("\n=== Testing Functionality Compatibility ===")
    
    test_cases = [
        {
            "name": "Simple field extraction",
            "filter_expr": None,
            "return_paths": ["field1", "field2"],
            "record_id": None
        },
        {
            "name": "Filter with expression", 
            "filter_expr": "field1 == 100",
            "return_paths": ["field1", "field2"],
            "record_id": None
        },
        {
            "name": "Special function first",
            "filter_expr": None,
            "return_paths": ["first(field1)"],
            "record_id": None
        },
        {
            "name": "Record ID specific",
            "filter_expr": None,
            "return_paths": ["field3"],
            "record_id": "test_002"
        }
    ]
    
    compatibility_passed = True
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            # Test original version
            original_result = filter_original(
                test_data,
                test_case['return_paths'],
                test_case['record_id'],
                test_case['filter_expr']
            )
            
            # Test optimized version
            optimized_result = filter_tree_data_optimized(
                test_data,
                test_case['return_paths'].copy(),  # Copy to avoid mutation
                test_case['record_id'],
                test_case['filter_expr']
            )
            
            # Compare results
            if len(original_result) == len(optimized_result):
                results_match = True
                for orig_item, opt_item in zip(original_result, optimized_result):
                    if orig_item.get('path') != opt_item.get('path'):
                        results_match = False
                        break
                    # Note: Values might be in different order, so we compare sets
                    orig_values = set(str(v) for v in orig_item.get('values', []))
                    opt_values = set(str(v) for v in opt_item.get('values', []))
                    if orig_values != opt_values:
                        results_match = False
                        break
                
                if results_match:
                    print(f"  ✓ Results match")
                else:
                    print(f"  ✗ Results differ")
                    print(f"    Original: {original_result}")
                    print(f"    Optimized: {optimized_result}")
                    compatibility_passed = False
            else:
                print(f"  ✗ Different number of results")
                print(f"    Original: {len(original_result)} items")
                print(f"    Optimized: {len(optimized_result)} items")
                compatibility_passed = False
                
        except Exception as e:
            print(f"  ✗ Error during test: {str(e)}")
            compatibility_passed = False
    
    if compatibility_passed:
        print(f"\n✓ All compatibility tests passed!")
    else:
        print(f"\n✗ Some compatibility tests failed!")
    
    return compatibility_passed

def measure_performance(test_data: Dict, iterations: int = 100):
    """Measure and compare performance between versions"""
    print(f"\n=== Performance Comparison ({iterations} iterations) ===")
    
    test_cases = [
        {
            "name": "Simple extraction",
            "filter_expr": None,
            "return_paths": ["field1", "field2", "field3"],
            "record_id": None
        },
        {
            "name": "Complex filter",
            "filter_expr": "field1 == 100 or field3 == 200",
            "return_paths": ["field1", "field2", "field3"],
            "record_id": None
        },
        {
            "name": "Special functions",
            "filter_expr": None,
            "return_paths": ["first(field1)", "last(field3)"],
            "record_id": None
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Test original version
        start_time = time.time()
        for _ in range(iterations):
            try:
                filter_original(
                    test_data,
                    test_case['return_paths'].copy(),
                    test_case['record_id'],
                    test_case['filter_expr']
                )
            except Exception as e:
                print(f"  Original version error: {e}")
                break
        original_time = time.time() - start_time
        
        # Test optimized version
        start_time = time.time()
        for _ in range(iterations):
            try:
                filter_tree_data_optimized(
                    test_data,
                    test_case['return_paths'].copy(),
                    test_case['record_id'],
                    test_case['filter_expr']
                )
            except Exception as e:
                print(f"  Optimized version error: {e}")
                break
        optimized_time = time.time() - start_time
        
        # Calculate improvement
        if original_time > 0:
            improvement = ((original_time - optimized_time) / original_time) * 100
            speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        else:
            improvement = 0
            speedup = 1
        
        results[test_case['name']] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'improvement_percent': improvement,
            'speedup': speedup
        }
        
        print(f"  Original: {original_time:.4f}s")
        print(f"  Optimized: {optimized_time:.4f}s")
        print(f"  Improvement: {improvement:.1f}% ({speedup:.2f}x faster)")
    
    return results

def test_memory_usage():
    """Test memory usage characteristics"""
    print("\n=== Memory Usage Test ===")
    
    # Test parser instance reuse
    print("Testing parser instance reuse...")
    
    # Create multiple parser instances (original way)
    start_time = time.time()
    for _ in range(10):
        parser = OriginalFilter()
    original_creation_time = time.time() - start_time
    
    # Use singleton pattern (optimized way)
    start_time = time.time()
    for _ in range(10):
        parser = get_optimized_parser()
    optimized_creation_time = time.time() - start_time
    
    print(f"  Original (10 new instances): {original_creation_time:.4f}s")
    print(f"  Optimized (10 singleton calls): {optimized_creation_time:.4f}s")
    
    if original_creation_time > 0:
        improvement = ((original_creation_time - optimized_creation_time) / original_creation_time) * 100
        print(f"  Parser creation improvement: {improvement:.1f}%")

def main():
    """Main test function"""
    print("=== Filters Performance and Compatibility Test ===")
    
    # Load test data
    test_data = load_test_data()
    print(f"Test data loaded: {len(test_data.get('data', []))} root nodes")
    
    # Test functionality compatibility
    compatibility_ok = test_functionality_compatibility(test_data)
    
    if not compatibility_ok:
        print("\n⚠️  Compatibility issues found. Performance tests may not be reliable.")
    
    # Test memory usage
    test_memory_usage()
    
    # Test performance
    performance_results = measure_performance(test_data, iterations=50)
    
    # Summary
    print("\n=== SUMMARY ===")
    total_improvements = []
    for test_name, results in performance_results.items():
        improvement = results['improvement_percent']
        total_improvements.append(improvement)
        print(f"{test_name}: {improvement:.1f}% improvement ({results['speedup']:.2f}x speedup)")
    
    if total_improvements:
        avg_improvement = sum(total_improvements) / len(total_improvements)
        print(f"\nAverage performance improvement: {avg_improvement:.1f}%")
        
        if avg_improvement > 0:
            print("✓ Optimized version shows performance improvements!")
        else:
            print("⚠️  Optimized version may need further tuning.")
    
    if compatibility_ok:
        print("✓ Functional compatibility maintained.")
    else:
        print("✗ Functional compatibility issues detected.")

if __name__ == "__main__":
    main()
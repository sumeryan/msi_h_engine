#!/usr/bin/env python3
"""
Simple performance test for filters optimization
"""

import time
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from filters.filters_paths import tree_data_filter as OriginalFilter
from filters.filters_paths_optimized import TreeDataFilterOptimized, get_optimized_parser

def create_test_data():
    """Create synthetic test data"""
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

def test_parser_creation_performance():
    """Test parser creation performance"""
    print("=== Parser Creation Performance ===")
    
    iterations = 50
    
    # Test original parser creation
    start_time = time.time()
    for _ in range(iterations):
        parser = OriginalFilter()
    original_time = time.time() - start_time
    
    # Test optimized parser creation (singleton)
    start_time = time.time()
    for _ in range(iterations):
        parser = get_optimized_parser()  # Should reuse singleton
    optimized_time = time.time() - start_time
    
    improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0
    
    print(f"Original ({iterations} new instances): {original_time:.4f}s")
    print(f"Optimized ({iterations} singleton calls): {optimized_time:.4f}s")
    print(f"Parser creation improvement: {improvement:.1f}%")
    
    return improvement

def test_expression_parsing():
    """Test expression parsing performance"""
    print("\n=== Expression Parsing Performance ===")
    
    expressions = [
        "field1 == 100",
        "field1 == 100 and field2 == 'test'",
        "field3 > 150 or field1 < 200"
    ]
    
    iterations = 100
    
    for expr in expressions:
        print(f"\nTesting expression: {expr}")
        
        # Original parsing
        original_parser = OriginalFilter()
        start_time = time.time()
        for _ in range(iterations):
            original_parser.parse(expr)
        original_time = time.time() - start_time
        
        # Optimized parsing (with cache)
        optimized_parser = get_optimized_parser()
        start_time = time.time()
        for _ in range(iterations):
            optimized_parser.parse(expr)  # Should hit cache after first call
        optimized_time = time.time() - start_time
        
        improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0
        
        print(f"  Original: {original_time:.4f}s")
        print(f"  Optimized: {optimized_time:.4f}s") 
        print(f"  Improvement: {improvement:.1f}%")

def main():
    """Main test function"""
    print("=== Simple Performance Test ===")
    
    # Test parser creation
    parser_improvement = test_parser_creation_performance()
    
    # Test expression parsing
    test_expression_parsing()
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"Parser creation improvement: {parser_improvement:.1f}%")
    
    if parser_improvement > 50:
        print("✓ Significant performance improvement achieved!")
    elif parser_improvement > 0:
        print("✓ Some performance improvement achieved.")
    else:
        print("⚠️  Performance improvement needs investigation.")

if __name__ == "__main__":
    main()
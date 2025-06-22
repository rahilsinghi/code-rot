"""
Problem: Remove Duplicates from Sorted Array
Platform: Leetcode
Difficulty: Easy
Date: 2025-06-21
URL: https://leetcode.com/problems/remove-duplicates-from-sorted-array/

Problem Description:
Given an integer array nums sorted in non-decreasing order, remove the duplicates in-place such that each unique element appears only once.
The relative order of the elements should be kept the same. Return k after placing the final result in the first k slots of nums.

Examples:
Input: nums = [1,1,2]
Output: 2, nums = [1,2,_]

Input: nums = [0,0,1,1,1,2,2,3,3,4]
Output: 5, nums = [0,1,2,3,4,_,_,_,_,_]

Constraints:
1 <= nums.length <= 3 * 10^4, -100 <= nums[i] <= 100, nums is sorted in non-decreasing order.

Tags: array,two-pointers
"""

# Standard library imports
from typing import List, Dict, Set, Tuple, Optional, Union
import math
import heapq
import bisect
from collections import Counter, defaultdict, deque
from functools import lru_cache
import itertools

# Third-party imports (available in venv - uncomment as needed)
import numpy as np
# import pandas as pd
# from sortedcontainers import SortedList, SortedDict, SortedSet
# import networkx as nx

def solution_two_pointers(nums: List[int]) -> int:
    """
    Two-pointer approach:
    1. Use slow pointer to track position for next unique element
    2. Use fast pointer to scan through array
    3. When we find a different element, place it at slow pointer position
    
    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    if not nums:
        return 0
    
    slow = 1  # Position for next unique element
    
    for fast in range(1, len(nums)):
        if nums[fast] != nums[fast - 1]:
            nums[slow] = nums[fast]
            slow += 1
    
    return slow

def solution_with_numpy(nums: List[int]) -> int:
    """
    Using NumPy for demonstration (though overkill for this problem):
    Shows how to leverage the libraries available in our venv
    
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    if not nums:
        return 0
    
    # Convert to numpy array for advanced operations
    arr = np.array(nums)
    
    # Find unique elements while preserving order
    unique_vals, indices = np.unique(arr, return_index=True)
    unique_vals = unique_vals[np.argsort(indices)]  # Maintain original order
    
    # Update original array
    for i, val in enumerate(unique_vals):
        nums[i] = val
    
    return len(unique_vals)

def solution_with_collections(nums: List[int]) -> int:
    """
    Using collections module for educational purposes:
    Demonstrates Counter usage (though not optimal for this specific problem)
    
    Time Complexity: O(n)
    Space Complexity: O(k) where k is number of unique elements
    """
    if not nums:
        return 0
    
    # Count occurrences (for demonstration)
    counter = Counter(nums)
    
    # Get unique elements in order
    seen = set()
    unique_idx = 0
    
    for num in nums:
        if num not in seen:
            nums[unique_idx] = num
            seen.add(num)
            unique_idx += 1
    
    return unique_idx

def benchmark_solutions():
    """
    Benchmark different solutions using the rich library for pretty output
    """
    from rich.console import Console
    from rich.table import Table
    import time
    
    console = Console()
    
    # Test data
    test_cases = [
        [1, 1, 2],
        [0, 0, 1, 1, 1, 2, 2, 3, 3, 4],
        list(range(100)) * 10,  # Larger test case
    ]
    
    solutions = [
        ("Two Pointers", solution_two_pointers),
        ("NumPy", solution_with_numpy),
        ("Collections", solution_with_collections),
    ]
    
    table = Table(title="Solution Performance Comparison")
    table.add_column("Solution", style="cyan")
    table.add_column("Test Case 1", style="magenta")
    table.add_column("Test Case 2", style="magenta")
    table.add_column("Test Case 3", style="magenta")
    
    for name, func in solutions:
        times = []
        for test_case in test_cases:
            nums = test_case.copy()
            start = time.time()
            result = func(nums)
            end = time.time()
            times.append(f"{(end-start)*1000:.3f}ms")
        
        table.add_row(name, *times)
    
    console.print(table)

def test_solution():
    """Test cases for the solution"""
    # Test case 1
    nums1 = [1, 1, 2]
    expected1 = 2
    result1 = solution_two_pointers(nums1)
    assert result1 == expected1, f"Test 1 failed: expected {expected1}, got {result1}"
    assert nums1[:result1] == [1, 2], f"Array modification failed for test 1"
    
    # Test case 2
    nums2 = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    expected2 = 5
    result2 = solution_two_pointers(nums2)
    assert result2 == expected2, f"Test 2 failed: expected {expected2}, got {result2}"
    assert nums2[:result2] == [0, 1, 2, 3, 4], f"Array modification failed for test 2"
    
    # Edge case: single element
    nums3 = [1]
    expected3 = 1
    result3 = solution_two_pointers(nums3)
    assert result3 == expected3, f"Test 3 failed: expected {expected3}, got {result3}"
    
    # Test all solutions give same results
    test_nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    results = []
    for func in [solution_two_pointers, solution_with_numpy, solution_with_collections]:
        nums_copy = test_nums.copy()
        result = func(nums_copy)
        results.append((result, nums_copy[:result]))
    
    # All results should be the same
    assert all(r == results[0] for r in results), "Different solutions gave different results!"
    
    print("✅ All test cases passed!")

def main():
    """Main function demonstrating the virtual environment capabilities"""
    print("🧪 Testing Remove Duplicates solutions...")
    test_solution()
    
    print("\n📊 Running performance benchmark...")
    benchmark_solutions()
    
    print("\n💡 This example demonstrates:")
    print("   • Two-pointer technique (optimal solution)")
    print("   • NumPy usage for array operations")
    print("   • Collections module for counting")
    print("   • Rich library for beautiful terminal output")
    print("   • Performance comparison between approaches")

if __name__ == "__main__":
    main()

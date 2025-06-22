"""
Problem: Two Sum
Platform: LeetCode
Difficulty: Easy
Date: 2024-01-15
URL: https://leetcode.com/problems/two-sum/

Problem Description:
Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
You may assume that each input would have exactly one solution, and you may not use the same element twice.
You can return the answer in any order.

Example:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Constraints:
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- -10^9 <= target <= 10^9
- Only one valid answer exists.

Tags: array, hash-table
"""

def two_sum_brute_force(nums, target):
    """
    Brute force approach:
    1. Check every pair of numbers
    2. Return indices when sum equals target
    
    Time Complexity: O(n²)
    Space Complexity: O(1)
    """
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

def two_sum_hash_map(nums, target):
    """
    Hash map approach:
    1. Store each number and its index in a hash map
    2. For each number, check if target - number exists in the map
    3. Return indices when found
    
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    num_to_index = {}
    
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_to_index:
            return [num_to_index[complement], i]
        num_to_index[num] = i
    
    return []

def two_sum_one_pass(nums, target):
    """
    One-pass hash map approach:
    1. Check for complement while building the hash map
    2. More efficient as we don't need to traverse twice
    
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

def test_solution():
    """Test cases for the solution"""
    # Test case 1
    assert two_sum_hash_map([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum_one_pass([2, 7, 11, 15], 9) == [0, 1]
    
    # Test case 2
    assert two_sum_hash_map([3, 2, 4], 6) == [1, 2]
    assert two_sum_one_pass([3, 2, 4], 6) == [1, 2]
    
    # Test case 3
    assert two_sum_hash_map([3, 3], 6) == [0, 1]
    assert two_sum_one_pass([3, 3], 6) == [0, 1]
    
    # Test with negative numbers
    assert two_sum_hash_map([-1, -2, -3, -4, -5], -8) == [2, 4]
    
    print("All test cases passed!")

if __name__ == "__main__":
    test_solution()
    
    # Performance comparison (optional)
    import time
    
    # Large test case
    large_nums = list(range(10000))
    target = 19999
    
    # Time the hash map approach
    start = time.time()
    result = two_sum_hash_map(large_nums, target)
    hash_time = time.time() - start
    
    print(f"Hash map approach: {hash_time:.6f} seconds")
    print(f"Result: {result}") 
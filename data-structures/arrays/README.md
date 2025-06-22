# 📊 Arrays

## 🎯 Overview
Arrays are one of the most fundamental data structures in computer science. They store elements in contiguous memory locations and provide constant-time access to elements by index.

## 🔑 Key Concepts

### Basic Operations
- **Access**: O(1) - Direct access by index
- **Search**: O(n) - Linear search for unsorted array
- **Insertion**: O(n) - Need to shift elements
- **Deletion**: O(n) - Need to shift elements

### Types of Arrays
- **Static Arrays**: Fixed size
- **Dynamic Arrays**: Resizable (e.g., Python lists, Java ArrayList)
- **Multi-dimensional Arrays**: 2D, 3D arrays

## 🧠 Important Techniques

### Two Pointers
Used for problems involving pairs or subarrays
```python
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []
```

### Sliding Window
Efficient for subarray problems
```python
def max_sum_subarray(arr, k):
    if len(arr) < k:
        return -1
    
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    for i in range(len(arr) - k):
        window_sum = window_sum - arr[i] + arr[i + k]
        max_sum = max(max_sum, window_sum)
    
    return max_sum
```

### Prefix Sum
Useful for range sum queries
```python
def build_prefix_sum(arr):
    prefix = [0] * (len(arr) + 1)
    for i in range(len(arr)):
        prefix[i + 1] = prefix[i] + arr[i]
    return prefix

def range_sum(prefix, left, right):
    return prefix[right + 1] - prefix[left]
```

## 📚 Essential Problems

### Beginner Level
- [ ] Two Sum
- [ ] Remove Duplicates from Sorted Array
- [ ] Merge Sorted Array
- [ ] Best Time to Buy and Sell Stock
- [ ] Maximum Subarray (Kadane's Algorithm)

### Intermediate Level
- [ ] 3Sum
- [ ] Container With Most Water
- [ ] Product of Array Except Self
- [ ] Rotate Array
- [ ] Find All Numbers Disappeared in an Array

### Advanced Level
- [ ] Trapping Rain Water
- [ ] Median of Two Sorted Arrays
- [ ] Maximum Product Subarray
- [ ] Sliding Window Maximum
- [ ] Minimum Window Substring

## 🔍 Common Patterns

1. **Frequency Counting**: Use hash maps to count elements
2. **Sorting**: Often simplifies the problem
3. **Binary Search**: For sorted arrays
4. **Divide and Conquer**: Break problem into smaller parts
5. **Greedy Approach**: Make locally optimal choices

## 💡 Tips & Tricks

1. **Edge Cases**: Always consider empty arrays, single elements
2. **Index Bounds**: Be careful with array boundaries
3. **In-place Operations**: Try to solve without extra space
4. **Multiple Passes**: Sometimes multiple passes are more readable
5. **Sorting Trade-off**: Consider if sorting helps vs. preserving order

## 🎯 Practice Plan

### Week 1: Basics
- Master basic operations
- Solve 5 easy problems
- Understand time/space complexity

### Week 2: Two Pointers & Sliding Window
- Learn the techniques
- Solve 8-10 problems using these patterns
- Practice implementation from scratch

### Week 3: Advanced Techniques
- Prefix sums, binary search on arrays
- Solve medium-level problems
- Focus on optimization

### Week 4: Integration
- Solve mixed difficulty problems
- Time yourself
- Review and optimize solutions

---

*Remember: Arrays are the foundation for many other data structures and algorithms. Master them well!* 
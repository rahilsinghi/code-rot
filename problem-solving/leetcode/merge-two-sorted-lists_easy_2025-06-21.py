"""
Problem: Merge Two Sorted Lists
Platform: Leetcode
Difficulty: Easy
Date: 2025-06-21
URL: https://leetcode.com/problems/merge-two-sorted-lists/

Problem Description:
You are given the heads of two sorted linked lists list1 and list2. Merge the two lists in a one sorted list.

Examples:
Input: list1 = [1,2,4], list2 = [1,3,4]
Output: [1,1,2,3,4,4]

Constraints:
The number of nodes in both lists is in the range [0, 50].
-100 <= Node.val <= 100
Both list1 and list2 are sorted in non-decreasing order.

Tags: linked-list,recursion
"""

def solution():
    # 1. Create a dummy node to start the merged list
    # 2. Create a pointer to the current node in the merged list
    # 3. While both lists have nodes left, compare the values of the current nodes
    # 4. Append the smaller value to the merged list
    # 5. Move the pointer to the next node in the list with the smaller value
    # 6. If one of the lists is exhausted, append the remaining nodes of the other list
    # 7. Return the merged list starting from the dummy node's next node
    dummy = ListNode()
    current = dummy
    while list1 and list2:
        if list1.val < list2.val:
            current.next = list1
            list1 = list1.next
        else:
            current.next = list2
            list2 = list2.next
        current = current.next
    current.next = list1 if list1 else list2
    return dummy.next
    """
    Approach:
    1. [Step 1 description]
    2. [Step 2 description]
    3. [Step 3 description]
    
    Time Complexity: O(?)
    Space Complexity: O(?)
    """
    pass

def solution_optimized():
    """
    Optimized approach:
    [Describe the optimized approach]
    
    Time Complexity: O(?)
    Space Complexity: O(?)
    """
    pass

def test_solution():
    """Test cases for the solution"""
    # Test cases based on examples
    # Test case 1: list1 = [1,2,4], list2 = [1,3,4]
    
    print("All test cases passed!")

if __name__ == "__main__":
    test_solution()

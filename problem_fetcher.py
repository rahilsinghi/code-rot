#!/usr/bin/env python3
"""
Problem Fetcher Module
Fetches problems from various coding platforms APIs
"""

import requests
import json
import time
from typing import List, Dict, Optional

class ProblemFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_leetcode_problems(self, limit: int = 50) -> List[Dict]:
        """
        Fetch problems from LeetCode API
        Note: This uses LeetCode's GraphQL API which may have rate limits
        """
        problems = []
        
        # LeetCode GraphQL endpoint
        url = "https://leetcode.com/graphql"
        
        # GraphQL query to get problem list
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
          problemsetQuestionList: questionList(
            categorySlug: $categorySlug
            limit: $limit
            skip: $skip
            filters: $filters
          ) {
            total: totalNum
            questions: data {
              acRate
              difficulty
              freqBar
              frontendQuestionId: questionFrontendId
              isFavor
              paidOnly: isPaidOnly
              status
              title
              titleSlug
              topicTags {
                name
                id
                slug
              }
              hasSolution
              hasVideoSolution
            }
          }
        }
        """
        
        variables = {
            "categorySlug": "",
            "skip": 0,
            "limit": limit,
            "filters": {}
        }
        
        try:
            response = self.session.post(
                url,
                json={"query": query, "variables": variables},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'problemsetQuestionList' in data['data']:
                    questions = data['data']['problemsetQuestionList']['questions']
                    
                    for q in questions:
                        if not q.get('paidOnly', True):  # Only free problems
                            problem = {
                                'title': q['title'],
                                'slug': q['titleSlug'],
                                'difficulty': q['difficulty'].lower(),
                                'topic': self._extract_primary_topic(q.get('topicTags', [])),
                                'platform': 'leetcode',
                                'description': f"Problem #{q['frontendQuestionId']}: {q['title']}",
                                'examples': '[]',
                                'constraints': '',
                                'hints': '',
                                'url': f"https://leetcode.com/problems/{q['titleSlug']}/",
                                'tags': ','.join([tag['name'] for tag in q.get('topicTags', [])])
                            }
                            problems.append(problem)
            
            print(f"✅ Fetched {len(problems)} problems from LeetCode")
            
        except Exception as e:
            print(f"❌ Error fetching LeetCode problems: {e}")
        
        return problems
    
    def fetch_sample_problems(self) -> List[Dict]:
        """
        Fetch a curated list of essential coding problems
        """
        sample_problems = [
            {
                "title": "Remove Duplicates from Sorted Array",
                "slug": "remove-duplicates-from-sorted-array",
                "difficulty": "easy",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an integer array nums sorted in non-decreasing order, remove the duplicates in-place such that each unique element appears only once.",
                "examples": '[{"input": "nums = [1,1,2]", "output": "2, nums = [1,2,_]", "explanation": "Your function should return k = 2, with the first two elements of nums being 1 and 2 respectively."}]',
                "constraints": "1 <= nums.length <= 3 * 10^4\n-100 <= nums[i] <= 100\nnums is sorted in non-decreasing order.",
                "url": "https://leetcode.com/problems/remove-duplicates-from-sorted-array/",
                "tags": "array,two-pointers"
            },
            {
                "title": "Best Time to Buy and Sell Stock",
                "slug": "best-time-to-buy-and-sell-stock",
                "difficulty": "easy",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "You are given an array prices where prices[i] is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.",
                "examples": '[{"input": "prices = [7,1,5,3,6,4]", "output": "5", "explanation": "Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5."}]',
                "constraints": "1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
                "url": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
                "tags": "array,dynamic-programming"
            },
            {
                "title": "Contains Duplicate",
                "slug": "contains-duplicate",
                "difficulty": "easy",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
                "examples": '[{"input": "nums = [1,2,3,1]", "output": "true"}, {"input": "nums = [1,2,3,4]", "output": "false"}]',
                "constraints": "1 <= nums.length <= 10^5\n-10^9 <= nums[i] <= 10^9",
                "url": "https://leetcode.com/problems/contains-duplicate/",
                "tags": "array,hash-table,sorting"
            },
            {
                "title": "Product of Array Except Self",
                "slug": "product-of-array-except-self",
                "difficulty": "medium",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].",
                "examples": '[{"input": "nums = [1,2,3,4]", "output": "[24,12,8,6]"}]',
                "constraints": "2 <= nums.length <= 10^5\n-30 <= nums[i] <= 30",
                "url": "https://leetcode.com/problems/product-of-array-except-self/",
                "tags": "array,prefix-sum"
            },
            {
                "title": "Reverse Linked List",
                "slug": "reverse-linked-list",
                "difficulty": "easy",
                "topic": "linked-lists",
                "platform": "leetcode",
                "description": "Given the head of a singly linked list, reverse the list, and return the reversed list.",
                "examples": '[{"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"}]',
                "constraints": "The number of nodes in the list is the range [0, 5000].\n-5000 <= Node.val <= 5000",
                "url": "https://leetcode.com/problems/reverse-linked-list/",
                "tags": "linked-list,recursion"
            },
            {
                "title": "Linked List Cycle",
                "slug": "linked-list-cycle",
                "difficulty": "easy",
                "topic": "linked-lists",
                "platform": "leetcode",
                "description": "Given head, the head of a linked list, determine if the linked list has a cycle in it.",
                "examples": '[{"input": "head = [3,2,0,-4], pos = 1", "output": "true", "explanation": "There is a cycle in the linked list, where the tail connects to the 1st node (0-indexed)."}]',
                "constraints": "The number of the nodes in the list is in the range [0, 10^4].\n-10^5 <= Node.val <= 10^5",
                "url": "https://leetcode.com/problems/linked-list-cycle/",
                "tags": "hash-table,linked-list,two-pointers"
            },
            {
                "title": "Binary Tree Inorder Traversal",
                "slug": "binary-tree-inorder-traversal",
                "difficulty": "easy",
                "topic": "trees",
                "platform": "leetcode",
                "description": "Given the root of a binary tree, return the inorder traversal of its nodes' values.",
                "examples": '[{"input": "root = [1,null,2,3]", "output": "[1,3,2]"}]',
                "constraints": "The number of nodes in the tree is in the range [0, 100].\n-100 <= Node.val <= 100",
                "url": "https://leetcode.com/problems/binary-tree-inorder-traversal/",
                "tags": "stack,tree,depth-first-search,binary-tree"
            },
            {
                "title": "Maximum Depth of Binary Tree",
                "slug": "maximum-depth-of-binary-tree",
                "difficulty": "easy",
                "topic": "trees",
                "platform": "leetcode",
                "description": "Given the root of a binary tree, return its maximum depth.",
                "examples": '[{"input": "root = [3,9,20,null,null,15,7]", "output": "3"}]',
                "constraints": "The number of nodes in the tree is in the range [0, 10^4].\n-100 <= Node.val <= 100",
                "url": "https://leetcode.com/problems/maximum-depth-of-binary-tree/",
                "tags": "tree,depth-first-search,breadth-first-search,binary-tree"
            },
            {
                "title": "Implement Queue using Stacks",
                "slug": "implement-queue-using-stacks",
                "difficulty": "easy",
                "topic": "stacks",
                "platform": "leetcode",
                "description": "Implement a first in first out (FIFO) queue using only two stacks.",
                "examples": '[{"input": "[\\"MyQueue\\", \\"push\\", \\"push\\", \\"peek\\", \\"pop\\", \\"empty\\"]\\n[[], [1], [2], [], [], []]", "output": "[null, null, null, 1, 1, false]"}]',
                "constraints": "1 <= x <= 9\nAt most 100 calls will be made to push, pop, peek, and empty.",
                "url": "https://leetcode.com/problems/implement-queue-using-stacks/",
                "tags": "stack,design,queue"
            },
            {
                "title": "Min Stack",
                "slug": "min-stack",
                "difficulty": "medium",
                "topic": "stacks",
                "platform": "leetcode",
                "description": "Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.",
                "examples": '[{"input": "[\\"MinStack\\",\\"push\\",\\"push\\",\\"push\\",\\"getMin\\",\\"pop\\",\\"top\\",\\"getMin\\"]\\n[[],[-2],[0],[-3],[],[],[],[]]", "output": "[null,null,null,null,-3,null,0,-2]"}]',
                "constraints": "-2^31 <= val <= 2^31 - 1\nMethods pop, top and getMin operations will always be called on non-empty stacks.",
                "url": "https://leetcode.com/problems/min-stack/",
                "tags": "stack,design"
            }
        ]
        
        print(f"✅ Prepared {len(sample_problems)} curated problems")
        return sample_problems
    
    def _extract_primary_topic(self, topic_tags: List[Dict]) -> str:
        """Extract primary topic from LeetCode topic tags"""
        if not topic_tags:
            return "general"
        
        # Priority mapping for common topics
        topic_priority = {
            'array': 'arrays',
            'string': 'strings',
            'linked-list': 'linked-lists',
            'tree': 'trees',
            'binary-tree': 'trees',
            'stack': 'stacks',
            'queue': 'stacks',
            'heap': 'heaps',
            'hash-table': 'hash-tables',
            'graph': 'graphs',
            'dynamic-programming': 'dynamic-programming',
            'greedy': 'greedy',
            'backtracking': 'backtracking',
            'divide-and-conquer': 'divide-conquer',
            'sorting': 'sorting',
            'searching': 'searching',
            'two-pointers': 'arrays',
            'sliding-window': 'arrays'
        }
        
        # Find the highest priority topic
        for tag in topic_tags:
            tag_slug = tag.get('slug', '').lower()
            if tag_slug in topic_priority:
                return topic_priority[tag_slug]
        
        # Default to first tag or general
        return topic_tags[0].get('slug', 'general') if topic_tags else 'general'

if __name__ == "__main__":
    fetcher = ProblemFetcher()
    
    # Fetch sample problems
    problems = fetcher.fetch_sample_problems()
    
    # Try to fetch from LeetCode (optional)
    try:
        leetcode_problems = fetcher.fetch_leetcode_problems(20)
        problems.extend(leetcode_problems)
    except Exception as e:
        print(f"Could not fetch from LeetCode API: {e}")
    
    print(f"Total problems fetched: {len(problems)}") 
# Virtual Environment & Dependencies Guide

## Overview

This repository uses a Python virtual environment to provide a comprehensive set of libraries for solving coding problems. All dependencies are pre-installed and ready to use.

## Quick Start

### Activating the Environment

```bash
# Method 1: Use the alias (after running setup.sh)
activate-practice

# Method 2: Manual activation
source venv/bin/activate

# Method 3: Aliases automatically activate the environment
practice start
pstart --topic arrays
```

### Deactivating the Environment

```bash
deactivate
```

## Available Libraries

### Core Data Science & Algorithms
- **numpy** - Numerical computing, arrays, mathematical operations
- **pandas** - Data manipulation and analysis
- **scipy** - Scientific computing and advanced algorithms
- **matplotlib** - Plotting and data visualization
- **seaborn** - Statistical data visualization

### Data Structures & Algorithms
- **sortedcontainers** - Sorted list, dict, set implementations
- **networkx** - Graph algorithms and data structures
- **more-itertools** - Additional iterator functions

### Built-in Modules (Always Available)
- **heapq** - Priority queue operations
- **collections** - Counter, defaultdict, deque, etc.
- **bisect** - Binary search utilities
- **itertools** - Iterator building blocks
- **functools** - Higher-order functions and operations

### Development & Testing
- **pytest** - Testing framework
- **pytest-cov** - Coverage testing
- **ipdb** - Interactive debugger
- **memory-profiler** - Memory usage profiling

### Code Quality
- **black** - Code formatter
- **flake8** - Linting
- **isort** - Import sorting

### Interactive Development
- **jupyter** - Jupyter notebooks
- **ipython** - Enhanced interactive Python shell

### Utilities
- **tqdm** - Progress bars
- **rich** - Beautiful terminal output
- **requests** - HTTP requests
- **beautifulsoup4** - HTML/XML parsing
- **regex** - Advanced regular expressions

## Common Usage Examples

### Arrays & Mathematical Operations

```python
import numpy as np
import bisect
from collections import Counter, defaultdict

# NumPy arrays for efficient computation
arr = np.array([1, 2, 3, 4, 5])
result = np.sum(arr)

# Binary search
sorted_list = [1, 3, 5, 7, 9]
index = bisect.bisect_left(sorted_list, 5)

# Counting elements
counter = Counter([1, 2, 2, 3, 3, 3])
```

### Data Structures

```python
from collections import deque, defaultdict
from sortedcontainers import SortedList, SortedDict
import heapq

# Queue operations
queue = deque([1, 2, 3])
queue.appendleft(0)

# Heap operations
heap = [3, 1, 4, 1, 5]
heapq.heapify(heap)
smallest = heapq.heappop(heap)

# Sorted containers
sorted_list = SortedList([3, 1, 4, 1, 5])
sorted_list.add(2)
```

### Graph Problems

```python
import networkx as nx
from collections import defaultdict

# NetworkX for complex graph algorithms
G = nx.Graph()
G.add_edges_from([(1, 2), (2, 3), (3, 4)])
shortest_path = nx.shortest_path(G, 1, 4)

# Manual graph representation
graph = defaultdict(list)
graph[1].append(2)
graph[2].extend([1, 3])
```

### String Processing

```python
import regex as re
from collections import Counter

# Advanced regex patterns
pattern = re.compile(r'(?P<word>\w+)')
matches = pattern.findall("hello world")

# String analysis
text = "hello world"
char_count = Counter(text)
```

### Data Analysis Problems

```python
import pandas as pd
import numpy as np

# DataFrame operations for data problems
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
result = df.groupby('A').sum()
```

### Visualization (for understanding algorithms)

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Plotting algorithm performance
x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]
plt.plot(x, y)
plt.title("Algorithm Performance")
plt.show()
```

### Testing Your Solutions

```python
import pytest

def test_my_solution():
    assert my_function([1, 2, 3]) == 6
    assert my_function([]) == 0

# Run with: pytest filename.py
```

### Debugging

```python
import ipdb

def problematic_function(data):
    ipdb.set_trace()  # Debugger will stop here
    result = process_data(data)
    return result
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    large_list = [i for i in range(1000000)]
    return sum(large_list)

# Run with: python -m memory_profiler filename.py
```

## Problem-Specific Library Recommendations

### Array Problems
- `numpy` for mathematical operations
- `bisect` for binary search
- `collections.Counter` for frequency counting

### Tree Problems
- `collections.deque` for level-order traversal
- `heapq` for priority operations

### Graph Problems
- `networkx` for complex graph algorithms
- `collections.defaultdict` for adjacency lists
- `collections.deque` for BFS

### Dynamic Programming
- `functools.lru_cache` for memoization
- `numpy` for 2D array operations

### String Problems
- `collections.Counter` for character frequency
- `regex` for complex pattern matching

### Data Structure Design
- `sortedcontainers` for maintaining sorted order
- `heapq` for priority queues
- `collections.deque` for efficient append/pop

## Performance Tips

1. **Use NumPy** for mathematical operations on large arrays
2. **Use SortedContainers** when you need to maintain sorted order
3. **Use collections.deque** for queue operations (faster than list)
4. **Use functools.lru_cache** for memoization in recursive solutions
5. **Use bisect** for binary search instead of manual implementation

## Jupyter Notebooks

For complex problems or algorithm visualization:

```bash
# Start Jupyter Lab (with venv activated)
activate-practice
jupyter lab

# Or start classic notebook
jupyter notebook
```

## Installing Additional Libraries

If you need additional libraries for specific problems:

```bash
# Activate environment first
activate-practice

# Install additional packages
pip install package-name

# Update requirements.txt if needed
pip freeze > requirements.txt
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Import Errors

Make sure the virtual environment is activated:
```bash
which python  # Should show path to venv/bin/python
```

### Memory Issues

For memory-intensive problems, use the memory profiler:
```bash
pip install memory-profiler
python -m memory_profiler your_script.py
```

This comprehensive setup ensures you have all the tools needed for efficient problem-solving across different domains! 
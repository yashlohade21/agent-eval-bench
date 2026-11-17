#!/usr/bin/env python3
"""
Programmatic RL task generator.

Takes working Python functions, injects known bug patterns, and auto-generates
Harbor-format tasks with instructions, Dockerfiles, verifiers, and oracle solutions.

Usage:
    python generate.py --pattern off-by-one --count 5 --output tasks/generated/
    python generate.py --pattern all --count 3 --output tasks/generated/
    python generate.py --list-patterns
"""

import argparse
import json
import os
import random
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class BugPattern:
    """A bug pattern that can be injected into working code."""
    name: str
    description: str
    difficulty: str
    category: str
    skills: list[str]
    # Each template returns (buggy_code, correct_code, test_code, instruction)
    templates: list[Callable] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template functions — each returns a complete task variant
# ---------------------------------------------------------------------------

def off_by_one_binary_search(variant: int = 0):
    """Binary search with off-by-one in boundary conditions."""
    correct = textwrap.dedent('''\
        def binary_search(arr, target):
            """Return index of target in sorted arr, or -1 if not found."""
            left, right = 0, len(arr) - 1
            while left <= right:
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            return -1
    ''')

    bugs = [
        # Bug variant 0: < instead of <=
        ('left <= right', 'left < right',
         'Loop terminates too early when target is at boundary'),
        # Bug variant 1: right = mid instead of mid - 1
        ('right = mid - 1', 'right = mid',
         'Infinite loop when target is not in array'),
        # Bug variant 2: wrong initial right
        ('0, len(arr) - 1', '0, len(arr)',
         'Potential index out of bounds on the right'),
    ]

    idx = variant % len(bugs)
    orig, replacement, hint = bugs[idx]
    buggy = correct.replace(orig, replacement)

    tests = textwrap.dedent('''\
        import pytest
        from solution import binary_search

        def test_found_first():
            assert binary_search([1, 3, 5, 7, 9], 1) == 0

        def test_found_last():
            assert binary_search([1, 3, 5, 7, 9], 9) == 4

        def test_found_middle():
            assert binary_search([1, 3, 5, 7, 9], 5) == 2

        def test_not_found():
            assert binary_search([1, 3, 5, 7, 9], 4) == -1

        def test_empty():
            assert binary_search([], 1) == -1

        def test_single_element_found():
            assert binary_search([5], 5) == 0

        def test_single_element_not_found():
            assert binary_search([5], 3) == -1

        def test_two_elements():
            assert binary_search([1, 2], 2) == 1

        def test_large_array():
            arr = list(range(0, 10000, 2))
            assert binary_search(arr, 5000) == 2500
            assert binary_search(arr, 5001) == -1

        def test_duplicates():
            arr = [1, 2, 2, 2, 3]
            result = binary_search(arr, 2)
            assert arr[result] == 2

        def test_negative_numbers():
            assert binary_search([-5, -3, -1, 0, 2], -3) == 1
    ''')

    instruction = textwrap.dedent(f'''\
        # Fix the Binary Search Bug

        The file `/app/solution.py` contains a `binary_search()` function.
        It has a subtle bug that causes incorrect results in certain edge cases.

        Hint: {hint}

        Fix the function so all tests pass. Only modify `/app/solution.py`.
    ''')

    return buggy, correct, tests, instruction


def off_by_one_flatten(variant: int = 0):
    """Nested list flattening with depth-limit off-by-one."""
    correct = textwrap.dedent('''\
        def flatten(lst, max_depth=None, _current_depth=0):
            """Flatten a nested list up to max_depth levels.

            Args:
                lst: Nested list to flatten
                max_depth: Maximum depth to flatten (None = fully flatten)
                _current_depth: Internal tracker, do not set manually

            Returns:
                Flattened list
            """
            result = []
            for item in lst:
                if isinstance(item, list) and (max_depth is None or _current_depth < max_depth):
                    result.extend(flatten(item, max_depth, _current_depth + 1))
                else:
                    result.append(item)
            return result
    ''')

    bugs = [
        ('_current_depth < max_depth', '_current_depth <= max_depth',
         'Flattens one level too deep when max_depth is specified'),
        ('_current_depth + 1', '_current_depth',
         'Depth counter never increments, causing infinite recursion on deep lists'),
    ]

    idx = variant % len(bugs)
    orig, replacement, hint = bugs[idx]
    buggy = correct.replace(orig, replacement)

    tests = textwrap.dedent('''\
        import pytest
        from solution import flatten

        def test_flat_list():
            assert flatten([1, 2, 3]) == [1, 2, 3]

        def test_one_level():
            assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

        def test_deep_nesting():
            assert flatten([1, [2, [3, [4]]]]) == [1, 2, 3, 4]

        def test_max_depth_zero():
            assert flatten([[1, 2], [3, [4]]], max_depth=0) == [[1, 2], [3, [4]]]

        def test_max_depth_one():
            assert flatten([[1, [2]], [3, [4]]], max_depth=1) == [1, [2], 3, [4]]

        def test_max_depth_two():
            assert flatten([1, [2, [3, [4]]]], max_depth=2) == [1, 2, 3, [4]]

        def test_empty():
            assert flatten([]) == []

        def test_mixed_types():
            assert flatten([1, "hello", [2, [True]]]) == [1, "hello", 2, True]

        def test_max_depth_exceeds_actual():
            assert flatten([[1], [2]], max_depth=10) == [1, 2]
    ''')

    instruction = textwrap.dedent(f'''\
        # Fix the List Flatten Bug

        The file `/app/solution.py` contains a `flatten()` function that flattens
        nested lists with an optional `max_depth` parameter.

        Hint: {hint}

        Fix the function so all tests pass. Only modify `/app/solution.py`.
    ''')

    return buggy, correct, tests, instruction


def fence_post_range(variant: int = 0):
    """Range/interval operations with classic fencepost errors."""
    correct = textwrap.dedent('''\
        def merge_intervals(intervals):
            """Merge overlapping intervals. Each interval is [start, end] inclusive."""
            if not intervals:
                return []
            sorted_iv = sorted(intervals, key=lambda x: x[0])
            merged = [sorted_iv[0][:]]
            for start, end in sorted_iv[1:]:
                if start <= merged[-1][1] + 1:
                    merged[-1][1] = max(merged[-1][1], end)
                else:
                    merged.append([start, end])
            return merged


        def count_in_range(arr, low, high):
            """Count elements where low <= element <= high."""
            return sum(1 for x in arr if low <= x <= high)
    ''')

    bugs = [
        ('start <= merged[-1][1] + 1', 'start <= merged[-1][1]',
         'Adjacent intervals like [1,3] and [4,6] should merge but do not'),
        ('low <= x <= high', 'low <= x < high',
         'Elements equal to the upper bound are excluded'),
    ]

    idx = variant % len(bugs)
    orig, replacement, hint = bugs[idx]
    buggy = correct.replace(orig, replacement)

    tests = textwrap.dedent('''\
        import pytest
        from solution import merge_intervals, count_in_range

        class TestMergeIntervals:
            def test_no_overlap(self):
                assert merge_intervals([[1, 2], [4, 5]]) == [[1, 2], [4, 5]]

            def test_overlap(self):
                assert merge_intervals([[1, 3], [2, 5]]) == [[1, 5]]

            def test_adjacent(self):
                assert merge_intervals([[1, 3], [4, 6]]) == [[1, 6]]

            def test_contained(self):
                assert merge_intervals([[1, 10], [3, 5]]) == [[1, 10]]

            def test_empty(self):
                assert merge_intervals([]) == []

            def test_single(self):
                assert merge_intervals([[1, 5]]) == [[1, 5]]

            def test_multiple_merges(self):
                result = merge_intervals([[1, 3], [4, 6], [7, 9]])
                assert result == [[1, 9]]

            def test_unsorted(self):
                result = merge_intervals([[5, 7], [1, 3], [4, 6]])
                assert result == [[1, 7]]

        class TestCountInRange:
            def test_basic(self):
                assert count_in_range([1, 2, 3, 4, 5], 2, 4) == 3

            def test_inclusive_bounds(self):
                assert count_in_range([1, 2, 3], 1, 3) == 3

            def test_single_match(self):
                assert count_in_range([5], 5, 5) == 1

            def test_no_match(self):
                assert count_in_range([1, 2, 3], 5, 10) == 0

            def test_empty(self):
                assert count_in_range([], 1, 5) == 0
    ''')

    instruction = textwrap.dedent(f'''\
        # Fix the Interval/Range Bug

        The file `/app/solution.py` has two functions: `merge_intervals()` and
        `count_in_range()`. One of them has a fencepost error.

        Hint: {hint}

        Fix the bug so all tests pass. Only modify `/app/solution.py`.
    ''')

    return buggy, correct, tests, instruction


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

PATTERNS: dict[str, BugPattern] = {
    'off-by-one': BugPattern(
        name='off-by-one',
        description='Off-by-one errors in loops, boundaries, and indices',
        difficulty='easy',
        category='bug-fix',
        skills=['debugging', 'boundary-conditions', 'python'],
        templates=[off_by_one_binary_search, off_by_one_flatten],
    ),
    'fencepost': BugPattern(
        name='fencepost',
        description='Fencepost errors in ranges and interval operations',
        difficulty='easy',
        category='bug-fix',
        skills=['debugging', 'intervals', 'python'],
        templates=[fence_post_range],
    ),
}


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------

def generate_task(pattern: BugPattern, template_fn, variant: int, output_dir: Path):
    """Generate a single Harbor-format task from a template."""
    buggy, correct, tests, instruction = template_fn(variant)

    fn_name = template_fn.__name__
    task_name = f"gen-{pattern.name}-{fn_name}-v{variant}"
    task_dir = output_dir / task_name

    # Create directories
    for sub in ['environment', 'solution', 'tests']:
        (task_dir / sub).mkdir(parents=True, exist_ok=True)

    # instruction.md
    (task_dir / 'instruction.md').write_text(instruction)

    # task.toml
    toml = textwrap.dedent(f'''\
        [task]
        name = "{task_name}"
        difficulty = "{pattern.difficulty}"
        category = "{pattern.category}"
        language = "python"
        timeout_seconds = 120
        max_attempts = 1
        generated = true

        [task.metadata]
        description = "{pattern.description}"
        skills = {json.dumps(pattern.skills)}
        template = "{fn_name}"
        variant = {variant}
    ''')
    (task_dir / 'task.toml').write_text(toml)

    # Dockerfile
    dockerfile = textwrap.dedent(f'''\
        FROM python:3.11.7-slim
        RUN pip install --no-cache-dir pytest==7.4.4
        RUN mkdir -p /app /logs/verifier

        COPY <<'EOF' /app/solution.py
        {buggy}EOF

        COPY <<'EOF' /app/test_solution.py
        {tests}EOF

        WORKDIR /app
    ''')
    (task_dir / 'environment' / 'Dockerfile').write_text(dockerfile)

    # solve.sh
    solve = textwrap.dedent(f'''\
        #!/bin/bash
        cat > /app/solution.py << 'PYEOF'
        {correct}PYEOF
    ''')
    (task_dir / 'solution' / 'solve.sh').write_text(solve)
    os.chmod(task_dir / 'solution' / 'solve.sh', 0o755)

    # test.sh
    test_sh = textwrap.dedent('''\
        #!/bin/bash
        set -euo pipefail
        mkdir -p /logs/verifier
        cd /app
        if python -m pytest test_solution.py -v --tb=short -x 2>&1 | tee /logs/verifier/test_output.txt; then
            echo 1 > /logs/verifier/reward.txt
        else
            echo 0 > /logs/verifier/reward.txt
        fi
    ''')
    (task_dir / 'tests' / 'test.sh').write_text(test_sh)
    os.chmod(task_dir / 'tests' / 'test.sh', 0o755)

    return task_name


def main():
    parser = argparse.ArgumentParser(description='Generate RL coding tasks')
    parser.add_argument('--pattern', default='all',
                        help='Bug pattern to use (or "all")')
    parser.add_argument('--count', type=int, default=3,
                        help='Number of tasks to generate per template')
    parser.add_argument('--output', default='tasks/generated',
                        help='Output directory')
    parser.add_argument('--list-patterns', action='store_true',
                        help='List available patterns and exit')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    if args.list_patterns:
        print("Available bug patterns:")
        for name, pat in PATTERNS.items():
            print(f"  {name:20s} [{pat.difficulty}] {pat.description}")
            for t in pat.templates:
                print(f"    - {t.__name__}: {t.__doc__.strip()}")
        return

    random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    patterns = list(PATTERNS.values()) if args.pattern == 'all' else [PATTERNS[args.pattern]]
    generated = []

    for pattern in patterns:
        for template_fn in pattern.templates:
            for variant in range(args.count):
                task_name = generate_task(pattern, template_fn, variant, output_dir)
                generated.append(task_name)
                print(f"Generated: {task_name}")

    print(f"\nTotal: {len(generated)} tasks in {output_dir}/")


if __name__ == '__main__':
    main()

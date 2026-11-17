FROM python:3.11.7-slim

RUN pip install --no-cache-dir pytest==7.4.4

RUN mkdir -p /app /logs/verifier

# Buggy paginator — has 3 off-by-one errors
COPY <<'EOF' /app/paginator.py
def paginate(items, page, page_size):
    """Return a single page of items from the list.

    Args:
        items: List of items to paginate
        page: 1-indexed page number
        page_size: Number of items per page (must be positive)

    Returns:
        List of items for the requested page, or empty list if out of range.

    Raises:
        ValueError: If page_size is not a positive integer.
    """
    if page_size <= 0:
        raise ValueError("page_size must be a positive integer")

    if not items:
        return []

    total_pages = len(items) // page_size  # BUG 1: doesn't account for remainder

    if page < 1 or page > total_pages:
        return []

    start = (page - 1) * page_size
    end = start + page_size + 1  # BUG 2: off-by-one on slice end

    return items[start:end]


def get_total_pages(items, page_size):
    """Return the total number of pages."""
    if page_size <= 0:
        raise ValueError("page_size must be a positive integer")
    if not items:
        return 0
    return len(items) // page_size  # BUG 3: same remainder issue
EOF

COPY <<'EOF' /app/test_paginator.py
import pytest
from paginator import paginate, get_total_pages


class TestPaginate:
    def test_first_page(self):
        items = list(range(1, 11))
        assert paginate(items, 1, 3) == [1, 2, 3]

    def test_middle_page(self):
        items = list(range(1, 11))
        assert paginate(items, 2, 3) == [4, 5, 6]

    def test_last_page_partial(self):
        """The last page should contain only the remaining items."""
        items = list(range(1, 11))
        assert paginate(items, 4, 3) == [10]

    def test_last_page_full(self):
        items = list(range(1, 13))
        assert paginate(items, 4, 3) == [10, 11, 12]

    def test_single_item_pages(self):
        items = ["a", "b", "c"]
        assert paginate(items, 2, 1) == ["b"]

    def test_page_size_equals_length(self):
        items = [1, 2, 3]
        assert paginate(items, 1, 3) == [1, 2, 3]

    def test_page_size_larger_than_length(self):
        items = [1, 2, 3]
        assert paginate(items, 1, 10) == [1, 2, 3]

    def test_out_of_range_high(self):
        items = list(range(10))
        assert paginate(items, 100, 3) == []

    def test_out_of_range_zero(self):
        items = list(range(10))
        assert paginate(items, 0, 3) == []

    def test_out_of_range_negative(self):
        items = list(range(10))
        assert paginate(items, -1, 3) == []

    def test_empty_list(self):
        assert paginate([], 1, 5) == []

    def test_invalid_page_size_zero(self):
        with pytest.raises(ValueError):
            paginate([1], 1, 0)

    def test_invalid_page_size_negative(self):
        with pytest.raises(ValueError):
            paginate([1], 1, -5)

    def test_large_dataset(self):
        items = list(range(1, 1001))
        page = paginate(items, 50, 20)
        assert page == list(range(981, 1001))
        assert len(page) == 20

    def test_consistency_across_all_pages(self):
        """All items should appear exactly once across all pages."""
        items = list(range(1, 18))
        page_size = 5
        total = get_total_pages(items, page_size)
        all_items = []
        for p in range(1, total + 1):
            all_items.extend(paginate(items, p, page_size))
        assert all_items == items


class TestGetTotalPages:
    def test_exact_division(self):
        assert get_total_pages(list(range(12)), 3) == 4

    def test_remainder(self):
        assert get_total_pages(list(range(10)), 3) == 4

    def test_single_item(self):
        assert get_total_pages([1], 5) == 1

    def test_empty(self):
        assert get_total_pages([], 5) == 0

    def test_invalid_page_size(self):
        with pytest.raises(ValueError):
            get_total_pages([1], 0)
EOF

WORKDIR /app
EOF

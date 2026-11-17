#!/bin/bash
# Oracle solution — fixes all 3 off-by-one bugs in paginator.py

cat > /app/paginator.py << 'PYEOF'
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

    total_pages = (len(items) + page_size - 1) // page_size  # ceiling division

    if page < 1 or page > total_pages:
        return []

    start = (page - 1) * page_size
    end = start + page_size  # correct slice end

    return items[start:end]


def get_total_pages(items, page_size):
    """Return the total number of pages."""
    if page_size <= 0:
        raise ValueError("page_size must be a positive integer")
    if not items:
        return 0
    return (len(items) + page_size - 1) // page_size  # ceiling division
PYEOF

# Fix the Off-By-One Bug

The file `/app/paginator.py` contains a `paginate()` function that splits a list of items into pages. Users are reporting that:

1. The last page sometimes has an extra empty entry
2. Requesting the last valid page number returns an empty list instead of the remaining items
3. Page numbers start at 1 (not 0), but something is wrong with the boundary math

Your task: **Fix the `paginate()` function so all tests pass.**

You may only modify `/app/paginator.py`. Do not modify the tests.

## Constraints

- Page numbers are 1-indexed (page 1 is the first page)
- If `page` is out of range, return an empty list
- If `items` is empty, return an empty list for any page
- `page_size` must be a positive integer; raise `ValueError` otherwise

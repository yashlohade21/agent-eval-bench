# Parse Malformed CSV to Clean JSON

The file `/app/data/input.csv` contains a messy CSV export from a legacy system. It has multiple problems:

1. **Mixed delimiters** — some rows use commas, others use semicolons, some use tabs
2. **Inconsistent quoting** — some fields are double-quoted, some have unescaped quotes inside
3. **Encoding artifacts** — some fields contain `\xa0` (non-breaking space) or BOM markers
4. **Missing fields** — some rows have fewer columns than the header
5. **Duplicate headers** — the header row appears again mid-file
6. **Trailing whitespace** — fields have leading/trailing spaces

Your task: **Write `/app/parse.py`** that reads `/app/data/input.csv` and writes clean JSON to `/app/data/output.json`.

## Output Format

```json
[
  {
    "id": 1,
    "name": "Alice Smith",
    "email": "alice@example.com",
    "age": 30,
    "city": "New York"
  },
  ...
]
```

## Rules

- `id` and `age` must be integers (not strings)
- All string fields must be stripped of whitespace, BOM, and non-breaking spaces
- Skip duplicate header rows
- Skip completely empty rows
- For rows with missing fields, use `null` for missing values
- Output must be valid JSON, pretty-printed with 2-space indent
- Rows must appear in the same order as the input (minus skipped rows)
- Email addresses must be lowercased

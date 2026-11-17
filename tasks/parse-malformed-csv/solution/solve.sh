#!/bin/bash
# Oracle solution for parse-malformed-csv

cat > /app/parse.py << 'PYEOF'
import json
import re

HEADERS = ["id", "name", "email", "age", "city"]


def clean_field(value):
    """Strip whitespace, BOM, and non-breaking spaces."""
    if value is None:
        return None
    # Remove BOM and non-breaking spaces
    value = value.replace('\ufeff', '').replace('\xa0', ' ')
    # Strip whitespace
    value = value.strip()
    # Remove surrounding quotes
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    # Handle escaped quotes
    value = value.replace('""', '"')
    return value


def detect_delimiter(line):
    """Detect whether the line uses comma, semicolon, or tab."""
    # Count potential delimiters outside quotes
    in_quote = False
    counts = {',': 0, ';': 0, '\t': 0}
    for ch in line:
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote and ch in counts:
            counts[ch] += 1
    # Pick the delimiter with the highest count
    return max(counts, key=counts.get)


def split_row(line, delimiter):
    """Split a CSV line respecting quoted fields."""
    fields = []
    current = []
    in_quote = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quote and i + 1 < len(line) and line[i + 1] == '"':
                current.append('"')
                i += 2
                continue
            in_quote = not in_quote
            current.append(ch)
        elif ch == delimiter and not in_quote:
            fields.append(''.join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    fields.append(''.join(current))
    return fields


def is_header_row(fields):
    """Check if this row is a duplicate header."""
    cleaned = [clean_field(f).lower() for f in fields if f.strip()]
    return cleaned == [h.lower() for h in HEADERS]


def parse_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    records = []
    first_header_seen = False

    for line in lines:
        line = line.rstrip('\n').rstrip('\r')

        # Skip empty lines
        if not line.strip():
            continue

        delimiter = detect_delimiter(line)
        fields = split_row(line, delimiter)

        # Skip header rows
        if is_header_row(fields):
            if not first_header_seen:
                first_header_seen = True
            continue

        # Clean all fields
        cleaned = [clean_field(f) for f in fields]

        # Build record with proper types
        record = {}
        for i, header in enumerate(HEADERS):
            if i < len(cleaned) and cleaned[i]:
                value = cleaned[i]
                if header in ('id', 'age'):
                    try:
                        value = int(value)
                    except ValueError:
                        value = None
                elif header == 'email':
                    value = value.lower()
                record[header] = value
            else:
                record[header] = None

        records.append(record)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    parse_csv('/app/data/input.csv', '/app/data/output.json')
PYEOF

python /app/parse.py

FROM python:3.11.7-slim

RUN mkdir -p /app/data /logs/verifier

# Create the malformed CSV input file
# This file has: mixed delimiters, bad quoting, encoding issues,
# missing fields, duplicate headers, trailing whitespace
COPY <<'EOF' /app/create_input.py
import os

# Write raw bytes to control encoding precisely
data = b'\xef\xbb\xbfid,name,email,age,city\n'  # BOM at start
data += b'1, Alice Smith , ALICE@EXAMPLE.COM , 30, New York\n'
data += b'2; Bob Johnson ;bob@example.com; 28; Los Angeles\n'
data += b'3\t"Charlie Brown"\tcharlie@example.com\t35\tChicago\n'
data += b'4, "Diana, Prince" , diana@example.com , 25, "San Francisco"\n'
data += b'\n'  # empty row
data += b'id,name,email,age,city\n'  # duplicate header
data += b'5, Eve\xc2\xa0Wilson , eve@example.com , 42, Seattle\n'  # non-breaking space
data += b'6, Frank Miller , frank@EXAMPLE.COM\n'  # missing age and city
data += b'7; Grace "Hopper" Lee ;grace@example.com; 31; Boston\n'  # unescaped quotes
data += b'  8  , Harry   Potter , harry@example.com , 22 , London  \n'  # extra whitespace
data += b'9,Ivy Chen,ivy@example.com,29,\n'  # empty last field
data += b'10, "Jack ""The Man"" Davis" , jack@example.com , 38, Miami\n'  # escaped quotes

os.makedirs('/app/data', exist_ok=True)
with open('/app/data/input.csv', 'wb') as f:
    f.write(data)

print("Created /app/data/input.csv")
EOF

RUN python /app/create_input.py

# Expected output for the verifier
COPY <<'EOF' /app/data/expected.json
[
  {
    "id": 1,
    "name": "Alice Smith",
    "email": "alice@example.com",
    "age": 30,
    "city": "New York"
  },
  {
    "id": 2,
    "name": "Bob Johnson",
    "email": "bob@example.com",
    "age": 28,
    "city": "Los Angeles"
  },
  {
    "id": 3,
    "name": "Charlie Brown",
    "email": "charlie@example.com",
    "age": 35,
    "city": "Chicago"
  },
  {
    "id": 4,
    "name": "Diana, Prince",
    "email": "diana@example.com",
    "age": 25,
    "city": "San Francisco"
  },
  {
    "id": 5,
    "name": "Eve Wilson",
    "email": "eve@example.com",
    "age": 42,
    "city": "Seattle"
  },
  {
    "id": 6,
    "name": "Frank Miller",
    "email": "frank@example.com",
    "age": null,
    "city": null
  },
  {
    "id": 7,
    "name": "Grace \"Hopper\" Lee",
    "email": "grace@example.com",
    "age": 31,
    "city": "Boston"
  },
  {
    "id": 8,
    "name": "Harry Potter",
    "email": "harry@example.com",
    "age": 22,
    "city": "London"
  },
  {
    "id": 9,
    "name": "Ivy Chen",
    "email": "ivy@example.com",
    "age": 29,
    "city": null
  },
  {
    "id": 10,
    "name": "Jack \"The Man\" Davis",
    "email": "jack@example.com",
    "age": 38,
    "city": "Miami"
  }
]
EOF

WORKDIR /app

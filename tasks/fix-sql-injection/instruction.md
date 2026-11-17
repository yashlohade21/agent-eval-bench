# Fix the SQL Injection Vulnerability

The file `/app/app.py` contains a Flask application with a user search endpoint. The endpoint is vulnerable to SQL injection.

Your task: **Fix the SQL injection vulnerability in `/app/app.py` without breaking any existing functionality.**

## The Vulnerable Endpoint

`GET /api/users/search?q=<query>` — searches users by name or email.

## Requirements

1. The search must still work correctly (partial match, case-insensitive)
2. The fix must use parameterized queries (not string escaping/sanitization)
3. The `/api/users/<id>` endpoint must also be fixed if vulnerable
4. Do not change the database schema or test data
5. Do not add new dependencies
6. The app must still start and respond on port 5000

## What You Can Modify

Only `/app/app.py`. Do not modify tests or the database setup.

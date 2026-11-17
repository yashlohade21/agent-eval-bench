FROM python:3.11.7-slim

RUN pip install --no-cache-dir flask==3.0.0 werkzeug==3.0.1

RUN mkdir -p /app /logs/verifier

# Vulnerable Flask app
COPY <<'APPEOF' /app/app.py
import sqlite3
import os
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = '/app/data/users.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs('/app/data', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL DEFAULT 'user',
        secret_token TEXT
    )''')
    # Seed data
    users = [
        (1, 'Alice Smith', 'alice@example.com', 'admin', 'sk-admin-secret-123'),
        (2, 'Bob Johnson', 'bob@example.com', 'user', 'sk-bob-token-456'),
        (3, 'Charlie Brown', 'charlie@example.com', 'user', 'sk-charlie-token-789'),
        (4, 'Diana Prince', 'diana@example.com', 'moderator', 'sk-diana-token-012'),
        (5, 'Eve Wilson', 'eve@example.com', 'user', 'sk-eve-token-345'),
    ]
    conn.executemany(
        'INSERT OR IGNORE INTO users (id, name, email, role, secret_token) VALUES (?, ?, ?, ?, ?)',
        users
    )
    conn.commit()
    conn.close()


@app.route('/api/users/search')
def search_users():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    db = get_db()
    # VULNERABLE: direct string formatting in SQL query
    sql = f"SELECT id, name, email, role FROM users WHERE name LIKE '%{query}%' OR email LIKE '%{query}%'"
    results = db.execute(sql).fetchall()
    return jsonify([dict(row) for row in results])


@app.route('/api/users/<user_id>')
def get_user(user_id):
    db = get_db()
    # VULNERABLE: direct string interpolation
    sql = f"SELECT id, name, email, role FROM users WHERE id = {user_id}"
    user = db.execute(sql).fetchone()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
APPEOF

# Test suite including exploit tests
COPY <<'TESTEOF' /app/test_app.py
import sqlite3
import json
import pytest
import sys
import os

sys.path.insert(0, '/app')
from app import app, init_db, DATABASE


@pytest.fixture(autouse=True)
def setup_db():
    """Reset database before each test."""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()
    yield
    if os.path.exists(DATABASE):
        os.remove(DATABASE)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestFunctionality:
    """These must still pass after the fix."""

    def test_search_by_name(self, client):
        resp = client.get('/api/users/search?q=Alice')
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'Alice Smith'

    def test_search_by_email(self, client):
        resp = client.get('/api/users/search?q=bob@example')
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'Bob Johnson'

    def test_search_case_insensitive(self, client):
        resp = client.get('/api/users/search?q=alice')
        data = resp.get_json()
        assert len(data) == 1

    def test_search_partial_match(self, client):
        resp = client.get('/api/users/search?q=example.com')
        data = resp.get_json()
        assert len(data) == 5

    def test_search_no_results(self, client):
        resp = client.get('/api/users/search?q=nonexistent')
        data = resp.get_json()
        assert len(data) == 0

    def test_search_empty_query(self, client):
        resp = client.get('/api/users/search?q=')
        data = resp.get_json()
        assert len(data) == 0

    def test_get_user_by_id(self, client):
        resp = client.get('/api/users/1')
        data = resp.get_json()
        assert data['name'] == 'Alice Smith'
        assert data['role'] == 'admin'

    def test_get_user_not_found(self, client):
        resp = client.get('/api/users/999')
        assert resp.status_code == 404

    def test_health(self, client):
        resp = client.get('/api/health')
        assert resp.get_json()['status'] == 'ok'

    def test_search_does_not_expose_secret_token(self, client):
        """Search results must never include secret_token."""
        resp = client.get('/api/users/search?q=Alice')
        data = resp.get_json()
        assert 'secret_token' not in data[0]

    def test_get_user_does_not_expose_secret_token(self, client):
        """User detail must never include secret_token."""
        resp = client.get('/api/users/1')
        data = resp.get_json()
        assert 'secret_token' not in data


class TestSQLInjectionPrevention:
    """These verify the vulnerability is actually fixed."""

    def test_search_union_injection(self, client):
        """UNION-based injection to extract secret_token."""
        payload = "' UNION SELECT id, secret_token, email, role FROM users--"
        resp = client.get(f'/api/users/search?q={payload}')
        data = resp.get_json()
        # Should return no results (the injection should not work)
        for record in data:
            for value in record.values():
                if isinstance(value, str):
                    assert 'sk-' not in value, f"Secret token leaked: {value}"

    def test_search_boolean_injection(self, client):
        """Boolean-based injection to dump all users."""
        payload = "' OR '1'='1"
        resp = client.get(f'/api/users/search?q={payload}')
        data = resp.get_json()
        # A fixed query should treat this as a literal search string
        # and return 0 results (no user has "' OR '1'='1" in their name)
        assert len(data) == 0, f"Boolean injection returned {len(data)} results (expected 0)"

    def test_search_stacked_query_injection(self, client):
        """Stacked query injection to drop table."""
        payload = "'; DROP TABLE users;--"
        resp = client.get(f'/api/users/search?q={payload}')
        # Table should still exist
        conn = sqlite3.connect(DATABASE)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1, "users table was dropped!"

    def test_search_time_based_injection(self, client):
        """Time-based blind injection should not work."""
        import time
        # This would cause a delay if injectable
        payload = "' AND (SELECT CASE WHEN (1=1) THEN RANDOMBLOB(100000000) ELSE 1 END)--"
        start = time.time()
        resp = client.get(f'/api/users/search?q={payload}')
        elapsed = time.time() - start
        assert elapsed < 5, f"Query took {elapsed}s, possible time-based injection"

    def test_get_user_injection(self, client):
        """SQL injection in the get_user endpoint."""
        payload = "1 OR 1=1"
        resp = client.get(f'/api/users/{payload}')
        # Should return 404 or single user, not all users
        if resp.status_code == 200:
            data = resp.get_json()
            # If 200, it should be exactly user 1, not multiple users
            assert isinstance(data, dict), "Should return single user object"
            assert data.get('id') == 1 or resp.status_code == 404

    def test_get_user_union_injection(self, client):
        """UNION injection in get_user to extract secrets."""
        payload = "0 UNION SELECT id, secret_token, email, role FROM users WHERE id=1"
        resp = client.get(f'/api/users/{payload}')
        if resp.status_code == 200:
            data = resp.get_json()
            for value in data.values():
                if isinstance(value, str):
                    assert 'sk-' not in value, f"Secret token leaked via get_user: {value}"

    def test_parameterized_query_used(self, client):
        """Verify the fix uses parameterized queries, not string escaping."""
        with open('/app/app.py', 'r') as f:
            source = f.read()

        # Should not contain f-string or format SQL construction
        import re
        # Check for f-string SQL patterns
        dangerous_patterns = [
            r'f"[^"]*SELECT',
            r'f\'[^\']*SELECT',
            r'"[^"]*SELECT[^"]*"\.format',
            r'"[^"]*SELECT[^"]*" %',
            r"'[^']*SELECT[^']*'\.format",
            r"'[^']*SELECT[^']*' %",
            r'f"[^"]*WHERE',
            r"f'[^']*WHERE",
        ]
        for pattern in dangerous_patterns:
            matches = re.findall(pattern, source, re.IGNORECASE)
            assert len(matches) == 0, (
                f"Found dangerous SQL construction pattern: {pattern} -> {matches}"
            )
TESTEOF

WORKDIR /app

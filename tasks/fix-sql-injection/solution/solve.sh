#!/bin/bash
# Oracle solution — fixes SQL injection using parameterized queries

cat > /app/app.py << 'PYEOF'
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
    sql = "SELECT id, name, email, role FROM users WHERE name LIKE ? OR email LIKE ?"
    param = f"%{query}%"
    results = db.execute(sql, (param, param)).fetchall()
    return jsonify([dict(row) for row in results])


@app.route('/api/users/<user_id>')
def get_user(user_id):
    db = get_db()
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'User not found'}), 404

    sql = "SELECT id, name, email, role FROM users WHERE id = ?"
    user = db.execute(sql, (uid,)).fetchone()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
PYEOF

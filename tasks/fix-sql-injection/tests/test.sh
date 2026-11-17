#!/bin/bash
# Verifier for fix-sql-injection task
# Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt

set -euo pipefail

mkdir -p /logs/verifier

cd /app

# Initialize the database
python -c "from app import init_db; init_db()"

# Run all tests
if python -m pytest test_app.py -v --tb=short -x 2>&1 | tee /logs/verifier/test_output.txt; then
    # Additional static analysis: verify no f-string SQL anywhere
    if grep -Pn 'f["\x27].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE)' /app/app.py; then
        echo "FAIL: Found f-string SQL construction in source" >> /logs/verifier/test_output.txt
        echo 0 > /logs/verifier/reward.txt
        exit 0
    fi

    # Verify parameterized queries are actually used (? placeholders)
    if ! grep -q 'execute.*?' /app/app.py; then
        echo "FAIL: No parameterized queries found" >> /logs/verifier/test_output.txt
        echo 0 > /logs/verifier/reward.txt
        exit 0
    fi

    echo "PASS: All tests passed and code uses parameterized queries" >> /logs/verifier/test_output.txt
    echo 1 > /logs/verifier/reward.txt
else
    echo "FAIL: Tests did not pass" >> /logs/verifier/test_output.txt
    echo 0 > /logs/verifier/reward.txt
fi

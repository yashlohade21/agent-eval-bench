#!/bin/bash
# Verifier for fix-off-by-one task
# Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt

set -euo pipefail

mkdir -p /logs/verifier

cd /app

# Run pytest with strict settings
if python -m pytest test_paginator.py -v --tb=short --strict-markers -x 2>&1 | tee /logs/verifier/test_output.txt; then
    # Additional edge-case checks beyond the test suite
    # Verify no trivial shortcuts (e.g., hardcoded returns)
    LINES=$(wc -l < paginator.py)
    if [ "$LINES" -gt 100 ]; then
        echo "FAIL: Solution is suspiciously long ($LINES lines)" >> /logs/verifier/test_output.txt
        echo 0 > /logs/verifier/reward.txt
        exit 0
    fi

    # Check the function actually uses slicing (not some shortcut)
    if ! grep -q 'items\[' paginator.py; then
        echo "FAIL: Solution doesn't appear to use list slicing" >> /logs/verifier/test_output.txt
        echo 0 > /logs/verifier/reward.txt
        exit 0
    fi

    echo "PASS: All tests passed" >> /logs/verifier/test_output.txt
    echo 1 > /logs/verifier/reward.txt
else
    echo "FAIL: Tests did not pass" >> /logs/verifier/test_output.txt
    echo 0 > /logs/verifier/reward.txt
fi

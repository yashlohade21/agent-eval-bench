# rl-coding-tasks

A Harbor-format RL task collection for evaluating coding agents. Each task provides a reproducible Docker environment, natural language instructions, a deterministic verifier, and an oracle solution.

## Structure

```
tasks/<task-name>/
├── instruction.md         # Agent-visible prompt
├── task.toml              # Metadata, timeouts, difficulty
├── environment/
│   └── Dockerfile         # Reproducible starting state
├── solution/
│   └── solve.sh           # Oracle fix (agent never sees this)
└── tests/
    └── test.sh            # Verifier → writes 1 or 0 to /logs/verifier/reward.txt
```

## Tasks

| Task | Difficulty | Category | Description |
|------|-----------|----------|-------------|
| fix-off-by-one | Easy | Bug Fix | Fix an off-by-one error in a Python pagination function |
| parse-malformed-csv | Medium | Data Processing | Parse malformed CSV with mixed delimiters, encoding issues, and missing fields into clean JSON |
| fix-sql-injection | Hard | Security | Fix a SQL injection vulnerability in a Flask endpoint without breaking functionality |

## Running a Task

```bash
cd tasks/<task-name>
docker build -t task-<name> -f environment/Dockerfile .
docker run --rm -v /logs:/logs task-<name> bash tests/test.sh
```

The verifier writes `1` (pass) or `0` (fail) to `/logs/verifier/reward.txt`.

## Programmatic Generation

```bash
python generate.py --pattern off-by-one --count 10 --output tasks/
```

See `generate.py` for template-based task generation from working code + injected bug patterns.

## Design Principles

1. **Deterministic verifiers** — no flaky tests, no network dependencies
2. **Hard to shortcut** — verifiers test edge cases, not just happy paths
3. **Fully reproducible** — pinned dependencies, no external fetches at runtime
4. **Difficulty signal** — includes tasks that frontier models (GPT-4, Claude) fail on

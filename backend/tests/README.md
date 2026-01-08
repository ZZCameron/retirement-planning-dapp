# Test Suite

## Directory Structure

- **integration/** - API endpoint tests (full stack)
- **unit/** - Pure function tests (calculator logic)
- **scratch/** - Temporary/exploratory tests (not run by CI)

## Running Tests

All commands should be run from: cd backend/tests

Run all tests:
    pytest

Run only integration tests:
    pytest integration/

Run only unit tests:
    pytest unit/

Run specific test file:
    pytest unit/test_calculator_logic.py

Run with verbose output:
    pytest -v

## Test Categories

### Integration Tests
- test_batch_api.py - Batch calculation API endpoints

### Unit Tests
- test_calculator_logic.py - Core calculation math
- Tests pension vs income equivalence
- Validates zero-growth depletion

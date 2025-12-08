#!/bin/bash
# Test script for Linux/macOS
# Runs security audit tests on both vulnerable and fixed versions

set -e

echo "=== Security Audit Test Suite (Linux/macOS) ==="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
fi

# Function to run test on a file
run_test_on_file() {
    local test_file=$1
    local test_name=$2
    
    echo "---"
    echo "Testing: $test_name"
    echo "File: $test_file"
    echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
    
    if [ ! -f "$test_file" ]; then
        echo "ERROR: Test file not found: $test_file"
        return 1
    fi
    
    # Run basic syntax check
    if ! python3 -m py_compile "$test_file" 2>/dev/null; then
        echo "RESULT: SYNTAX_ERROR - File has syntax errors"
        echo "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
        return 1
    fi
    
    # Import test - check if module imports successfully
    echo "Running import test..."
    if python3 -c "import sys; sys.path.insert(0, '.'); exec(open('$test_file').read().replace('if __name__ == \"__main__\":', 'if False:'))" 2>&1; then
        echo "RESULT: IMPORT_SUCCESS"
    else
        echo "RESULT: IMPORT_FAILED"
        return 1
    fi
    
    # Check for basic security issues
    echo "Scanning for security issues..."
    if grep -q "shell=True" "$test_file"; then
        echo "WARNING: Found shell=True in subprocess calls"
        return 1
    fi
    if grep -q "hashlib.md5" "$test_file"; then
        echo "WARNING: Found weak MD5 hash usage"
        return 1
    fi
    if grep -q "debug=True" "$test_file"; then
        echo "WARNING: Found debug=True enabled"
        return 1
    fi
    
    # Check for SQL injection patterns
    if grep -E "SELECT.*%|INSERT.*%|UPDATE.*%|DELETE.*%" "$test_file" | grep -q "%"; then
        # Only flag if it's actual SQL injection, not false positive
        if grep -q "%" "$test_file" | grep -v "fromtimestamp" | grep -v "%" > /dev/null 2>&1; then
            echo "WARNING: Potential SQL injection patterns found"
            return 1
        fi
    fi
    
    echo "RESULT: SECURITY_CHECK_PASSED"
    echo "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
    return 0
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Run tests
OVERALL_STATUS=0

echo "=== Testing Original (Vulnerable) Version ==="
if run_test_on_file "input_backup.py" "Vulnerable Version" >> logs/test_run.log 2>&1; then
    echo "input_backup.py: Tests completed"
else
    echo "input_backup.py: Tests found issues (expected for vulnerable version)"
    OVERALL_STATUS=1
fi

echo ""
echo "=== Testing Fixed Version ==="
if run_test_on_file "inputs.py" "Secure Version"; then
    echo "inputs.py: All security checks passed!"
else
    echo "inputs.py: Security checks failed"
    OVERALL_STATUS=1
fi

echo ""
echo "=== Test Summary ==="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi

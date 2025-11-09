#!/usr/bin/env python3
"""
Test runner for the rust_reconciler adapter.
Ensures Python path is set up correctly and rust_reconciler module is available.
"""

import os
import sys
import unittest

# Add the parent directory to Python path so we can import pythra
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Run all tests in the test_rust_adapter module."""
    # First try to import rust_reconciler to give helpful message if missing
    try:
        import rust_reconciler
        print("✅ rust_reconciler module found")
    except ImportError:
        print("⚠️  rust_reconciler module not found!")
        print("💡 Run 'maturin develop' in the rust_reconciler directory first")
        sys.exit(1)

    # Run the tests
    from pythra.tests.test_rust_adapter import TestRustReconcilerAdapter
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRustReconcilerAdapter)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    run_tests()
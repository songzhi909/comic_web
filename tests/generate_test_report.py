#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simplified test report generator for the Comic Web application.
"""

import unittest
import sys
import os

def run_tests_and_generate_report():
    """Run all tests and generate a simplified report."""
    print("=" * 70)
    print("COMIC WEB APPLICATION - TEST REPORT")
    print("=" * 70)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create a custom test runner that only shows summary
    runner = unittest.TextTestRunner(verbosity=1)
    
    # Run the tests
    result = runner.run(suite)
    
    # Generate simplified report
    print("\nSUMMARY:")
    print("-" * 30)
    print(f"Total tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"Success rate: {success_rate:.2f}%")
    
    # Test result status
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
        status = "PASS"
    else:
        print("\n[FAILURE] Some tests failed!")
        status = "FAIL"
        print(f"\nDetails:")
        if result.failures:
            print(f"- {len(result.failures)} test(s) failed")
        if result.errors:
            print(f"- {len(result.errors)} test(s) had errors")
    
    # Final status
    print("\n" + "=" * 70)
    print(f"FINAL STATUS: {status}")
    print("=" * 70)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests_and_generate_report()
    sys.exit(0 if success else 1)
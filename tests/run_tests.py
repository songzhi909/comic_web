#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test runner script for the Comic Web application.
This script runs all tests and generates a detailed report.
"""

import unittest
import sys
import os
from io import StringIO

def run_tests():
    """Run all tests and generate a report."""
    # Capture stdout to collect test results
    test_output = StringIO()
    runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    result = runner.run(suite)
    
    # Get the output
    output = test_output.getvalue()
    
    # Generate report
    generate_report(result, output)
    
    return result.wasSuccessful()

def generate_report(result, output):
    """Generate a detailed test report."""
    print("=" * 70)
    print("COMIC WEB APPLICATION - TEST REPORT")
    print("=" * 70)
    
    # Summary
    print("\nSUMMARY:")
    print("-" * 30)
    print(f"Total tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0:.2f}%")
    
    # Test result status
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
        status = "PASS"
    else:
        print("\n[FAILURE] Some tests failed!")
        status = "FAIL"
    
    # Detailed output
    print("\nDETAILED OUTPUT:")
    print("-" * 30)
    print(output)
    
    # Failure details
    if result.failures:
        print("\nFAILURE DETAILS:")
        print("-" * 30)
        for test, traceback in result.failures:
            print(f"\nFAILED: {test}")
            print(f"Traceback:\n{traceback}")
    
    # Error details
    if result.errors:
        print("\nERROR DETAILS:")
        print("-" * 30)
        for test, traceback in result.errors:
            print(f"\nERROR in: {test}")
            print(f"Traceback:\n{traceback}")
    
    # Final status
    print("\n" + "=" * 70)
    print(f"FINAL STATUS: {status}")
    print("=" * 70)

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
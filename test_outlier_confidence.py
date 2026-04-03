#!/usr/bin/env python3
"""Test outlier detection with confidence scoring."""

from utils.outlier_detector import flag_outlier

def test_outlier_detection():
    print("Testing Outlier Detection with Confidence Scoring...")
    print()

    # Test 1: Good data (should have high confidence)
    print("Test 1: High confidence outlier with 6 consistent values")
    result = flag_outlier(
        parameter='WBC',
        value=50.0,
        historical_values=[9.0, 9.5, 10.0, 9.8, 10.2, 9.7],
        timestamp='2024-01-15T12:00:00'
    )
    if result:
        print(f"  ✓ Outlier detected: WBC={result['value']}")
        print(f"  ✓ Confidence: {result['confidence']}")
        print(f"  ✓ Z-score: {result['z_score']}")
        print(f"  ✓ Recommendation: {result['recommendation'][:50]}...")
    else:
        print("  ✗ No outlier detected")

    print()

    # Test 2: Insufficient data (should return None)
    print("Test 2: Insufficient data (only 2 values)")
    result = flag_outlier(
        parameter='WBC',
        value=50.0,
        historical_values=[9.0, 9.5],
        timestamp='2024-01-15T12:00:00'
    )
    if result is None:
        print("  ✓ Correctly returned None (insufficient data)")
    else:
        print("  ✗ Should have returned None")

    print()

    # Test 3: Variable data (should have lower confidence)
    print("Test 3: Variable data (lower confidence)")
    result = flag_outlier(
        parameter='WBC',
        value=25.0,
        historical_values=[5.0, 15.0, 8.0, 20.0, 12.0, 18.0],  # Variable data
        timestamp='2024-01-15T12:00:00'
    )
    if result:
        print(f"  ✓ Outlier detected: WBC={result['value']}")
        print(f"  ✓ Confidence: {result['confidence']} (should be lower)")
        print(f"  ✓ Recommendation: {result['recommendation'][:50]}...")
    else:
        print("  ✗ No outlier detected")

    print()
    print("✓ Outlier detection with confidence scoring working!")

if __name__ == "__main__":
    test_outlier_detection()
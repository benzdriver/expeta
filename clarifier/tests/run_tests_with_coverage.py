#!/usr/bin/env python3
"""
Run Clarifier tests with coverage report
"""

import subprocess
import sys
from pathlib import Path

def run_tests_with_coverage():
    """Run pytest with coverage for clarifier module"""
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    clarifier_root = project_root / "clarifier"
    
    # Install coverage if not installed
    try:
        import coverage
    except ImportError:
        print("Installing coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], check=True)
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "coverage", "run",
        "--source", str(clarifier_root / "core"),
        "--omit", "*/tests/*,*/__pycache__/*",
        "-m", "pytest",
        str(clarifier_root / "tests"),
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    print(f"Running tests with coverage...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(project_root))
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("TESTS PASSED! Generating coverage report...")
        print("="*60 + "\n")
        
        # Generate coverage report
        subprocess.run([
            sys.executable, "-m", "coverage", "report",
            "--show-missing",
            "--skip-covered",
            "--precision=2"
        ], cwd=str(project_root))
        
        # Generate HTML report
        subprocess.run([
            sys.executable, "-m", "coverage", "html",
            "--directory", str(clarifier_root / "tests" / "htmlcov")
        ], cwd=str(project_root))
        
        print(f"\nHTML coverage report generated at: {clarifier_root / 'tests' / 'htmlcov' / 'index.html'}")
        
        # Show coverage summary
        subprocess.run([
            sys.executable, "-m", "coverage", "report",
            "--format=total"
        ], cwd=str(project_root))
        
    else:
        print("\n" + "="*60)
        print("TESTS FAILED!")
        print("="*60)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())
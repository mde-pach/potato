"""Pytest configuration and shared fixtures for all tests.

This module imports all fixtures from the fixtures package to make them
available to all tests.
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Tuple

import pytest
from mypy import api

# Register fixture modules with pytest
# This ensures pytest discovers all fixtures in these modules
pytest_plugins = [
    "tests.fixtures.aggregates",
    "tests.fixtures.classes",
    "tests.fixtures.prices",
    "tests.fixtures.products",
    "tests.fixtures.users",
]

# Import domain classes for convenience
from .fixtures.domains import Buyer, Order, Price, Product, Seller, User  # noqa: E402

__all__ = [
    "Buyer",
    "Order",
    "Price",
    "Product",
    "Seller",
    "User",
]


# ============================================================================
# Mypy Plugin Testing Fixtures
# ============================================================================

@pytest.fixture
def run_mypy_on_code():
    """
    Fixture that returns a function to run mypy on a code string.
    
    Returns:
        A function that takes code and returns (stdout, stderr, exit_code).
    """
    def _run(code: str) -> Tuple[str, str, int]:
        """Run mypy on a string of code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            fname = f.name
            
        try:
            config = """
[mypy]
plugins = potato.mypy
check_untyped_defs = True
"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as cfg:
                cfg.write(config)
                cfg_name = cfg.name
                
            try:
                args = [
                    fname,
                    '--config-file', cfg_name,
                    '--show-traceback',
                    '--no-incremental',
                    '--hide-error-context',
                    '--no-error-summary'
                ]
                
                # Add current directory to python path for mypy to find potato
                os.environ['MYPYPATH'] = os.getcwd() + "/src"
                
                result = api.run(args)
                return result
            finally:
                os.unlink(cfg_name)
        finally:
            os.unlink(fname)
    
    return _run


@pytest.fixture
def assert_mypy_output(run_mypy_on_code):
    """
    Fixture that returns a function to assert mypy output.
    
    Returns:
        A function that takes code and expected errors/clean flag and asserts.
    """
    def _assert(code: str, expected_errors: List[str] = None, expected_clean: bool = False):
        """Assert that running mypy on the code produces the expected errors."""
        stdout, stderr, exit_code = run_mypy_on_code(code)
        
        output = stdout + stderr
        
        if expected_clean:
            if exit_code != 0:
                raise AssertionError(f"Expected no errors, but got exit code {exit_code}.\nOutput:\n{output}")
            return

        if expected_errors:
            missing = []
            for error in expected_errors:
                if error not in output:
                    missing.append(error)
            
            if missing:
                raise AssertionError(
                    f"Missing expected errors: {missing}\n"
                    f"Actual output:\n{output}"
                )
    
    return _assert

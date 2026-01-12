"""
Tests for the MoCoM main module.
"""

import sys
import os

# Add parent directory to path to import src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import __version__, __authors__, main


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_authors():
    """Test that authors are defined."""
    assert isinstance(__authors__, list)
    assert len(__authors__) == 2
    assert "Timothée POULY" in __authors__
    assert "Célestin GABORIAU" in __authors__


def test_main_runs():
    """Test that main function runs without error."""
    try:
        main()
        assert True
    except Exception as e:
        assert False, f"main() raised an exception: {e}"

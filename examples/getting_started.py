"""
Example: Getting Started with MoCoM

This example demonstrates the basic usage of the MoCoM project.
"""

import sys
import os

# Add parent directory to path to import src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import __version__, __authors__


def main():
    """Run the example."""
    print("=" * 50)
    print("MoCoM Project - Getting Started Example")
    print("=" * 50)
    print(f"\nVersion: {__version__}")
    print(f"Authors: {', '.join(__authors__)}")
    print("\nThis is a basic example of the MoCoM project.")
    print("More examples will be added as the project develops.")
    print("=" * 50)


if __name__ == "__main__":
    main()

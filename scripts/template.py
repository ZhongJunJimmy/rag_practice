"""
Template for scripts in the scripts/ directory

Usage:
1. Copy this file to create new scripts
2. Replace the content with your script logic
3. Keep the setup_path() call at the top
"""

try:
    from _common import setup_path
except ImportError:
    from scripts._common import setup_path

setup_path()

# Now you can import from the main package
# from services.xxx import xxx
# from libs.xxx import xxx

def main():
    print("Script template - replace with your logic")

if __name__ == "__main__":
    main()
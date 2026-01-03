# Remove unused imports
autoflake --in-place --remove-all-unused-imports --recursive .

# Fix PEP8 formatting (whitespaces, newlines, etc.)
autopep8 --in-place --recursive .

# Run flake8 to check if anything is left
flake8 .
# ./fix_code.ps1 to run 

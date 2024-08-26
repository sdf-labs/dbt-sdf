import re
import sys

def update_config(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Replace the deprecated Extra configuration with the new string literal
    content = re.sub(r'extra = Extra\.([a-z]+)', r"extra = '\1'", content)

    with open(file_path, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cleanup_codegen_output.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    if not file_path.endswith('.py'):
        print("Error: The provided file is not a Python file.")
        sys.exit(1)
    
    try:
        update_config(file_path)
        print(f"Cleanup completed for {file_path}")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
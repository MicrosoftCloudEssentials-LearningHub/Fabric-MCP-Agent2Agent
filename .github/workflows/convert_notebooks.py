#!/usr/bin/env python3
"""
Notebook to GitHub-Compatible Format Converter

This script fixes Jupyter notebooks for GitHub rendering by:
1. Converting XML-format notebooks to standard Jupyter JSON format
2. Cleaning widget metadata that can cause GitHub rendering issues
"""

import os
import json
import re
import nbformat
from nbformat.validator import validate

def process_notebooks(directory="."):
    """Find and process all notebook files in the repository"""
    notebook_files = []
    print(f"Searching for notebooks in directory: {directory}")
    for root, dirs, files in os.walk(directory):
        # Skip directories that should be excluded
        if '.git' in dirs:
            dirs.remove('.git')  # Skip git directory
        if '.github' in dirs:
            dirs.remove('.github')  # Skip GitHub directory
        if '.venv' in dirs:
            dirs.remove('.venv')  # Skip virtual environments
        
        for file in files:
            if file.endswith('.ipynb'):
                notebook_path = os.path.join(root, file)
                print(f"Found notebook: {notebook_path}")
                notebook_files.append(notebook_path)
    
    print(f"Found {len(notebook_files)} notebooks to process")
    
    success_count = 0
    for nb_path in notebook_files:
        if convert_notebook(nb_path):
            success_count += 1
    
    print(f"Successfully rendered {success_count} out of {len(notebook_files)} notebooks")
    return success_count

def convert_notebook(filepath):
    """Convert a notebook to GitHub-compatible format by cleaning widget metadata"""
    print(f"\nProcessing {filepath}")
    
    try:
        # Read the notebook content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is a XML notebook
        if '<VSCode.Cell' in content:
            print(f"  Converting from XML format...")
            # Extract cells using regex
            cells = []
            cell_pattern = re.compile(r'<VSCode\.Cell.*?language="(.*?)".*?>(.*?)</VSCode\.Cell>', re.DOTALL)
            
            matches = list(cell_pattern.finditer(content))
            if not matches:
                print(f"  WARNING: No cells found in {filepath}")
                return False
                
            print(f"  Found {len(matches)} cells")
            
            for match in matches:
                cell_type, cell_content = match.groups()
                
                if cell_type == "markdown":
                    cells.append(nbformat.v4.new_markdown_cell(
                        source=cell_content.strip()
                    ))
                else:  # python, javascript, etc.
                    cells.append(nbformat.v4.new_code_cell(
                        source=cell_content.strip()
                    ))
            
            # Create a new notebook
            nb = nbformat.v4.new_notebook()
            nb.cells = cells
            
            # Add required metadata
            nb.metadata = {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.8.10"
                },
                # Add empty widget state to prevent GitHub rendering issues
                "widgets": {
                    "application/vnd.jupyter.widget-state+json": {
                        "state": {},
                        "version_major": 2,
                        "version_minor": 0
                    }
                }
            }
            
            # Validate and write the notebook
            validate(nb)
            with open(filepath, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
            
            print(f"  Successfully rendered {filepath} for GitHub compatibility")
            return True
        
        else:
            # It's already in JSON format, clean widget metadata
            try:
                notebook = json.loads(content)
                print(f"  Cleaning widget metadata...")
                
                # Remove potentially problematic widget state but keep proper structure
                if 'metadata' in notebook:
                    # Replace with clean widget state
                    notebook['metadata']['widgets'] = {
                        "application/vnd.jupyter.widget-state+json": {
                            "state": {},
                            "version_major": 2,
                            "version_minor": 0
                        }
                    }
                
                # Clean widget metadata from cells as well
                for cell in notebook.get('cells', []):
                    if 'metadata' in cell and 'widgets' in cell['metadata']:
                        del cell['metadata']['widgets']
                
                # Write the cleaned notebook
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(notebook, f, indent=2)
                
                print(f"  Successfully cleaned {filepath} for GitHub compatibility")
                return True
                
            except json.JSONDecodeError:
                print(f"  ERROR: {filepath} is not in valid JSON format or XML format")
                return False
    
    except Exception as e:
        print(f"  ERROR processing {filepath}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Rendering notebooks for GitHub compatibility...")
    # Get the repository root directory from environment variable if available
    repo_root = os.environ.get('GITHUB_WORKSPACE', '.')
    print(f"Repository root: {repo_root}")
    process_notebooks(repo_root)

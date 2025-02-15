
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import shutil

def process_directory():
    # Setup Jinja environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Variables available in all templates
    global_vars = {
        'year': datetime.now().year,
    }

    # Create output directory if it doesn't exist
    os.makedirs('public', exist_ok=True)

    # Walk through all files in templates directory
    for root, _, files in os.walk('templates'):
        for file in files:
            # Get full path and make it relative to templates dir
            template_path = os.path.join(root, file)
            relative_path = os.path.relpath(template_path, 'templates')
            
            # Create corresponding output directory
            output_dir = os.path.join('public', os.path.dirname(relative_path))
            os.makedirs(output_dir, exist_ok=True)
            
            # Full path for output file
            output_path = os.path.join('public', relative_path)
            
            # Process HTML files with Jinja
            if file.endswith(('.html', '.htm')):
                try:
                    # Load template relative to templates directory
                    template = env.get_template(relative_path)
                    
                    # Render template
                    output = template.render(**global_vars)
                    
                    # Write rendered template to file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(output)
                    print(f"Processed: {relative_path}")
                except Exception as e:
                    print(f"Error processing {relative_path}: {str(e)}")
            
            # Copy non-HTML files directly
            else:
                shutil.copy2(template_path, output_path)
                print(f"Copied: {relative_path}")

if __name__ == "__main__":
    process_directory()
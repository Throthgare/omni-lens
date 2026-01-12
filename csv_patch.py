#!/usr/bin/env python3
"""
This script patches commit_gather_script.py to add the generate_csv_report function.
"""
import re

# Read the original file
with open('commit_gather_script.py', 'r') as f:
    content = f.read()

# The new function to add
new_function = '''
def generate_csv_report(output: Dict, output_type: str = 'commits') -> str:
    """Generate a CSV report from analysis output.
    
    Args:
        output: The analysis output dictionary
        output_type: Type of data to export ('commits', 'classes', 'all')
    
    Returns:
        CSV formatted string
    """
    csv_lines = []
    
    if output_type in ('commits', 'all'):
        # Export commits to CSV
        csv_lines.append("hash,author,date,category,scope,message,is_breaking,insertions,deletions,files_changed")
        for commit in output.get('history', []):
            date_str = commit.get('date', '')
            if isinstance(date_str, str) and 'T' in date_str:
                date_str = date_str.split('T')[0]
            csv_lines.append(
                f"{commit.get('hash', '')},"
                f"{commit.get('author_name', '')},"
                f"{date_str},"
                f"{commit.get('category', '')},"
                f"{commit.get('scope', '') or ''},"
                f'"' + commit.get("message", "").replace('"', '""') + '",'
                f"{commit.get('is_breaking', False)},"
                f"{commit.get('insertions', 0)},"
                f"{commit.get('deletions', 0)},"
                f"{commit.get('files_changed', 0)}"
            )
    
    if output_type in ('classes', 'all'):
        # Add blank line between sections if exporting all
        if output_type == 'all' and csv_lines:
            csv_lines.append("")
        
        # Export classes to CSV
        csv_lines.append("name,file_path,line_number,class_type,language,is_test,complexity,methods_count")
        
        for cls in output.get('classes', []):
            methods_count = len(cls.get('methods', []))
            csv_lines.append(
                f"{cls.get('name', '')},"
                f"{cls.get('file_path', '')},"
                f"{cls.get('line_number', 0)},"
                f"{cls.get('class_type', '')},"
                f"{cls.get('language', '')},"
                f"{cls.get('is_test', False)},"
                f"{cls.get('complexity', 0)},"
                f"{methods_count}"
            )
    
    return "\\n".join(csv_lines)
'''

# Find the pattern to replace
pattern = r'(    return "\\n"\.join\(lines\)\n\n)(def parse_relative_date)'

# Replace with new function + original function
replacement = r'\1' + new_function + '\n\n\2'

# Apply the patch
new_content = re.sub(pattern, replacement, content)

# Write the patched file
with open('commit_gather_script.py', 'w') as f:
    f.write(new_content)

print("Patched commit_gather_script.py with generate_csv_report function")


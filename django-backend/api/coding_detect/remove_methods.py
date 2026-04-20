import ast
import os

file_path = r"d:\anyworkspace\quanzhan\django-backend\api\coding_detect\detector.py"
methods_to_remove = {
    "_extract_json_from_output",
    "_parse_json_result",
    "_parse_result",
    "_smart_vulnerability_check",
    "_validate_cwe_with_code",
    "_extract_final_vuln_type_from_reasoning",
    "_calculate_confidence",
    "_validate_cwe_for_language",
    "_generate_fix_suggestion",
    "_map_severity",
    "_optimize_code_conservative",
    "_estimate_tokens",
    "_smart_truncate_code",
    "_split_code_by_functions",
    "_add_context"
}

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)
lines = source.splitlines()

ranges = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in methods_to_remove:
        start_line = node.decorator_list[0].lineno if node.decorator_list else node.lineno
        end_line = getattr(node, 'end_lineno', -1)
        if end_line != -1:
            ranges.append((start_line - 1, end_line))

# Sort ranges in descending order to delete from bottom to top
ranges.sort(key=lambda x: x[0], reverse=True)

for start, end in ranges:
    print(f"Removing method at lines {start+1}-{end}")
    del lines[start:end]

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write('\n'.join(lines) + '\n')

print(f"Successfully processed. Removed {len(ranges)} methods.")

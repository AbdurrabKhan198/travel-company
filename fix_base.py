import re

file_path = r'c:\Users\hp\Desktop\clients\travel company\Travel_agency\templates\base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix split template tags by joining lines with unclosed braces
lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Count open and close braces/tags
    open_braces = line.count('{{')
    close_braces = line.count('}}')
    open_tags = line.count('{%')
    close_tags = line.count('%}')
    
    if open_braces > close_braces or open_tags > close_tags:
        # Join with next lines until balanced
        combined = line.rstrip()
        i += 1
        
        while i < len(lines):
            next_line = lines[i].strip()
            combined = combined + ' ' + next_line
            
            # Check if now balanced
            if combined.count('{{') <= combined.count('}}') and combined.count('{%') <= combined.count('%}'):
                break
            i += 1
        
        new_lines.append(combined)
        i += 1
    else:
        new_lines.append(line)
        i += 1

# Also fix the pattern where {% if %} <div is on same line
result = '\n'.join(new_lines)

# Fix the specific issue: {% if ... %} <div should have newline between them
result = re.sub(r'(%\})\s*(<div)', r'\1\n                                \2', result)

# Write the file back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(result)

print('Fixed all split template tags and formatting!')

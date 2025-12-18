import re

# Read the file
file_path = r'c:\Users\hp\Desktop\clients\travel company\Travel_agency\templates\base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Process the file line by line and join split template tags
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if line has an unclosed {{ 
    open_braces = line.count('{{')
    close_braces = line.count('}}')
    
    if open_braces > close_braces:
        # This line has an unclosed {{ - need to join with next line(s)
        combined = line.rstrip()
        i += 1
        while i < len(lines) and combined.count('{{') > combined.count('}}'):
            combined = combined + ' ' + lines[i].strip()
            i += 1
        new_lines.append(combined + '\n')
    else:
        # Check if line has an unclosed {% 
        open_tags = line.count('{%')
        close_tags = line.count('%}')
        
        if open_tags > close_tags:
            # This line has an unclosed {% - need to join with next line(s)
            combined = line.rstrip()
            i += 1
            while i < len(lines) and combined.count('{%') > combined.count('%}'):
                combined = combined + ' ' + lines[i].strip()
                i += 1
            new_lines.append(combined + '\n')
        else:
            new_lines.append(line)
            i += 1

# Join and write the file
content = ''.join(new_lines)

# Write the file back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Template fixed - all split tags joined!')

import fitz
import re

doc = fitz.open('resources/PDFDataExtract.pdf')

def extract_code_and_description(input_string):
    match = re.search(r"([A-Z]\d{4}) – (.+)", input_string)
    
    if match:
        return match.group(1), match.group(2)
    else:
        '', ''

all_blocks = []

for page in doc:
    blocks = page.get_text('blocks')
    for i, block in enumerate(blocks):
        x, y, x1, y1, text, _, _ = block
        if(x < 100): # beyond (100, _) is the second column "What you must pay whenyou get these services". Ignore entirely.
            if('• \nD' in text or 'per year' in text or 'each year' in text or 'per calendar year' in text):
                all_blocks.append(text) # we only care about dental codes and visits. Visits are identified by "***year" phrasing - brittle logic.
        if('Optional supplemental package 2 – Dental and vision package' in text):
            break #ignore supplemental package 2 section completely
            

dental_info = {}
visits = ''        
for text in all_blocks:
    if('per year' in text or 'each year' in text or 'per calendar year' in text):
        visits = text
    if  '• \nD' in text:
        code, description = extract_code_and_description(text)
        dental_info[code] = {"description": description, "visits": visits}

from tabulate import tabulate

def print_table(dental_info):
    table_data = []
    for code, info in dental_info.items():
        row = [code, info["description"], info["visits"].strip()]
        table_data.append(row)
    headers = ["Dental Code", "Description", "Visits"]
    table = tabulate(table_data, headers=headers, tablefmt="grid")

    print(table)

print_table(dental_info)
    

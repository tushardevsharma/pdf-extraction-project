import fitz
import openai

doc = fitz.open('resources/PDFDataExtract.pdf') # open the PDF file

text = ''
# only get texts of interest; entire text is too large for the gpt-3.5 context window
for page in doc:
    # Get the blocks of text
    blocks = page.get_text('blocks')
    # Iterate over the blocks
    for i, block in enumerate(blocks):
        x, y, x1, y1, line, _, _ = block
        if(x < 100): # brittle-code alert! Using pdf co-ordinates to ignore the second coloum of the table
            text += line + ' '
        if('Optional supplemental package 2 – Dental and vision package' in line): #ignore supplemental package 2 section completely
            break

prompt = f'''
You are an expert at reading medical benefits plans and are working with an benefits document from a vendor.

Specifically for "Optional supplemental package 1 – Preventive dental package",
can you give me the data of which dental codes (along with their description) have how many visits.
For visits include all the details/phrasing "as-is" from the document.
E.g. - "Two oral exams each year" or "Two cleanings per year" or 
"Dental X-rays include one full-mouth or panoramic X-ray and
one set/series of bitewing X-rays each year and up to seven
periapical images per calendar year". Include the full phrasing.
Return the answer in the following json format:
{{
    'D0120':
        {{'description': 'Periodic oral evaluation – established patient', 'visits': 'Two oral exams each year (from the following codes):\n'}}
}}

Do not infer any data based on previous training, strictly use only source text given above as input.
The text is from two pages from a pdf (page number 115 and 116).
'''
openai_input = text + prompt

openai.api_key = '<your-api-key-here>'
completion = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0,
    seed=3241,
    messages=[{"role": "user", "content": openai_input}])
gpt_response = completion.choices[0].message.content

import json
from tabulate import tabulate

data_dict = json.loads(gpt_response.replace("'", '"'))
table = [[key] + list(value.values()) for key, value in data_dict.items()]
headers = ['Dental Code', 'Description', 'Visits']
print(tabulate(table, headers, tablefmt='pipe'))

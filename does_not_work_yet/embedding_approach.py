import fitz
from openai import OpenAI # for calling the OpenAI API
import pandas as pd  # for storing text and embeddings data
import tiktoken  # for counting tokens
import os # for getting API token from env variable OPENAI_API_KEY
from scipy import spatial  # for calculating vector similarities for search

EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"
BATCH_SIZE = 100  # you can submit up to 2048 embedding inputs per request

doc = fitz.open('resources/PDFDataExtract.pdf')
client = OpenAI(api_key='<your-api-key-here>')

pdf_data = []
for page in doc:
    # Get the blocks of text
    blocks = page.get_text('blocks')
    for block in blocks:
        _, _, _, _, line, _, _ = block
        pdf_data.append(line)

embeddings = []
for batch_start in range(0, len(pdf_data), BATCH_SIZE):
    batch_end = batch_start + BATCH_SIZE
    batch = pdf_data[batch_start:batch_end]
    print(f"Batch {batch_start} to {batch_end-1}")
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
    for i, be in enumerate(response.data):
        assert i == be.index  # double check embeddings are in same order as input
    batch_embeddings = [e.embedding for e in response.data]
    embeddings.extend(batch_embeddings)

df = pd.DataFrame({"text": pdf_data, "embedding": embeddings})

# search function
def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatednesses = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:top_n], relatednesses[:top_n]


def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def query_message(
    query: str,
    df: pd.DataFrame,
    model: str,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings, relatednesses = strings_ranked_by_relatedness(query, df)
    introduction = f'''
                You are an expert at reading medical benefits plans and are working with a benefits document from a vendor.
                Do not infer any data based on previous training, strictly use only source text given below as input.
                '''
    question = f"\n\nQuestion: {query}"
    message = introduction
    for string in strings:
        next_article = f'\nNext relevant section:\n"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question

def ask(
    query: str,
    df: pd.DataFrame = df,
    model: str = GPT_MODEL,
    token_budget: int = 4096 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, df, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "You answer questions about medical health documents. Be as helpful as possible."},
        {"role": "user", "content": message},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        seed=3241
    )
    response_message = response.choices[0].message.content
    return response_message

import json
from tabulate import tabulate

def print_as_table(gpt_response):
    data_dict = json.loads(gpt_response.replace("'", '"'))
    table = [[key] + list(value.values()) for key, value in data_dict.items()]
    headers = ['Dental Code', 'Description', 'Visits']
    print(tabulate(table, headers, tablefmt='pipe'))

print_as_table(ask('''
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
    '''))
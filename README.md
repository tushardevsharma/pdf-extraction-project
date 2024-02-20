### Problem Statement
Dental Benefit is a key benefit in Medicare Domain. Detailed Dental Benefits data can be found in EOC( Insurance Plan Document listing all the benefits details covered by plan in detailed manner).
This Dental Data consists of Dental Codes, Description of Dental Code, Copay/Coinsurance(Cost of benefit) and Visits(Quantity of benefit) information present in structured, semi- structured or 
unstructured manner inside the EOC pdf.

[PDFDataExtract.pdf](resources/PDFDataExtract.pdf) contains semi-structured/unstructured Dental Data. The assignment is to use the pdf to generate an output similar to FinalOutput_PDFDataExtract.xlsx using any technical means.

#### Few Pointers to Note:

- Data to Extract:-
  - Dental Code(Highlighted in Green in Pdf and output excel)
  - Description( Highlighted in blue in pdf and output excel)
  - Visits (Highlighted in Yellow in pdf and excel)
- Data to be extracted just for Optional Supplemental Package 1( Ignore the Optional Supplemental package 2 present in 2nd Page)
- In Optional Supplemental Package 1 Table, please ignore the right column( What you must pay when you get these service)  completely.
- Colour formatting done in output excel is for explanatory purpose only and not expected as part of output.


### Solution/Approach
 - I first started to explore off-the-shelf python libraries. My thought process was that if there were existing libraries that could somehow read the pdf in a structured way,
I could get away with transforming the unstructured data with minimal parsing logic on my end. I found out that there were many pdf mining libraries in python but all of them read the pdf in very
different ways - some flattened the pdf into a list of lines, some tried to extract the data in a tabular format, some tried to capture the pdf data in an xml, etc.
Overall, I found out that I could not rely on the direct output from the library. If I did, then I would have to write a lot of parsing logic on my end and make massive assumptions about the
structure of the pdf which would not scale well (I remember you telling me about how the format of the EOC changes from vendor to vendor).
- I then came across a pdf extraction library (`PyMuPDF`) which allowed me to read the pdf based on coordinates of the text blocks of the page. I found that I could read "blocks" of text using this
library and ignore sections of the pdf based on coordinates (like the second column - "What you must pay when you get these services" or the section on "Optional supplemental package 2").
This was my first approach to extract the data (code in [`coordinates_approach.py`](coordinates_approach.py)). I wasn't particularly happy about the way I was extracting the data.
I had to make some assumptions about the structure of the content in the pdf (like "per year" phrasing of the sentence to identify if the sentence talked about the number of dental visits) which
makes the code brittle. If these phrasings changed in a future version of the document, the code would not work.
- Because of the shortcomings of the previous approach, I started to explore if LLM could help. Specifically, if I can get away with not having to rely on phrases to identify the number of visits.
That was my second approach (code in [`llm_approach.py`](llm_approach.py) file). I was able to get the desired output using `gpt-3.5`. I have had to make some assumptions about the text (like beyond 100-pixel on
the x-axis is the second column) because I needed to trim the text that I sent into the gpt-3.5 context window as there is a limit of 4000 characters (including the prompt). But this logic is still
more robust than the previous approach because of less assumptions in the code. With `gpt-4`, I think we can pass in larger tokens in the context window, so that might help us avoid the parsing logic,
resulting in more robust code.
The obvious downside with LLMs is determinism. So far during all my testing, with zero temperature and a seed value, I was able to consistently see the desired results. But if we need to scale then
this is something that we need to be cognizant about. If we keep the context small, then I think we can (mostly) achieve deterministic results but there are no guarantees. In contrast, the previous
approach will always produce the desired results as long as the pdf content & layout does not change significantly.

Overall I think both the approaches have their pros and cons and which one would I choose would depend on the context, the scale that we want to achieve and the diversity of the data.

- In an attempt to avoid any sort of parsing logic I am exploring another approach of creating embeddings for text blocks inside the pdf and then using a cosine similarity function to find related texts.
I haven't gotten it fully working yet (the output has missing values) but you can check out the code in [`embedding_approach.py`](does_not_work_yet\embedding_approach.py).

**Note**
- To run the `llm_approach.py` script, you'd need an OpenAI API key. Once you have the key, paste the key on `line 40`:
  ```python
  openai.api_key = '<your-api-key-here>'

# OpenFDA Query Assistant

The OpenFDA Query Assistant is an innovative tool designed to leverage the power of the openFDA API. By utilizing a Retrieval-Augmented Generation (RAG) approach, this project formulates proper queries based on user questions, interacts with the openFDA servers, and processes the data to deliver informative responses.


## Overview
![Alt text](image-1.png)



## Getting Started

1. Installation
: Install the required dependencies by navigating to the project directory and running

   ```bash
   pip install -r requirements.txt
   ```

2. Getting Started:
: Open .env file and insert your OpenAI API key.
   ```bash
    OPENAI_API_KEY = "Your-OpenAI-API-Key-Here"
    OPENFDA_API_KEY = "Your-OpenAI-API-Key-Here"
   ```

3. Run the model
:
   ```bash
    python3 main.py "Your Question Here"
   ```


## Example
Here are a few example questions you might try:

"What are the side effects of Ibuprofen?"
"Has there been any recall on Metformin?"
"What adverse events are associated with Lexapro?"
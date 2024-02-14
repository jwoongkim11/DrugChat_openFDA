from openai import OpenAI
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from config import OPENFDA_API_KEY
from chain import loader
from chain.prompts import Property_example_question, Property_example_response, Property_example_tool_response, Searchterm_example_question, Searchterm_example_response, Searchterm_example_tool_response
from abc import ABC, abstractmethod
import requests

client = OpenAI()

#Defining tools to be used inside chatGPT
tools_for_property = [
    {
        "type": "function",
        "function": {
            "name": "search_query_generator",
            "description": """
        The 'Context' provided includes openFDA functions and their description. Determine which openFDA functions could be useful in answering the given question and extract their 'properties' on a word-by-word basis.
        """,
            "parameters": {
                "type": "object",
                "properties": {
                    "properties": {
                        'type': 'string',
                        'items': {
                        'type': 'string'
                        },
                        'description': """
                        This array contains the 'properties' extracted from the context, each identified as a distinct element. These 'properties' represent specific openFDA functions, facilitating targeted information retrieval.
                        """
                    },
                },
                "required": ["properties"]
            }
        }
    }
]

tools_for_url = [
    {
        "type": "function",
        "function": {
            "name": "search_query_generator",
            "description": """
            This function returns array of urls to be used for querying the openFDA database.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        'type': 'array',
                        'items': {
                        'type': 'string'
                        },
                        'description': """
                        This array contains the 'urls', which represent the actual query to be put into openFDA database, searching for relevant information. It should follow the syntax of openFDA API.
                        """
                    },
                },
                "required": ["url"]
            }
        }
    }
]

tools_for_search_term= [
    {
        "type": "function",
        "function": {
            "name": "search_query_generator",
            "description": """
            This function generates ‘search terms’ for querying a dataset, based on the identified 'properties' and the given question. It processes each property individually to determine the most relevant 'search terms' for finding information related to the question.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "search_terms": {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'description': """
                        This array contains the 'search_terms' inferred from the properties and the question, each identified as a distinct element. These 'search_temrs' represent the actual query to be put into openFDA database, searching for relevant information. It should follow the syntax of openFDA API.
                        """
                    },
                },
                "required": ["search_terms"]
            }
        }
    }
]




#Defining templates to be used inside chatGPT
RAG_Prompt_template = """
The 'Context' provided consists of openFDA functions. Determine which openFDA functions could be helpful in answering the given question and extract their properties. Multiple outputs are possible.
It is highly recommended to use your own knowledge about the syntax of openFDA
\n\n
Context: {context}
\n\n
Question: {question}
"""

NativeGPT_Prompt_template = """
{question}
\n\n
Please write openFDA queries to get the information above
"""


Search_term_template = """
This function is designed to generate 'search terms' for generating queries to be fed into the openFDA API. 'Properties' denote the searchable fields or domains pertinent to the query, and the 'search terms' are constructed in a query format that links these 'properties' with exact keywords It's crucial to utilize your knowledge of the openFDA query syntax when deciding on the 'search terms'!. If you believe the provided 'properties' are incorrect or incomplete, feel free to modify them accordingly to ensure the accuracy and relevance of the 'search terms'. These 'search terms' will be the queries used for searching the openFDA database.

Decide the search terms below.
\n
\n
properties: {json_response}
\n
question: {question}
\n
search_terms: 
"""

class Extractor(ABC):
    """
    Desined to outline the structure and required methods for different types of extractors within the system.
    """
    @abstractmethod
    def RAG_extract(self):
        #Extract attributes using RAG
        pass




class Extract_property(Extractor):
    """
    Perform the 'property' extraction process specific to the extractor's purpose. 

    Returns:
        The structured output produced by the extraction process, ready for further use within the system.
    """
    def __init__(self, user_request):
        self.user_request = user_request

    def RAG_extract(self):
        """
        Extracts the 'properties' relevant to openFDA functions that are helpful to answer the given user request. This method leverages the GPT model to understand and interpret the user request, identifying and extracting key 'properties' that can be used to formulate targeted queries against the openFDA database.

        Returns:
            list: A list of strings where each string represents a distinct 'property' relevant to the user's request.
        """
        response = client.chat.completions.create(
            model = 'gpt-4-turbo-preview',
            messages = [
                {'role': 'system', 'content': "You are a system that determines the right 'properties' of openFDA functions that is helpful to answer the given question."},
                Property_example_question,
                Property_example_response,
                Property_example_tool_response,
                {"role": "user", "content": self.user_request}
                ],
            tools = tools_for_property,
            tool_choice = 'auto',
            temperature = 0.5,
            response_format={ "type": "json_object" }
        )
        json_response = json.loads(response.choices[0].message.content)['properties']
        return json_response
    
    def GPT_native_extract(self):
        """
        Generates complete query URLs based on the user's request. 

        Returns:
            list: A list of complete query URLs, each formatted according to the openFDA API syntax.
        """
        response = client.chat.completions.create(
            model = 'gpt-4-turbo-preview',
            messages = [
                {'role': 'system', 'content': "You are a system that generates urls to query openFDA database."},
                {"role": "user", "content": self.user_request}
                ],
            tools = tools_for_url,
            tool_choice = 'auto',
            temperature = 0.5,
        )
        json_response = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        json_response_2 = json_response['url']
        return json_response_2


class Extract_search_term(Extractor):
    def __init__(self, prompt):
        self.prompt = prompt

    def RAG_extract(self):
        """
        Generate the ’search term’ relevant to extracted properties of openFDA functions and given user question.

        Returns:
            list: A list of strings where each string represents a distinct ‘search term’
        """
        response = client.chat.completions.create(
            model = 'gpt-4-turbo-preview',
            messages = [
                {'role': 'system', 'content': "You are a system that determines the right 'search terms' of openFDA functions to give an answer to the given question."},
                Searchterm_example_question,
                Searchterm_example_response,
                Searchterm_example_tool_response,
                {"role": "user", "content": self.prompt}
                ],
            tools = tools_for_search_term,
            tool_choice = 'auto',
            temperature = 0.5,
        )
        result = json.loads(response.choices[0].message.tool_calls[0].function.arguments)['search_terms']
        return result

def find_source(context, json_response):
    """
    Find the source of the property in the context. Source means the category of the openFDA API endpoint.
    """
    property_source_pairs = []
    for doc in context:
        page_content = json.loads(doc.page_content)
        api_endpoint_name = page_content['Endpoint']
        property_source_pairs.append({page_content["property"]: api_endpoint_name})
    endpoints = []
    for source in property_source_pairs:
        for property in json_response:
            if property in source:
                endpoints.append(source[property])
    return endpoints


def generate_url_RAG(context_prompt):
    """
    Generate urls using RAG model
    """
    context = context_prompt['context']
    #Extract context and question
    question = context_prompt['question']
    #Formulate first query
    user_request = RAG_Prompt_template.format(context=context, question=question)
    Property_generator = Extract_property(user_request)
    json_response = Property_generator.RAG_extract()
    #Formulate second query
    formatted_search_term_template = Search_term_template.format(json_response=json.dumps(json_response), question=question) # json_response를 문자열로 변환하여 사용
    Searchterm_generator = Extract_search_term(formatted_search_term_template)
    final_result = Searchterm_generator.RAG_extract()
    sources = find_source(context, json_response)
    urls = []
    for result, source in zip(final_result, sources):
        url = f"https://api.fda.gov/{source}.json?api_key={OPENFDA_API_KEY}&search={result}"
        urls.append(url)
    return {'urls': urls, 'question': question}


def generate_url_nativeGPT(context_prompt):
    """
    Generate urls using NativeGPT model
    """
    #Extract context and question
    question = context_prompt['question']
    #Formulate query
    user_request = NativeGPT_Prompt_template.format(question=question)
    Property_generator = Extract_property(user_request)
    urls = Property_generator.GPT_native_extract()
    #insert api_key parameter inside each urls
    new_urls = []
    for url in urls:
        index = str.find(url, "search=")
        if index != -1:
            new_url = url[:index] + "api_key=" + OPENFDA_API_KEY + "&" + url[index:]
            new_urls.append(new_url)
        else:
            new_urls = urls
    return {'urls': new_urls, 'question': question}


def combine_url(urls):
    """
    Combine the urls from the two models
    """
    total_urls = []
    url1 = urls['result1']
    url2 = urls['result2']

    for comp in url1['urls']:
        total_urls.append(comp)
    for comp in url2['urls']:
        total_urls.append(comp)

    question = url1['question']
    return {'total_urls': total_urls, 'question': question}

def return_openfda_data(urls_with_question):
    """
    Return the openFDA data from the given urls
    """
    urls = urls_with_question['total_urls']
    question = urls_with_question['question']
    returned_responses = []
    for url in urls:
        response = requests.get(url)
        data = response.json()
        #Check if the response id valid
        error_present = False
        for key in data:
            if key == 'error':
                error_present = True
                break
        if error_present:
            continue
        
        #Extract core information inside the response
        if "results" in data:
            openfda_data = data["results"]
        else:
            openfda_data = data
        remove_openfda_key(openfda_data, 'openfda')
        #Integrate the response with requested url
        openfda_data_with_url = {}
        openfda_data_with_url['Requested url'] = url
        openfda_data_with_url['Result'] = openfda_data
        returned_responses.append(openfda_data_with_url)
    return {'openfda_data_list': returned_responses, 'question': question}


def remove_openfda_key(d, key):
    """
    Delete key which is not helpful in answering the given question
    :param d: dict or list
    :param key: key to be deleted
    """
    if isinstance(d, dict): 
        if key in d:
            del d[key]
        for k, v in list(d.items()):
            remove_openfda_key(v, key)
    elif isinstance(d, list): 
        for item in d:
            remove_openfda_key(item, key)
    else:
        pass

def final_response(openfda_data_list):
    """
    Generate final response using GPT model
    """
    openfda_data = openfda_data_list['openfda_data_list']
    question = openfda_data_list['question']
    prompt = f"Answer the below question based on the relevant data extracted from the openFDA database, excluding any entries where errors were encountered. Only consider the data that was successfully returned and do not even mention about the failed data. \n question: {question} \n openFDA data: {openfda_data}"
    response = client.chat.completions.create(
        model = 'gpt-4-turbo-preview',
        messages = [
            {'role': 'system', 'content': "You are an expert of drugs, providing helpful answers to a given question."},
            {"role": "user", "content": prompt}
            ],
        tools = tools_for_search_term,
        tool_choice = 'auto',
        temperature = 1,
    )
    result = response.choices[0].message
    return result

vector_db = loader.vector_db
retriever = vector_db.as_retriever()
prompt = ChatPromptTemplate.from_template(RAG_Prompt_template)


chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | RunnableParallel({"result1": RunnableLambda(generate_url_nativeGPT), "result2": RunnableLambda(generate_url_RAG)})
    | RunnableLambda(combine_url)
    | RunnableLambda(return_openfda_data)
    | RunnableLambda(final_response)
)
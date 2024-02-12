from openai import OpenAI
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from config import OPENFDA_API_KEY, common_source
from chain import loader
from chain.prompts import Property_example_question, Property_example_response, Property_example_tool_response, Searchterm_example_question, Searchterm_example_response, Searchterm_example_tool_response
from abc import ABC, abstractmethod
import requests

client = OpenAI()

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




#similarity search with langchain
Prompt_template = """
The 'Context' provided consists of openFDA functions. Determine which openFDA functions could be helpful in answering the given question and extract their properties. Multiple outputs are possible.
It is highly recommended to use your own knowledge about the syntax of openFDA
\n\n
Context: {context}
\n\n
Question: {question}
"""

#similarity search with langchain
Search_term_template = """
This function formulates 'search terms' as queries by pairing identified 'properties' with specific keywords or phrases relevant to the question. Properties' denote the searchable fields or domains, and the 'search terms' are constructed in a query format that links these 'properties' with exact keywords. This ‘search terms’ will eventually be used for querying to openFDA API.
Input:
* 		Properties: The searchable fields or domains pertinent to the question.
* 		Question: The specific inquiry guiding the pairing of keywords with 'properties'.
Output: A singular or list of 'search terms' formatted as queries, such as search=property:"keyword"

Decide the search terms based on the following properties and question.\n
It is highly recommended for you to use your own knowledge about the syntax of openFDA\n\n

properties: {json_response}
\n
question: {question}
\n
search_terms: 
"""

class Extractor(ABC):

    @abstractmethod
    def gpt_extract(self):
        #Extract attributes using gpt
        pass




class Extract_property(Extractor):
    def __init__(self, user_request):
        self.user_request = user_request

    #pararral function calling으로 수정
    def gpt_extract(self):
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
    

class Extract_search_term(Extractor):
    def __init__(self, prompt):
        self.prompt = prompt

    #Few shot prompt로 수정.
    def gpt_extract(self):
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


def make_prompt(context_prompt):
    context = context_prompt['context']
    question = context_prompt['question']
    return Prompt_template.format(context=context, question=question)

def find_source(context, json_response):
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


def generate_url_wrapper(context_prompt):
    #Extract context and question
    context = context_prompt['context']
    question = context_prompt['question']
    #Formulate first query
    user_request = Prompt_template.format(context=context, question=question)
    Property_generator = Extract_property(user_request)
    json_response = Property_generator.gpt_extract()
    #Formulate second query
    formatted_search_term_template = Search_term_template.format(json_response=json.dumps(json_response), question=question) # json_response를 문자열로 변환하여 사용
    Searchterm_generator = Extract_search_term(formatted_search_term_template)
    final_result = Searchterm_generator.gpt_extract()
    sources = find_source(context, json_response)
    #Generate final url to be fed into openFDA

    return {'json_response': json_response, 'final_result': final_result, 'sources': sources, 'question': question}

def return_openfda_data(query_result):
    final_result = query_result['final_result']
    sources = query_result['sources']
    question = query_result['question']
    openfda_data_list = []
    for result, source in zip(final_result, sources):
        url = f"https://api.fda.gov/{source}.json?api_key={OPENFDA_API_KEY}&search={result}"
        response = requests.get(url)
        data = response.json()
        if "results" in data:
            openfda_data = data["results"]
            openfda_data.append(f"query: {result}")
        else:
            openfda_data = data
            openfda_data['query']=result
        remove_openfda_key(openfda_data, 'openfda')
        openfda_data_list.append(openfda_data)
    return {'openfda_data_list': openfda_data_list, 'question': question}

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
    openfda_data = openfda_data_list['openfda_data_list']
    question = openfda_data_list['question']
    prompt = f"Answer the below question based on the relevant data extracted from the openFDA database, excluding any entries where errors were encountered. Only consider the data that was successfully returned. \n question: {question} \n openFDA data: {openfda_data_list}"
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
retriever = vector_db.as_retriever() #중복X로 수정
prompt = ChatPromptTemplate.from_template(Prompt_template)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | RunnableLambda(generate_url_wrapper)
    | RunnableLambda(return_openfda_data)
    | RunnableLambda(final_response)
)

import json

# Example questions and assistant's response structures for few-shot prompting (simplified)

Property_example_question = {
    'role': 'user',
    'content': "What are the reported adverse events associated with the use of nonsteroidal anti-inflammatory drugs (NSAIDs) according to the FDA's database?"
}

Property_example_response = {
    "role": 'assistant', 
    "content": None,
    "tool_calls": [
        {
            'id': 'call_abc123',
            'function': {
                'name': 'search_query_generator',
                'arguments': json.dumps({
                    "properties": [
                        "patient.drug.openfda.pharm_class_epc",
                    ]
                }),
            },
            'type': 'function'
        }
    ]
}

Property_example_tool_response = {
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": '{"properties": [{"patient.drug.openfda.pharm_class_epc"}]}'
}

Searchterm_example_question = {
    'role': 'user',
    'content': 
"""
This function is designed to generate 'search terms' for generating queries to be fed into the openFDA API. 'Properties' denote the searchable fields or domains pertinent to the query, and the 'search terms' are constructed in a query format that links these 'properties' with exact keywords It's crucial to utilize your knowledge of the openFDA query syntax when deciding on the 'search terms'!. If you believe the provided 'properties' are incorrect or incomplete, feel free to modify them accordingly to ensure the accuracy and relevance of the 'search terms'. These 'search terms' will be the queries used for searching the openFDA database.

Decide the search terms below.
\n
\n
properties: {"properties": ['monomer_substance.refuuid', 'monomer_substance.name', 'moieties.digest', 'parent_substance.name']}
\n
question: "Can you tell me everything about benzene?"
\n
search_terms: 
"""
}

Searchterm_example_response = {
    "role": 'assistant', 
    "content": None,
    "tool_calls": [
        {
            'id': 'call_abc123',
            'function': {
                'name': 'search_query_generator',
                'arguments': json.dumps({
                    "search_terms": [
                        'monomer_substance.refuuid:"benzene"',
                        'monomer_substance.name:"benzene',
                        'moieties.digest:"benzene"',
                        'parent_substance.name:"benzene"'
                    ]
                }),
            },
            'type': 'function'
        }
    ]
}

Searchterm_example_tool_response = {
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": '{"search_terms":[monomer_substance.refuuid:"benzene", monomer_substance.name:"benzene", moieties.digest:"benzene", parent_substance.name:"benzene"]}'
}


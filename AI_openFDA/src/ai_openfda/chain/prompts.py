import json

Property_example_question = {
    'role': 'user',
    'content': "What are the reported adverse events associated with the use of nonsteroidal anti-inflammatory drugs (NSAIDs) according to the FDA's database?"
}

# Example assistant's response structure (simplified)
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
            'type': 'function'  # Correctly include 'type' as required
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
This function formulates 'search terms' as queries by pairing identified 'properties' with specific keywords or phrases relevant to the question. Properties' denote the searchable fields or domains, and the 'search terms' are constructed in a query format that links these 'properties' with exact keywords. This ‘search terms’ will eventually be used for querying to openFDA API.
Input:
* 		Properties: The searchable fields or domains pertinent to the question.
* 		Question: The specific inquiry guiding the pairing of keywords with 'properties'.
Output: A singular or list of 'search terms' formatted as queries, such as search=property:"keyword"

Decide the search terms based on the following properties and question.\n
It is highly recommended for you to use your own knowledge about the syntax of openFDA\n\n

properties: {"properties": ['monomer_substance.refuuid', 'monomer_substance.name', 'moieties.digest', 'parent_substance.name']}
\n
question: "Can you tell me everything about benzene?"
\n
search_terms: 
"""
}

# Example assistant's response structure (simplified)
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
            'type': 'function'  # Correctly include 'type' as required
        }
    ]
}

Searchterm_example_tool_response = {
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": '{"search_terms":[monomer_substance.refuuid:"benzene", monomer_substance.name:"benzene", moieties.digest:"benzene", parent_substance.name:"benzene"]}'
}


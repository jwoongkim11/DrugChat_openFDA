import argparse
from chain.chains import chain
from config import OPENFDA_API_KEY

parser = argparse.ArgumentParser(description="Query information from the openFDA's database.")
parser.add_argument("question", type=str, help="The question to query the openFDA's database")

args = parser.parse_args()

response = chain.invoke(args.question)
print(response)

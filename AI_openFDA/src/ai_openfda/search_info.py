import openai
import requests
from config import OPENFDA_API_KEY
from generate_url import url

response = requests.get(url)
data = response.json()


results = []
for result in data["results"]:
  results.append(result)

if len(results) != 0:
    version_list = {}
    for order, result in enumerate(results):
        if 'version' not in result:
            continue
        version = result['version']
        version_list[order] = version

    if version_list is not None:
        newest_index = max(version_list, key = lambda k: float(version_list[k]))
        final_results = version_list[newest_index]
    else:
        final_results = results
else:
    raise Exception(f"No data found. Please check the request URL: {url}")
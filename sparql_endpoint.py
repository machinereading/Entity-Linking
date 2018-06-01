import urllib
import urllib2
import json, re
from time import sleep
import time

class Constants:
	SPARQL_LIMIT = 10000

# Retrieves results of a SPARQL query from an endpoint.
# This function doesn't support LIMITS. All (even 10000+) results are retrieved.
# All query arguments are present as keys in all rows of the resulting array. (Null column == None value)
# All results (and their keys) are in Unicode.
# query_str: not url_encoded
def query(endpoint_url, graph_iri, query_str, timeout=0, delay=0):
	args = {
		'default-graph-uri': graph_iri,
		'format': 'application/json',
		'query': None,
		'timeout': timeout
	}

	current_offset = 0
	result_data = []

	while True:
		args['query'] = query_str + ' LIMIT ' + str(Constants.SPARQL_LIMIT) + ' OFFSET ' + str(current_offset)
		data = urllib.urlencode(args)
		url = endpoint_url + '?' + data

		# print url
		while True :
			try :
				request = urllib2.urlopen(url)
				break
			except :
				time.sleep(1)

		response_str = request.read()
		try:
			response_data = json.loads(response_str)
		except Exception as e:
			response_str = re.sub(r'\\U[0-9A-Za-z]{8}', '', response_str)
			response_data = json.loads(response_str)

		"""
		try:
			response_data = json.loads(response_str)
		except Exception as e:
			response_str = re.sub(r'\\U[0-9A-Za-z]{8}', '', response_str)
			response_data = json.loads(response_str)
		"""
		query_vars = response_data['head']['vars']

		count =0
		for row in response_data['results']['bindings']:
			result_row = {}
			for var in query_vars:
				if var in row:
					result_row[var] = row[var]['value']
				else:
					result_row[var] = None

			result_data.append(result_row)

			count += 1
			if False and u'\uadc0\uc778' in result_row['label']:
				print result_row
				print count
				print current_offset

		if len(response_data['results']['bindings']) == Constants.SPARQL_LIMIT:
			current_offset += Constants.SPARQL_LIMIT
		else:
			break

	if delay > 0:
		# sleep a bit to preserve endpoint sanity.
		sleep(delay)

	return result_data

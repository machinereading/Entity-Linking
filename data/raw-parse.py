import json
import os
import codecs
import urllib
import sparql_endpoint

endpoint = "http://143.248.135.20:45103/sparql"
graph_iri = "http://ko.dbpedia2015.kaist.ac.kr"

def clean_annotation(annotation)  :
	annotation['start'] = str(annotation['start'])
	annotation['end'] = str(annotation['end'])
	try:
		annotation['uri'] = urllib.unquote(annotation['uri'].encode('ASCII')).decode('utf-8')
	except:
		pass

	if annotation['uri'] == "empty" :
		annotation['uri'] = ""
	elif annotation['uri'] != "" :
		index = annotation['uri'].rfind('/')+1
		entity = annotation['uri'][index:].replace('_', ' ')

		sparql_query = "select * where { <http://ko.dbpedia.org/resource/" + entity.replace(' ', '_').encode('utf-8') + "> ?p ?o . }"
		sparql_result = sparql_endpoint.query(endpoint, sparql_query, graph_iri)

		#using sparql endpoint
		if len(sparql_result) > 0 :
			annotation['uri'] = 'http://ko.dbpedia.org/page/' + entity
		else :
			print annotation['uri']
			annotation['uri'] = ""

		"""
		# using label cache
		if entity not in addresses :
			print annotation['uri']
			annotation['uri'] = ""
		else :
			annotation['uri'] = 'http://ko.dbpedia.org/page/' + entity
		"""
	return annotation

for root, dirs, files in os.walk('toparse3/'):
	for filename in files:
		f = open('toparse3/' + filename)
		data = f.read().replace('\xef\xbb\xbf', '').replace('True','true').replace('False','false').decode('utf-8')
		entities = json.loads(data)

		f.close()

		index = filename[len('annotation') : filename.index('.')]


		f2 = open('wiki-raw/wiki-' + index + '.txt')
		text = f2.read().replace('\xef\xbb\xbf', '')

		f2.close()

		f3 = codecs.open('processing/' + index + '.txt', 'w', 'utf-8')
		result = '{"text":"' + text.decode('utf-8').replace('"','\\"') + '", "entities":['
		for entity in entities :
			entity = clean_annotation(entity)
			try:
				entity['uri'] = urllib.unquote(entity['uri'].encode('ASCII')).decode('utf-8')
			except:
				pass

			result += json.dumps(entity, ensure_ascii=False) + ','
		result = result[:-1] + ']}'
#		print json.dumps({'text':text.decode('utf-8'), 'entities':entities}, ensure_ascii=False)
		f3.write(result)

		f3.close()
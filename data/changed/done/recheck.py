import json
import os
import sparql_endpoint
import codecs
import urllib
basedir = './raw'
mergedir = './merging'
MAX_LEN = 100000

endpoint = "http://143.248.135.20:45103/sparql"
graph_iri = "http://ko.dbpedia2015.kaist.ac.kr"

addresses = []

def get_json(annotator, file) :
	f = open(basedir + '/' + annotator + '/' + file)
	data = json.loads(f.read())

	f.close()

	return data

def format_row(annotation1, annotation2, key) :

	value1 = annotation1[key]
	value2 = annotation2[key]

	print value1

	if isinstance(value1, basestring) :
		value1 = '"' + value1 + '"'
		value2 = '"' + value2 + '"'
	else :
		value1 = str(value1)
		value2 = str(value2)

	if value1 == value2 :
		return '"' + key + '": ' + value1  + ',' + '\r\n'
	else :
		return ' '*4 + '"' + key + '": ' + value1 + '/' + value2 + ',' + '\r\n'

def format_json(annotation) :
	different = '{' + '\r\n'
	different += format_row(annotation, annotation, 'is_noun')
	different += format_row(annotation, annotation, 'start')
	different += format_row(annotation, annotation, 'text')
	different += format_row(annotation, annotation, 'timespace')
	different += format_row(annotation, annotation, 'end')
	different += format_row(annotation, annotation, 'uri')
	different += format_row(annotation, annotation, 'redirection')
	different += format_row(annotation, annotation, 'meaning')
	different += format_row(annotation, annotation, 'coreference')
	different += format_row(annotation, annotation, 'metaphor')
	different += '"id": ' + str(annotation['id']) + '\r\n},\r\n'
	return different

# clean annotation into structured one
def clean_annotation(annotation)  :
	annotation['start'] = int(annotation['start'])
	annotation['end'] = int(annotation['end'])
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
			annotation['uri'] = 'http://ko.dbpedia.org/resource/' + entity.replace(' ', '_')
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

def compare(data1 ,data2) :
	index1 = 0
	index2 = 0
	same = []
	different = ""

	data1 = sorted(data1, key = lambda x: int(x['start']) + float(x['end'])/MAX_LEN)
	data2 = sorted(data2, key = lambda x: int(x['start']) + float(x['end'])/MAX_LEN)

	while index1 < len(data1) and index2 < len(data2) :
		annotation1 = clean_annotation(data1[index1])
		annotation2 = clean_annotation(data2[index2])

		if annotation1['start'] < annotation2['start'] or (annotation1['start'] == annotation2['start'] and annotation1['end'] < annotation2['end']):
			index1 += 1
			different += format_json(annotation1)
		elif annotation1['start'] > annotation2['start'] or (annotation1['start'] == annotation2['start'] and annotation1['end'] > annotation2['end']):
			index2 += 1
			different += format_json(annotation2)
		else :
			index1 += 1
			index2 += 1
			annotation2['id'] = annotation1['id']
			if annotation1 == annotation2 :
				same.append(annotation1)
			else :
				different += '{' + '\r\n'
				different += format_row(annotation1, annotation2, 'is_noun')
				different += format_row(annotation1, annotation2, 'start')
				different += format_row(annotation1, annotation2, 'text')
				different += format_row(annotation1, annotation2, 'timespace')
				different += format_row(annotation1, annotation2, 'end')
				different += format_row(annotation1, annotation2, 'uri')
				different += format_row(annotation1, annotation2, 'redirection')
				different += format_row(annotation1, annotation2, 'meaning')
				different += format_row(annotation1, annotation2, 'coreference')
				different += format_row(annotation1, annotation2, 'metaphor')
				different += '"id": ' + str(annotation1['id']) + '\r\n},\r\n'



	return same, different

for index in [1,2,3,4,5,11,12,13,14,15] :
	f = open('annotation' + str(index) + '.txt')
	print index

	data = '[' + f.read().decode('utf-8').replace('True', 'true').replace('False', 'false').replace(u'\ufeff', '')[:-2] + ']'
	data = json.loads(data)
	for annotation in data :
		clean_annotation(annotation)

	f.close()

	f = codecs.open('changed/annotation' + str(index) + '.txt', 'w', 'utf-8')
	f.write(json.dumps(data))

	f.close()

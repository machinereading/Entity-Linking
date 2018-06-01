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
	f = open('merged/annotation' + str(index) + '.txt')
	data = json.loads(f.read())
	f.close()

	f = codecs.open('changed/annotation' + str(index) + '.txt', 'w', 'utf-8')
	data = sorted(data, key = lambda x: int(x['start']) + float(x['end'])/MAX_LEN)
	for annotation in data :
		f.write(format_json(annotation))

	f.close()

"""
f = open('2015-dbpedia-instance-label-cache.txt')
for line in f :
	cols = line.strip().split('\t')
	addresses.append(cols[1].decode('utf-8'))
#	addresses.append(cols[0].decode('utf-8').replace('resource', 'page'))
#	print `cols[0].decode('utf-8')`
#	print `cols[0]`

f.close()

annotators = []
for annotator in os.listdir(basedir) :
	annotators.append(annotator)

for annotator1 in annotators :
	for annotator2 in annotators :
		if annotator1 < annotator2 and annotator1 != annotator2 :
			try :
				os.mkdir(mergedir + '/' + annotator1 + '-' + annotator2)
			except :
				pass
			filelist1 = os.listdir(basedir + '/' + annotator1)
			filelist2 = os.listdir(basedir + '/' + annotator2)

			for file in filelist1 :
				if file in filelist2:
					data1 = get_json(annotator1, file)
					data2 = get_json(annotator2, file)
					result1, result2 = compare(data1, data2)

					f = codecs.open(mergedir + '/' + annotator1 + '-' + annotator2 + '/' + file+ '.txt', 'w', 'utf-8')
					f.write(json.dumps(result1))
					f.close()

					f = codecs.open(mergedir + '/' + annotator1 + '-' + annotator2 + '/' + file , 'w', 'utf-8')
					f.write(unicode(result2))
					f.close()
"""
print 'done'
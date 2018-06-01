import json
import urllib
def analyze(filename1, filename2) :
	f = open(filename1)
	f2 = open(filename2)
	print filename1

	data1 = json.loads(f.read())
	data2 = json.loads(
		'[' + f2.read().decode('utf-8').replace('True', 'true').replace('False', 'false').replace(u'\ufeff', '')[
		      :-2] + ']')

	f.close()
	f2.close()

	for elem1 in data1:
		for elem2 in data2:
			if elem1['start'] == elem2['start'] and elem1['end'] == elem2['end']:
				print 'no'

	result = []
	for elem1 in data1 :
		result.append(elem1)
	for elem2 in data2:
		result.append(elem2)

	for elem in result :

		try:
			elem['uri'] = urllib.unquote(elem['uri'].encode('ASCII')).decode('utf-8')
		except:
			pass
		elem['uri'] = elem['uri'].replace('page', 'resource')

	index = filename1[10:filename1.find('.txt')]
	f = open('done/annotation' + index + '.txt', 'w')
	f.write(json.dumps(result))
	f.close()

for i in range(1, 6) :
	analyze('annotation' + str(i) + '.txt.txt', 'jeonguk_sejin_annotation' + str(i) + '_difference_merged.txt')

for i in range(11, 16) :
	analyze('annotation' + str(i) + '.txt.txt', 'sangha_sejin_annotation' + str(i) + '_difference_merged.txt')
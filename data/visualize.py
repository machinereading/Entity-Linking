import json

for i in range(1, 16) :
	raw_data = ''
	try :
		f = open('merged/annotation' + str(i) + '.txt')
		raw_data = f.read()
		f.close()
	except :
		continue

	data = json.loads(raw_data)
	print json.dumps(data, ensure_ascii= False)
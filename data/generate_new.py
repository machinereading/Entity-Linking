import json
import os
import codecs

for root, dirs, files in os.walk('merged/'):
	for filename in files:
		f = open('merged/' + filename)
		data = f.read().replace('\xef\xbb\xbf', '').replace('True','true').replace('False','false').decode('utf-8')
		print `data`
		entities = json.loads(data)

		f.close()

		index = filename[len('annotation') : filename.index('.')]


		f2 = open('wiki-raw/wiki-' + index + '.txt')
		text = f2.read().replace('\xef\xbb\xbf', '')

		f2.close()

		f3 = codecs.open('processing/' + index + '.txt', 'w', 'utf-8')
		result = '{"text":"' + text.decode('utf-8').replace('"','\\"') + '", "entities":['
		for entity in entities :
			result += json.dumps(entity, ensure_ascii=False) + ','
		result = result[:-1] + ']}'
#		print json.dumps({'text':text.decode('utf-8'), 'entities':entities}, ensure_ascii=False)
		f3.write(result)

		f3.close()
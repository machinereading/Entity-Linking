import json
import os,time
import urllib2, urllib

ELU_ADDR = "http://143.248.135.60:2223/entity_linking"
IS_ETRI = True
IS_UTF8 = False
data_dir = "test"
def load_answers() :
	answer_list = []
	text_list = []
	for root, dirs, files in os.walk(data_dir):
		for file in files:
			f = open(data_dir + '/' + file)
			data = json.loads(f.read().replace('\xef\xbb\xbf',''))
			answer_list.append(data['entities'])
			text_list.append(data['text'])

			f.close()

	return answer_list, text_list


def send_post(url, input_string):
	req = urllib2.Request(url, data=input_string.encode('utf-8'), headers={'Content-Type':'application/json; charset=utf-8'})
	f = urllib2.urlopen(req)
	data = f.read()

	f.close()

	return data.replace('\xef\xbb\xbf','')


def modify_answers(answers, header) :
	new_answers = []

	for answer in answers :
		for elem in answer:
			elem['uri'] = elem['uri'].replace('http://ko.dbpedia.org/page/','http://ko.dbpedia.org/resource/')
			if elem['redirection'] == False :
				elem['uri'] = ''
			elif header not in elem['uri']:
				#print 'no header ' +  elem['uri']
				elem['uri'] = ''
			if 'subanswers' not in elem.keys():
				elem['subanswers'] = []
			if 'included' not in elem.keys():
				elem['included'] = -1

		new_answer = []
		for i in range(len(answer)) :
			is_required = True
			answer[i]['subanswers'] = []
			for j in range(len(answer)) :
				if i != j and answer[i]['start'] >= answer[j]['start'] and answer[i]['end'] <= answer[j]['end'] :
					if answer[i]['uri'] == '':
						is_required = False
					elif answer[j]['uri'] != '' :
						is_required = False
					answer[j]['subanswers'].append(i)
					answer[i]['included'] = j
			if is_required :
				new_answer.append(answer[i])

		new_answers.append(answer)

	return new_answers

def pos_match(text, pos) :
	return len(bytearray(text.decode('utf-8')[:pos].encode('utf-8')))

def match_entities(annotation, elu_result) :
	for entity in elu_result:
		# change for etri
		if annotation['begin'] == entity['start_offset'] and annotation['end'] == entity['end_offset']:
			entity['matched'] = True
			if annotation['uri'] == '' or not annotation['redirection']:
				annotation['case'] = 7
				return False
			elif entity['uri'] == annotation['uri']:
				annotation['case'] = 0
				return True
			else:

			#	print annotation['uri'] + ' ' + entity['selected_uri'] + ' ' + entity['text'] + ' ' + str(annotation['redirection'])
				annotation['case'] = 2
				return True

	return False


def check_performance_boundary(answers, texts):
	cases = [0, 0, 0, 0, 0, 0, 0, 0]
	totaltime = 0
	sent_count = 0


	for i in range(len(answers)) :
		text = texts[i]
		pos_data = json.loads(send_post('http://143.248.135.60:31235/etri_pos', json.dumps({'text': text})))
		sent_count += len(pos_data)
		print 'pos ' + str(i)

	starttime = time.time()


	for i in range(len(answers)):
		answer = answers[i]
		text = texts[i]


		elu_result = json.loads(send_post(ELU_ADDR, json.dumps({'text':text})))
		print 'elu ' + str(i)
		# arrange answers

		annotations = []
		for annotation in answer :
			begin = int(annotation['start'])
			end = int(annotation['end'])
			uri = annotation['uri']
			subanswers = annotation['subanswers']
			included = annotation['included']
			redirection = annotation['redirection']

			annotations.append({'begin':begin, 'text':annotation['text'], 'end':end, 'uri':uri, 'subanswers':subanswers, 'included':included, 'case':4, 'redirection':redirection})


		utf8text = text.encode('utf-8')
		for entity in elu_result :
			entity['matched'] = False
			if 'offset_end' in entity.keys() :
				entity['start_offset'] = len(utf8text[:entity['offset_start']].decode('utf-8'))
				entity['end_offset'] = len(utf8text[:entity['offset_end']].decode('utf-8'))

		for annotation in annotations :
			match_entities(annotation, elu_result)

		for entity in elu_result :
			if not entity['matched']:
				#print 'wrongly found : ' + text[entity['start_offset']:entity['end_offset']]
				cases[2] += 1

		for annotation in annotations:
			if annotation['included'] != -1:
				continue
			if annotation['case'] == 0 :
				cases[0] += 1
			elif annotation['case'] == 4:
				#print 'could not found : ' + annotation['text']
				cases[1] += 1

	print 'total sent : ' +str(sent_count)
	print "total time : " + str(totaltime)
	print 'Correctly found exact boundary : ' + str(cases[0])
	print 'Could not found boundary : ' + str(cases[1])
	print 'Found non-boundary : ' + str(cases[2])

	tp = cases[0]
	fn = cases[1]

	fp = cases[2]

	precision = tp / float(tp+fp)
	recall = tp / float(tp + fn)

	print 'true positive : ' + str(tp)
	print 'false negative : ' + str(fn)
	print 'false positive : ' + str(fp)
	print 'precision : ' + str(precision)
	print 'recall : ' + str(recall)

	print 'f1-score : ' +  str(2*precision*recall/(precision+recall))
	print
	print

	return time.time()-starttime


def check_performance_entity(answers, texts):
	cases = [0, 0, 0, 0, 0, 0, 0, 0]
	totaltime = 0
	sent_count = 0


	for i in range(len(answers)) :
		text = texts[i]
		pos_data = json.loads(send_post('http://143.248.135.60:31235/etri_pos', json.dumps({'text': text})))
		sent_count += len(pos_data)

	starttime = time.time()


	for i in range(len(answers)):
		answer = answers[i]
		text = texts[i]

		elu_result = json.loads(send_post(ELU_ADDR, json.dumps({'text':text})))
		# arrange answers
		annotations = []
		for annotation in answer :
			begin = int(annotation['start'])
			end = int(annotation['end'])
			uri = annotation['uri']
			subanswers = annotation['subanswers']
			included = annotation['included']
			redirection = annotation['redirection']

			annotations.append({'begin':begin, 'text':annotation['text'], 'end':end, 'uri':uri, 'subanswers':subanswers, 'included':included, 'case':4, 'redirection':redirection})


		utf8text = text.encode('utf-8')
		for entity in elu_result :
			if 'offset_end' in entity.keys() :
				entity['start_offset'] = len(utf8text[:entity['offset_start']].decode('utf-8'))
				entity['end_offset'] = len(utf8text[:entity['offset_end']].decode('utf-8'))

		for annotation in annotations :
			match_entities(annotation, elu_result)

		for annotation in annotations:
			if annotation['uri'] == '':
				continue
			if annotation['case'] == 4:
				print 'no found : ' + annotation['text']

			cases[annotation['case']] += 1

	print 'total sent : ' +str(sent_count)
	print "total time : " + str(totaltime)
	print 'Correctly found exact entity : ' + str(cases[0])
	print 'Found entity candidate but too low score : ' + str(cases[1])
	print 'Found entity candidate but choose wrong candidate : ' + str(cases[2])
	print 'Found non-entity : ' + str(cases[3])
	print 'Could not detect entity : ' + str(cases[4])

	tp = cases[0]
	fn = cases[4]

	fp = cases[1] + cases[2] + cases[3] + cases[5]

	precision = tp / float(tp+fp)
	recall = tp / float(tp + fn)

	print 'true positive : ' + str(tp)
	print 'false negative : ' + str(fn)
	print 'false positive : ' + str(fp)
	print 'precision : ' + str(precision)
	print 'recall : ' + str(recall)

	print 'f1-score : ' +  str(2*precision*recall/(precision+recall))

	return time.time()-starttime

if __name__ == "__main__":

	alltime = 0

#	testset = [1,2,3,4,5,6,7,8,9,10,21,24,36,38,39]

	loaded_answers, loaded_texts = load_answers()
	new_answers = modify_answers(loaded_answers, 'http://ko.dbpedia.org/resource/')
	alltime += check_performance_boundary(new_answers, loaded_texts)
	alltime += check_performance_entity(new_answers, loaded_texts)

	print alltime

	alltime2 = 0
	total_line = 0

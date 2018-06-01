import json
import os,time
import urllib2, urllib

ANSWER_DIR = "merged"
TEXT_DIR = "wiki-raw"

IS_NEW = False
IS_ETRI = None
IS_UTF8 = None

OFFSET = 0.75

alltime = 0
# parameters for subanswer-scoring
Parital_Answer = True   # True - matching only one would be ok / False - score 1/n
Subanswer_Coeff = 0.5   # score when parital answer True

def load_answers() :
	answer_list = []
	text_list = []
	for root, dirs, files in os.walk(ANSWER_DIR):
		for file in files:
			f = open(ANSWER_DIR + '/' + file)
#			print
			answer_list.append(json.loads(f.read().replace('\xef\xbb\xbf','')))
			f.close()

			pos = file[10:file.find('txt')-1]
			f = open(TEXT_DIR + '/wiki-' + pos + '.txt')
			text_list.append(f.read())

			f.close()

	return answer_list, text_list


def send_post(url, input_string):

	req = urllib2.Request(url, data=input_string.encode('utf-8'), headers={'Content-Type':'application/json; charset=utf-8'})
	f = urllib2.urlopen(req)
	data = f.read()

	f.close()

	return data.replace('\xef\xbb\xbf','')


def modify_answers(answers) :
	for answer in answers :
		for i in range(len(answer)) :
			for j in range(len(answer)) :
				if i != j and answer[i]['start'] <= answer[j]['start'] and answer[i]['end'] >= answer[j]['end'] :
					answer[j]['included'] = i
					if 'subanswers' in answer[i].keys() :
						answer[i]['subanswers'].append(j)
					else :
						answer[i]['subanswers'] = [j]

		for elem in answer :
			if 'subanswers' not in elem.keys() :
				elem['subanswers'] = []
			if 'included' not in elem.keys():
				elem['included'] = -1


def pos_match(text, pos) :
	return len(bytearray(text.decode('utf-8')[:pos].encode('utf-8')))

def match_entities(annotation, elu_result) :
	for entity in elu_result['entities']:
		# change for etri
		if (not IS_UTF8 and annotation['begin'] == entity['start_offset'] and annotation['end'] == entity['start_offset'] + len(bytearray(entity['text'].encode('utf-8')))) or (IS_UTF8 and annotation['utf_begin'] == entity['start_offset'] and annotation['utf_end'] == entity['start_offset'] + len(entity['text'])):
#		boundary_checked = False
#		if IS_ETRI and (annotation['begin'] == entity['start_offset'] and annotation['end'] == entity['start_offset'] + len(bytearray(entity['text'].encode('utf-8')))):
#			boundary_checked = True
#		elif not IS_ETRI and (annotation['begin'] == entity['start_offset'] and annotation['end'] == entity['start_offset'] + len(entity['text'])) :
#			boundary_checked = True
#		if boundary_checked :

			entity['matched'] = True
			if annotation['uri'] == '' or not annotation['redirection']:
				annotation['case'] = 7
				return False
			elif entity['uri'] == annotation['uri']:
				annotation['case'] = 0
				print 'found : ' + entity['uri']
				return True
			else:

			#	print annotation['uri'] + ' ' + entity['selected_uri'] + ' ' + entity['text'] + ' ' + str(annotation['redirection'])
				annotation['case'] = 2
				return True

	return False


def check_performance(answers, texts):

	begin_dict = {}
	end_dict = {}
#	for i in range(len(answers)) :
	for i in range(10):
		answer = answers[i]
		text = texts[i]

		# arrange answers
		annotations = []
		for annotation in answer :
#			if IS_ETRI :
			begin = pos_match(text, int(annotation['start']))
			end = pos_match(text, int(annotation['end']))
#			else :
#				begin = annotation['start']
#				end = annotation['end']
			uri = annotation['uri']
			subanswers = annotation['subanswers']
			included = annotation['included']
			redirection = annotation['redirection']

			annotations.append({'begin':begin, 'text':annotation['text'], 'end':end, 'uri':uri, 'subanswers':subanswers, 'included':included, 'case':4, 'redirection':redirection, 'utf_begin':annotation['start'], 'utf_end':annotation['end']})

#		totaltime += elu_result['time_spent']
#		elu_result = elu_result['entities']


		pos_data = {}
		if IS_ETRI :
			pos_data = json.loads(send_post('http://143.248.135.60:31235/etri_pos', json.dumps({'text':text})))
		else :
			pos_data = json.loads(send_post('http://143.248.135.60:42336/hannanum_pos', json.dumps({'text':text})))

		full_morps = []
		for elem in pos_data :
			full_morps += elem['morp']



		for annotation in annotations :

			begin_lemmas = ''
			begin_types = ''
			end_lemmas = ''
			end_types = ''
			for morp in full_morps :
				if morp['position'] >= annotation['begin']-2 and morp['position'] < annotation['begin'] :
					begin_lemmas += morp['lemma'] + '/'
					begin_types = morp['type'] + '/'
				if morp['position'] >= annotation['end']and morp['position'] < annotation['end']+2 :
					end_lemmas += morp['lemma'] + '/'
					end_types += morp['type'] + '/'

			print 'uri ' + annotation['uri']
			print 'begin ' + begin_lemmas
			print begin_types
			print 'end ' + end_lemmas
			print end_types

			if begin_types in begin_dict.keys() :
				begin_dict[begin_types] += 1
			else :
				begin_dict[begin_types] = 1

			if end_types in end_dict.keys():
				end_dict[end_types] += 1
			else :
				end_dict[end_types] = 1

	print begin_dict
	print end_dict
	return None

if __name__ == "__main__":

	IS_ETRI = True
	loaded_answers, loaded_texts = load_answers()
	modify_answers(loaded_answers)
	check_performance(loaded_answers, loaded_texts)

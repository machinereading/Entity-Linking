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
	cases = [0, 0, 0, 0, 0, 0, 0, 0]
	totaltime = 0
	total_subannotation_score = 0
	total_neg_subannotation_score = 0
	sent_count = 0

#	for i in range(len(answers)) :
	for i in range(10):
		answer = answers[i]
		text = texts[i]

		print text
		print i

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

		starttime = time.time()
		elu_result = json.loads(send_post(ELU_ADDR, json.dumps({'text':text})))


#		totaltime += elu_result['time_spent']
#		elu_result = elu_result['entities']
		endtime = time.time()

		totaltime += endtime-starttime

		pos_data = {}
		if IS_ETRI :
			pos_data = json.loads(send_post('http://143.248.135.60:31235/etri_pos', json.dumps({'text':text})))
		else :
			pos_data = json.loads(send_post('http://143.248.135.60:42336/hannanum_pos', json.dumps({'text':text})))

		full_morps = []
		sent_count += len(pos_data)
		for elem in pos_data :
			full_morps += elem['morp']


		for annotation in annotations :

			if annotation['included'] != -1 :
				continue

			# only possible candidates
			begin_check = False
			end_check = False

			for morp in full_morps:
				if IS_ETRI and annotation['begin'] == morp['position'] :
					begin_check = True
				elif not IS_ETRI and annotation['utf_begin'] == morp['position'] :
					begin_check = True
				if IS_ETRI and annotation['end'] == morp['position'] + len(bytearray(morp['lemma'].encode('utf-8'))):
					end_check = True
				elif not IS_ETRI and annotation['utf_end'] == morp['position'] + len(morp['lemma']):
					end_check = True
	#			elif not IS_ETRI and annotation['end'] == morp['position'] + len(morp['lemma']):
	#				end_check = True

			# for testS
#			begin_check = True
#			end_check = True

			# find parsing program fail detection
			if not (begin_check and end_check):
				annotation['case'] = 5
			else :
				if annotation['uri'] == '' or not annotation['redirection']:
					annotation['case'] = 7
				if not match_entities(annotation, elu_result) :
					count = 0
					for subanswer in annotation['subanswers'] :
						subannotation = annotations[subanswer]
						if match_entities(subannotation, elu_result) :
							annotation['case'] = 6

							count += 1
					if not Parital_Answer:
						if count != len(annotation['subanswers']) :
							count = 0

					if len(annotation['subanswers']) > 0 :
						total_subannotation_score += Subanswer_Coeff * (float(count)/len(annotation['subanswers']))
						total_neg_subannotation_score += 1- Subanswer_Coeff * (float(count)/len(annotation['subanswers']))

		for entity in elu_result['entities'] :
		#	print str(entity['start_offset']) + " " + str((entity['start_offset']+ len(bytearray(entity['text'].encode('utf-8')))))
			if 'matched' not in entity.keys() :
				included = False
				for annotation in annotations :
					if annotation['begin'] <= entity['start_offset'] and annotation['end'] >= entity['start_offset']+ len(bytearray(entity['text'].encode('utf-8'))):
						included = True
						break
				#	elif not IS_ETRI and annotation['begin'] <= entity['start_offset'] and annotation['end'] >= entity['start_offset'] + len(entity['text']):
				#		included = True
				#		break

				if not included :
					cases[3] += 1
					print 'wrongly found : ' + entity['text'] + ' ' + entity['uri']
#					print entity['text']
#					print entity['selected_uri']

		for annotation in annotations :
			if annotation['included'] != -1 :
				continue
			if annotation['case'] == 4 :
				print 'no found : ' + annotation['text']

			cases[annotation['case']] += 1

	print 'total sent : ' +str(sent_count)
	print "total time : " + str(totaltime)
	print 'Correctly found exact entity : ' + str(cases[0])
	print 'Found entity candidate but too low score : ' + str(cases[1])
	print 'Found entity candidate but choose wrong candidate : ' + str(cases[2])
	print 'Found non-entity : ' + str(cases[3])
	print 'Could not detect entity : ' + str(cases[4])
	print 'Boundary problem : ' + str(cases[5])
	print 'Subannotation found : ' + str(cases[6])
	print 'No dbepdia entity : ' + str(cases[7]) + '\n'

	tp = cases[0] + total_subannotation_score
	fn = cases[4] + total_neg_subannotation_score

	fp = cases[1] + cases[2] + cases[3] + cases[5]

	precision = tp / (tp+fp)
	recall = tp / (tp + fn)

	print 'subanswer score : ' + str(total_subannotation_score)
	print 'true positive : ' + str(tp)
	print 'false negative : ' + str(fn)
	print 'false positive : ' + str(fp)
	print 'precision : ' + str(precision)
	print 'recall : ' + str(recall)

	print 'f1-score : ' +  str(2*precision*recall/(precision+recall))

	return totaltime

if __name__ == "__main__":


	alltime = 0

	if IS_NEW :
		ELU_ADDR = "http://143.248.135.150:2223/entity_full"
		IS_ETRI = True
		IS_UTF8 = True
	else :
		ELU_ADDR = "http://143.248.135.150:2221/entity_linking2"
		IS_ETRI = True
		IS_UTF8 = False

	for i in range(10) :
		loaded_answers, loaded_texts = load_answers()
		modify_answers(loaded_answers)
		alltime += check_performance(loaded_answers, loaded_texts)

		break
	alltime2 = 0
	total_line = 0

	"""
ELU_ADDR = "http://143.248.135.150:2222/entity_linking2";
IS_ETRI = False
IS_UTF8 = False
	#calculate time
	for (path, dir, files) in os.walk("gold_standard/"):
		for filename in files:
			f = open("gold_standard/"+filename)
			total_text = ''
			for line in f :
				cur_text = line.strip().replace('\xef\xbb\xbf','')
				if len(cur_text) > 2 :
					total_text += cur_text + ' '
					total_line+=1
				else :
					print total_text
					elu_result = json.loads(send_post(ELU_ADDR, json.dumps({'text':total_text})))
					alltime += elu_result['time_spent']
					alltime2 += elu_result['pos_time']
					total_text = ''

			if len(total_text) > 0 :
				print total_text
				elu_result = json.loads(send_post(ELU_ADDR, json.dumps({'text': total_text})))
				alltime += elu_result['time_spent']
				alltime2 += elu_result['pos_time']
				total_text = ''

			f.close()
	"""
	print alltime, alltime2, total_line
import urllib2
import json
import token_template

# match etri&hannanum offset to utf-8
def match_offset(data, text) :
	for sent in data :
		for morp in sent['morp'] :
			morp['position'] = len(text[:morp['position']].decode('utf-8'))

# match hannnanum to etri tagset
def match_tagset(data) :
	f = open('preprocessing/tagset_mapping.txt')
	mapping  = {}
	for line in f :
		cols = line.replace('\xef\xbb\xbf','').strip().split(' ')
		if len(cols) == 2 :
			mapping[cols[0]] = cols[1]

	f.close()

	for sent in data :
		for morp in sent['morp']:
			morp['type'] = mapping[morp['type']]

# Transforms morph analysis result for ELU
class MorphAnalyzer :

	chosen_parser = None

	# parser format
	# input : {"text": ~~}
	# output : [{"text":sentence1, "morp":[{"lemma":lemma1, "id":id1, "position":position1, "type":type1}, ... ]},
	#           {"text":sentence2}, ...]
	def __init__(self, parser):
		if parser == 'ko_espresso' :
			self.chosen_parser = self.call_espresso_parser
		elif parser == 'ko_etri' :
			self.chosen_parser = self.call_etri_parser
		elif parser == 'ko_hannanum' :
			self.chosen_parser = self.call_hannanum_parser
		elif parser == 'preprocessed' :
			self.chosen_parser = self.use_etri_parser_result
		else :
			print 'You must choose one of ko_espresso/ko_etri'
			raise Exception

	# call external parser service
	@staticmethod
	def call_espresso_parser(text) :
		service_url = 'http://143.248.135.60:31996/espresso_parser'
		headers = {
			'Content-type': 'application/json'
		}
		request = urllib2.Request(service_url, json.dumps({'text':text.encode('utf-8')}), headers)
		response = urllib2.urlopen(request)
		data = json.loads(response.read())['sentence']
		match_offset(data, text)
		return data

	@staticmethod
	def call_etri_parser(text) :
		service_url = 'http://143.248.135.20:31235/etri_pos'
		headers = {
			'Content-type': 'application/json'
		}
		try :
			text = text.encode('utf-8')
		except :
			pass
		request = urllib2.Request(service_url, json.dumps({'text':text}), headers)

		response = urllib2.urlopen(request)
		data = json.loads(response.read())
		match_offset(data, text)
		return data

	@staticmethod
	def use_etri_parser_result(result):
		data = result
		text = ""
		for sent in result:
			text += sent['text']
		text = text.encode('utf-8')
		for sent in data :
			for morp in sent['morp'] :
				morp['position'] = len(text[:morp['position']].decode('utf-8'))
		return data

	@staticmethod
	def call_hannanum_parser(text):
		service_url = 'http://143.248.135.60:42336/hannanum_pos'
		headers = {
			'Content-type': 'application/json'
		}
		try :
			text = text.encode('utf-8')
		except :
			pass
		request = urllib2.Request(service_url, json.dumps({'text': text}), headers)

		response = urllib2.urlopen(request)
		data = json.loads(response.read())
		match_tagset(data)
		return data


	"""
	# returns a list of morph token data for the given text & list of morps.
	# this list will have no tokens that have altered text.
	@staticmethod
	def word_to_tokens(text, morps):
		tokens_data = []

		offset = morps[0]['position']
		begin_index = -1
		end_index = 0
		next_begin = 0
		current_pos = []

		for morp_id in range(len(morps)) :
			cur_morp = morps[morp_id]
			if morp_id == len(morps)-1:
				next_begin = len(text) + offset
			else :
				next_begin = morps[morp_id+1]['position']

			if begin_index == -1 :
				begin_index = cur_morp['position']
			end_index = cur_morp['position'] + len(cur_morp['lemma'])
			current_pos.append(cur_morp['type'])

			# need to cut the current token
#			print str(cur_morp) + ' ' + str(begin_index) + ' ' + str(end_index) + ' ' + str(next_begin)
			if cur_morp['position'] + len(cur_morp['lemma']) <= next_begin :
				print text[begin_index-offset:end_index-offset]
				tokens_data.append((begin_index, end_index, text[begin_index-offset:end_index-offset], current_pos))
				begin_index = -1

#   	def add_token(self, start_offset, end_offset, text, pos, sentence_id, is_word_start, is_word_end):


		return tokens_data

	def find_index(self, morps, index, isBegin):
		result = -1
		for morp_id, morp in enumerate(morps) :
			if isBegin and morp['position'] == index :
				return morp_id
			elif not isBegin and morp['position'] + len(morp['lemma']) == index :
				result = morp_id

		if result != -1 :
			return result

		print 'index problem at find index'
		raise Exception

	# divide given text with space and '.'
	def split_text(self, text, morps):
		splitted_words = []
		index = 0
		for word in text.strip().split(' ') :
			if '.' in word :
				pos = word.find('.')
				splitted_words.append({'text': word[:pos + 1], 'begin':self.find_index(morps, index, True), 'end': self.find_index(morps, index+pos, False)+1})
				if len(word) != pos+1 :
					splitted_words.append({'text':word[pos+1:], 'begin':self.find_index(morps, index+pos+1, True), 'end':self.find_index(morps, index+len(word), False)})
			else :
				splitted_words.append({'text':word, 'begin':self.find_index(morps,index,True), 'end':self.find_index(morps, index+len(word), False)})
			index += len(word) + 1

		return splitted_words

	# gets the parse result for the given text.
	def text_to_tokens(self, text):
		parsed_sentences = self.chosen_parser(text)

		tokens = token_template.TokenList()

		for sentence_id, sentence_json in enumerate(parsed_sentences):
			morps = sentence_json['morps']

			words = self.split_text(sentence_json['text'], morps)
			for word_index, word in enumerate(words):

				word_tokens = self.word_to_tokens(word['text'], morps[word['begin']:word['end'] + 1])
				for token_index, word_token_data in enumerate(word_tokens):
					tokens.add_token(
						word_token_data[0],
						word_token_data[1],
						word_token_data[2],
						word_token_data[3],
						sentence_id,
						(token_index == 0),
						(token_index == len(word_tokens) - 1))

				tokens.increment_word_id()

		return tokens
	"""

	def pos_parse(self, text):
		return self.chosen_parser(text)

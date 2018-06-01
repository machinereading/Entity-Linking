from itertools import chain
import nltk
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelBinarizer
import sklearn
import pycrfsuite

import json
import os
import re
from pylab import *
import random as pyrandom 
from functools import partial


class EntityBoundary :
	def __init__(self, begin, end, confidence):
		self.begin = begin
		self.end = end
		self.confidence = confidence

	def __init__(self):
		self.begin = -1

	def __repr__(self):
		return json.dumps({'begin':self.begin, 'end':self.end})

class EntityBoundaryCRF(object) :
	def __init__(self, analyzer, model_file, surface_matcher):
		self.morph_analyzer = analyzer
		self.model_file = model_file
		self.train_features = []
		self.train_results = []
		self.trainer = pycrfsuite.Trainer(verbose=False)
		self.tagger = None
		self.surface_matcher = surface_matcher

	def tokenize_with_morph(self, result):
#		result = self.morph_analyzer.chosen_parser(text)
		tokens = []
		for sent in result :
			for morph in sent['morp'] :
				tokens.append({'lemma':morph['lemma'], 'pos':morph['type'], 'position':morph['position']})

		return tokens

	def generate_model(self):
		for feature, result in zip(self.train_features, self.train_results):
			self.trainer.append(feature, result)

		self.trainer.set_params({
			'c1': 1.0,  # coefficient for L1 penalty
			'c2': 1e-3,  # coefficient for L2 penalty
			'max_iterations': 50,  # stop earlier

			# include transitions that are possible, but not observed
			'feature.possible_transitions': True
		})

		self.trainer.train(self.model_file)

	def open_model(self):
		self.tagger = pycrfsuite.Tagger()
		self.tagger.open(self.model_file)

	def get_features(self, tokens, boundaries):
		features = []
		boundary_index = 0
		numbers = ['1','2','3','4','5','6','7','8','9','0']
		notnounprevtag = 'BGN'
		current_pos = ''
		for i in range(len(tokens)) :
			token = tokens[i]
			current_pos = token['pos']
			feature = ['bias']
#			feature = ['bias',
#			           'postag=' + token['pos'],
#			           'simpletag=' + token['pos'][0]]
			if i == 0 :
				feature.append('prevtag=' + 'BGN')
			else :
				feature.append('prevtag=' + tokens[i-1]['pos'])

			feature.append('notnounprevtag=' + notnounprevtag)
			if token['pos'][0] != 'N' :
				notnounprevtag = token['pos']

			while boundary_index < len(boundaries) and token['position'] >= boundaries[boundary_index]['end'] :
				boundary_index += 1

			if len(boundaries) > 0 and boundary_index < len(boundaries) :
				if token['position'] == boundaries[boundary_index]['start'] :
					feature.append('boundary=B')
				elif token['position'] + len(token['lemma']) > boundaries[boundary_index]['start'] :
					feature.append('boundary=I')
				else :
					feature.append('boundary=O')
			else :
				feature.append('boundary=O')

			if i != 0 :
				features[-1].append('nextboundary=' + feature[-1][-1])
			if i == len(tokens) - 1:
				feature.append('nextboundary=O')

			if i == len(tokens) - 1:
				feature.append('nexttag=' + 'END')
			else:
				if feature[-1][-1] == 'I' :
					current_pos = 'NNG'
					feature.append('nexttag=NNG') # for error management of nlp parser
				else :
					feature.append('nexttag=' + tokens[i + 1]['pos'])

			feature.append('postag=' + current_pos)
			feature.append('simpletag=' + current_pos[0])

			if i == 0 :
				feature.append('numberinprev=' + 'B')
			else :
				is_number = 'N'
				for number in numbers :
					if number in tokens[i-1]['lemma'] :
						is_number = 'Y'
				feature.append('numberinprev=' + is_number)

			features.append(feature)

		return features


	def get_boundaries(self, tokens, tags):
		newentity = EntityBoundary()
		boundaries = []
		for i in range(len(tokens)):
			token = tokens[i]
			if tags[i] == 'B' :
				if newentity.begin != -1:
					boundaries.append(newentity)
					newentity = EntityBoundary()
				newentity.begin = token['position']
				newentity.end = token['position'] + len(token['lemma'])
			elif tags[i] == 'I'  :
				newentity.end = token['position'] + len(token['lemma'])
			elif tags[i] == 'O':
				if newentity.begin != -1 :
					boundaries.append(newentity)
					newentity = EntityBoundary()

		if newentity.begin!= -1 :
			boundaries.append(newentity)

		return boundaries

	def get_results(self, tokens, entities):
		entity_index = 0
		for entity in entities :
			entity['start'] = int(entity['start'])
			entity['end'] = int(entity['end'])

		result_tags = []
		for token in tokens :
			while entity_index < len(entities) and token['position'] >= entities[entity_index]['end'] :
				entity_index += 1

			if len(entities) > 0 and entity_index < len(entities) :
				if token['position'] == entities[entity_index]['start'] :
					result_tags.append('B')
				elif token['position'] + len(token['lemma']) >  entities[entity_index]['start'] :
					result_tags.append('I')
				else :
					result_tags.append('O')
			else :
				result_tags.append('O')

		return result_tags

	def parse_traindata(self, raw_data, morph_analyzer):
		text = raw_data['text']
		pos_result = morph_analyzer.pos_parse(text)
		tokens = self.tokenize_with_morph(pos_result)

		self.train_features.append(self.get_features(tokens, self.surface_matcher.get_boundaries(pos_result, text)))
		self.train_results.append(self.get_results(tokens, raw_data['entities']))

	def train(self, dir, morph_analyzer) :
		p = re.compile("[0-9]*[.]txt")
		for root, dirs, files in os.walk(dir):
			for filename in files:
				if p.match(filename):
					f = open(dir+filename)
					data = f.read().replace('\xef\xbb\xbf','').replace('\n', ' ')
					print(filename)
					entities = json.loads(data)


					f.close()

					self.parse_traindata(entities, morph_analyzer)

		self.generate_model()

	def detect(self, text, pos_result):
		if self.tagger == None :
			print 'model not loaded'
			return None
		tokens = self.tokenize_with_morph(pos_result)
		result = self.tagger.tag(self.get_features(tokens, self.surface_matcher.get_boundaries(pos_result, text)))

		features = self.get_features(tokens, self.surface_matcher.get_boundaries(pos_result, text))
#		for i in range(len(tokens)) :
#			print tokens[i]['lemma']
#			print features[i]
#			print self.tagger.tag([features[i]])

		return self.get_boundaries(tokens, result)

pos_vec = ['JX', 'JKQ', 'XSA', 'JKC', 'ETN', 'JC', 'NNG', 'XSN', 'JKV', 'NNB', 'JKS', 'JKO', 'NP', 'NR',
		                'JKG', 'JKB', 'NNP', 'VA', 'XPN', 'EF', 'EC', 'ETM', 'VV', 'VX', 'IC', 'EP', 'SS', 'SP', 'SW',
		                'MM', 'SO', 'MAG', 'SL', 'MMG', 'MAJ', 'SF', 'SE', 'XSV', 'VCP', 'SN']
pos_vec = []
simple_vec = ['E', 'I', 'J', 'M', 'N', 'S', 'V', 'X']
simple_vec = ['J', 'N', 'X', 'O']
#https://arxiv.org/pdf/1508.01991v1.pdf
class EntityBoundaryLSTM(object) :
	def __init__(self, analyzer, surface_matcher):
		self.morph_analyzer = analyzer
		self.tagger = None
		self.surface_matcher = surface_matcher

	def pos_to_vec(self, pos):
		index1 = -1
		index2 = -1
		for pos_index, full_pos in enumerate(pos_vec) :
			if pos == full_pos :
				index1 = pos_index
		for pos_index, simple_pos in enumerate(simple_vec) :
			if pos[:1] == simple_pos :
				index2 = pos_index

		vec = [0]*(len(pos_vec) + len(simple_vec))
		vec[index2] = 1
		#vec[len(simple_vec) + index1] = 1


		return vec

	def tokenize_with_morph(self, result):
#		result = self.morph_analyzer.chosen_parser(text)
		tokens = []
		for sent in result :
			for morph in sent['morp'] :
				tokens.append({'lemma':morph['lemma'], 'pos':morph['type'], 'position':morph['position']})

		return tokens

	def get_features(self, tokens, boundaries):
		features = []
		boundary_index = 0
		numbers = ['1','2','3','4','5','6','7','8','9','0']
		for i in range(len(tokens)) :
			token = tokens[i]
			feature = self.pos_to_vec(token['pos'])

			while boundary_index < len(boundaries) and token['position'] >= boundaries[boundary_index]['end']:
				boundary_index += 1

			if len(boundaries) > 0 and boundary_index < len(boundaries) :
				if token['position'] == boundaries[boundary_index]['start'] :
					feature.append(1)
					feature.append(0)
					feature.append(0)
				elif token['position'] + len(token['lemma']) > boundaries[boundary_index]['start'] :
					feature.append(0)
					feature.append(1)
					feature.append(0)
				else :
					feature.append(0)
					feature.append(0)
					feature.append(1)
			else :
				feature.append(0)
				feature.append(0)
				feature.append(1)
			'''

			if i == 0 :
				feature.append(0)
			else :
				is_number = 1
				for number in numbers :
					if number in tokens[i-1]['lemma'] :
						is_number = -1
				feature.append(is_number)
			'''
			features.append(feature)

		return features

	def get_results(self, tokens, entities):
		entity_index = 0
		for entity in entities :
			entity['start'] = int(entity['start'])
			entity['end'] = int(entity['end'])

		result_tags = []
		for token in tokens :
			while entity_index < len(entities) and token['position'] >= entities[entity_index]['end'] :
				entity_index += 1

			if len(entities) > 0 and entity_index < len(entities) :
				if token['position'] == entities[entity_index]['start'] :
					result_tags.append([1, 0, 0]) #B
				elif token['position'] + len(token['lemma']) >  entities[entity_index]['start'] :
					result_tags.append([0, 1, 0]) #I
				else :
					result_tags.append([0, 0, 1]) # O
			else :
				result_tags.append([0, 0, 1]) # O

		return result_tags

	def parse_traindata(self, raw_data, morph_analyzer):
		text = raw_data['text']
		pos_result = morph_analyzer.pos_parse(text)
		tokens = self.tokenize_with_morph(pos_result)

		train_features = self.get_features(tokens, self.surface_matcher.get_boundaries(pos_result, text))
		train_results = self.get_results(tokens, raw_data['entities'])

#		for i in range(len(train_features)) :
	#		print train_features[i], train_results[i]
#		print train_features
#		print train_results
		for i in range(1000) :
			self.tagger.train(train_features, train_results)

	def train(self, dir, morph_analyzer) :
		self.tagger = ocrolib.lstm.BIDILSTM(len(pos_vec) + len(simple_vec) + 3,5,3)
		self.tagger.setLearningRate(1e-1, 0.0)

		count = 0
		for root, dirs, files in os.walk(dir):
			for filename in files:
				f = open(dir+filename)
				data = f.read().replace('\xef\xbb\xbf','').replace('\n', ' ')
				entities = json.loads(data)

				f.close()

				self.parse_traindata(entities, morph_analyzer)
				count += 1
#				if count == 10 :
#					break

	def get_boundaries(self, tokens, results):
		tags = []
		for result in results :
			if result[0] >= 0.5 and result[0] >= result[1]:
				tags.append('B')
			elif result[1] >= 0.5 :
				if len(tags) == 0 or tags[-1] == 'O' :
					tags.append('B')
				else :
					tags.append('I')
			else :
				tags.append('O')

		print results
		newentity = EntityBoundary()
		boundaries = []
		for i in range(len(tokens)):
			token = tokens[i]
			if tags[i] == 'B' :
				if newentity.begin != -1:
					boundaries.append(newentity)
					newentity = EntityBoundary()
				newentity.begin = token['position']
				newentity.end = token['position'] + len(token['lemma'])
			elif tags[i] == 'I':
				newentity.end = token['position'] + len(token['lemma'])
			elif tags[i] == 'O':
				if newentity.begin != -1:
					boundaries.append(newentity)
					newentity = EntityBoundary()

		if newentity.begin!= -1 :
			boundaries.append(newentity)

		return boundaries

	def detect(self, text, pos_result):
		if self.tagger == None :
			print 'model not loaded'
			return None
		tokens = self.tokenize_with_morph(pos_result)
		features = self.get_features(tokens, self.surface_matcher.get_boundaries(pos_result, text))
		result = self.tagger.predict(features)


		return self.get_boundaries(tokens, result)

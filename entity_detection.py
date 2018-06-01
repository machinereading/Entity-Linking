import json
import os
import sklearn
import sklearn.svm
from sklearn.externals import joblib
import collections
import math

class EntityCandidate(object) :
	current_id = 0

	def __init__(self, text, match, uri, confidence, score, relation, link, indirect):
		self.start = match.start
		self.end = match.end
		self.uri = uri
		self.text = text
		self.id = EntityCandidate.current_id
		self.confidence = confidence
		self.pos = match.pos
		self.score = score
		self.relation = relation
		self.link = link
		self.indirect = indirect

		EntityCandidate.current_id += 1

	def __repr__(self):
		return self.uri.encode('utf-8')
#		return json.dumps({'start':self.start, 'end':self.end, 'uri':self.uri, 'text':self.text,'id':self.id})

	def jsonize(self):
		return {'start_offset':self.start, 'end_offset':self.end, 'uri':self.uri, 'text':self.text,'id':self.id, 'confidence':self.confidence, 'score':self.score, 'relation':self.relation, 'link':self.link, 'indirect':self.indirect}


class FeatureManager(object) :
	@staticmethod
	def is_in_boundary(match, boundaries):
		for boundary in boundaries :
			if match.start >= boundary.begin and match.start < boundary.end :
				return 1
			elif match.end > boundary.begin and match.end <= boundary.end :
				return 1

		return 0

	@staticmethod
	def is_end_boundary(match, boundaries):
		for boundary in boundaries :
			if match.end == boundary.end :
				return 1
		return 0

	@staticmethod
	def is_before_boundary(match, boundaries):
		for boundary in boundaries :
			if match.end+1 == boundary.begin :
				return 1
		return 0

	@staticmethod
	def get_features(match, uri, uri_scores, uri_relation_score, boundaries):
		features = []
#		features.append(len(match.text))
		relation_score = uri_relation_score[uri][0]*2+uri_relation_score[uri][1]+uri_relation_score[uri][2]
		#features.append(math.log10(uri_scores[match.kb.name][uri]+1))
		#features.append(uri_relation_score[uri][1]) #wikilinks
		#features.append(uri_relation_score[uri][2]) # indirects
		features.append(FeatureManager.is_in_boundary(match, boundaries))
		features.append(FeatureManager.is_end_boundary(match, boundaries))
		features.append(FeatureManager.is_before_boundary(match, boundaries))

		if features[-1] == 0 and features[-2] == 0 :
			features.append(math.log10(uri_scores[match.kb.name][uri]+1)   * 0.1)
			features.append(relation_score*0.1) # relation
		else :
			features.append(math.log10(uri_scores[match.kb.name][uri]+ 1))
			features.append(relation_score) # relation

		return features


# entity training based on string matching
class EntityTrainer(object) :
	def __init__(self, model_file, config):
		self.model_file = model_file
		self.config = config
		self.feature_list = []
		self.is_entity_result = []

	def generate_model(self):
		clf = sklearn.svm.SVC(C=1.0, kernel='linear')
		clf.fit(self.feature_list, self.is_entity_result)

		joblib.dump(clf, self.model_file)

	# check if current match is correct
	def try_match(self, match, uri, answer):
		for annotation in answer:
			if annotation['start'] == match.start:
				if annotation['end'] == match.end and annotation['uri'] == uri:
					return True
		return False

	def preprocessing(self, text, result=None):
		#		print "morph analysis..."
		if result is None:
			pos_result = self.config.training_morph_analyzer.pos_parse(text)  # get text and make them to morph-tokens
		else:
			pos_result = self.config.morph_analyzer.pos_parse(result)
		boundaries = self.config.boundary_detector.detect(text, pos_result)
		#		print "finding entity candidates..."

		matches = self.config.surface_matcher.find_entity_candidates(pos_result, text)

		#		print "retrieving uri base scores..."
		uri_scores = self.config.entity_base_scorer.calculate_scores(matches)

		#		print "finding uri relations..."
		uri_relation_scores,relation_lists = self.config.relation_finder.find_relations(matches)

		return boundaries, pos_result, matches, uri_scores, uri_relation_scores, relation_lists

	def parse_traindata(self, raw_data):
		text = raw_data['text']
		answer = raw_data['entities']
#		pos_result = self.config.morph_analyzer.pos_parse(text)

#		boundaries = self.config.boundary_detector.detect(text)
#		matches = self.config.surface_matcher.find_entity_candidates(pos_result, text)
#		uri_scores = self.config.entity_base_scorer.calculate_scores(matches)
#		uri_relation_scores = self.config.relation_finder.find_relations(matches)
		boundaries, pos_result, matches, uri_scores, uri_relation_scores = self.preprocessing(text)

		for i in range(len(matches)):
			match = matches[i]
			uri_relation_score = uri_relation_scores[i]
			matched_uri = None
			is_entity = False
			for uri in match.uris :
				is_entity = self.try_match(match, uri, answer)
				if is_entity :
					matched_uri = uri
#					print article[match.start:match.end], match.text, uri, match.prev_pos, '/'.join(match.pos), match.pos[-1], match.next_pos, is_entity

			if is_entity :
				self.is_entity_result.append(1)
				self.feature_list.append(FeatureManager.get_features(match, matched_uri, uri_scores, uri_relation_score, boundaries))

			else :
				max_score = -1
				for uri in match.uris :
					if uri_scores[match.kb.name][uri] > max_score :
						max_score = uri_scores[match.kb.name][uri]
						matched_uri = uri

				self.feature_list.append(FeatureManager.get_features(match, matched_uri, uri_scores, uri_relation_score, boundaries))
				self.is_entity_result.append(-1)

 
	# self.train_results.append(self.get_results(tokens, raw_data['entities']))


class EntityDetector(object) :
	def __init__(self, model_file, config):
		self.train_features = []
		self.train_results = []
		self.model_file = model_file
		self.trainer = EntityTrainer(model_file, config)
		self.model = None

		#		self.feature_manager = FeatureManager()
		#		self.feature_manager.load_from_file(feature_file, model_file)

	def generate_model(self):
		self.trainer.generate_model()

	def open_model(self):
		self.model = joblib.load(self.model_file)

	def get_confidence(self, match, uri, pos_result, uri_scores, uri_relation_score, boundaries) :
		features = FeatureManager.get_features(match, uri, uri_scores, uri_relation_score, boundaries)
		result = self.model.predict(features)[0]
		confidence = self.model.decision_function(features)[0]
#		print match.text, uri
#		print result, confidence
#		print features

		return result, confidence

	def train(self, train_dir):
		count = 0
		for root, dirs, files in os.walk(train_dir):
			for filename in files:
				f = open(train_dir+filename)
				data = f.read().replace('\xef\xbb\xbf','').replace('\n', ' ')
				entities = json.loads(data)

				f.close()


				self.trainer.parse_traindata(entities)

				count += 1
				if count == 10  :
					break

		print 'generating model ...'
		self.generate_model()
		print 'model done'

	def detect_entities(self, pos_result, matches, uri_scores, uri_relation_scores, boundaries, lower_bound):
		entities = []
		for i in range(len(matches)) :
			max_uri = ''
			max_confidence = lower_bound
			match = matches[i]
			uri_relation_score = uri_relation_scores[i]
			match.detail_uris = []
			t = {}
			for uri in match.uris :
				result, entity_confidence = self.get_confidence(match, uri, pos_result, uri_scores, uri_relation_score, boundaries)

				if uri not in t.keys() : 
					detail_data ={}
					detail_data['id'] = match.uris.index(uri) + 1000*match.id
					detail_data['confidence'] = entity_confidence
					detail_data['uri'] = uri
					detail_data['score'] = math.log10(uri_scores[match.kb.name][uri]+1) 
					detail_data['relation'] = uri_relation_score[uri][0]
					detail_data['link'] = uri_relation_score[uri][1]
					detail_data['indirect'] = uri_relation_score[uri][2]
					match.detail_uris.append(detail_data)
					t[uri] = 1

				if max_confidence < entity_confidence :
					max_confidence = entity_confidence
					max_uri = uri
					max_score = math.log10(uri_scores[match.kb.name][uri]+1) 
					max_relation = uri_relation_score[uri][0]
					max_link = uri_relation_score[uri][1]
					max_indirect = uri_relation_score[uri][2]

			if max_confidence > lower_bound :
				entities.append(EntityCandidate(match.text, match, max_uri, max_confidence, max_score, max_relation, max_link, max_indirect))

		return entities

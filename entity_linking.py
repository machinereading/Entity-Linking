import sys
import random
import config
import json
import time

class Entity(object) :
	current_id = 0

	def __init__(self, text, match, uri, confidence):
		self.start = match.start
		self.end = match.end
		self.uri = uri
		self.text = text[self.start:self.end]
		self.id = Entity.current_id
		self.confidence = confidence
		self.pos = match.pos

		Entity.current_id += 1

	def __repr__(self):
		return self.uri.encode('utf-8')
#		return json.dumps({'start':self.start, 'end':self.end, 'uri':self.uri, 'text':self.text,'id':self.id})

	def jsonize(self):
		return {'start_offset':self.start, 'end_offset':self.end, 'uri':self.uri, 'text':self.text,'id':self.id, 'confidence':self.confidence}

class EntityLinker:
	def __init__(self, config_file) :
		self.config = config.Config(config_file)

	def add_type(self, entities):
		for entity in entities:
			entity['type'] = self.config.uri_type_cache[entity['uri']]
		return entities

	def entity_boundary(self, text):
		pos_result = self.config.morph_analyzer.pos_parse(text) #
		return self.config.boundary_detector.detect(text, pos_result)

	# get full inforamtion about the found entities
	def entity_full(self, preprocessed_text, lower_bound=-100):
		start_time = time.time()
		text = ""
		for sent in preprocessed_text:
			text += sent['text']

		print(text)
		boundaries, pos_result, matches, uri_scores, uri_relation_scores, relation_lists = self.config.entity_detector.trainer.preprocessing(text, preprocessed_text)
		entities = self.config.entity_detector.detect_entities(pos_result, matches, uri_scores, uri_relation_scores, boundaries, lower_bound)
		end_time = time.time()

		if self.config.overlapping :
			entities = self.filter_boundary(entities)

		entities = self.add_type(entities)

		match_data = []
		for match in matches : 
			match_data.append({'start':match.start, 'end':match.end, 'uris':match.detail_uris, 'id':match.id})

		return {'time_spent':end_time-start_time, 'entities':entities, 'matches':match_data, 'relations':relation_lists}

	def entity_linking(self, preprocessed_text, lower_bound=-1):
		result = self.entity_full(preprocessed_text, lower_bound)

		return result['entities']


	def popular_entity_linking(self, text, threshold=0.75) :
		pos_result = self.config.morph_analyzer.pos_parse(text)  # get text and make them to morph-tokens

		matches = self.config.surface_matcher.find_entity_candidates(pos_result, self.config.kbs)

		uri_scores = self.config.entity_base_scorer.calculate_scores(matches)

		entities = []
		for match in matches :
			max_score = 0
			max_uri = ''
			for uri in match.uris :
				uri_score = uri_scores[uri]
				if max_score < uri_score :
					max_score = uri_score
					max_uri = uri
			entities.append(Entity(match, max_uri))

		return self.filter_boundary(entities)

	def random_entity_linking(self, text, threshold=0.75) :
		pos_result = self.config.morph_analyzer.pos_parse(text)  # get text and make them to morph-tokens

		matches = self.config.surface_matcher.find_entity_candidates(pos_result, self.config.kbs)

		entities = []
		for match in matches :
			index = random.randInt(0, len(match.uris)-1)
			entities.append(Entity(match, match.uris[index]))

		return self.filter_boundary(entities)


	def filter_boundary(self, entities) :

		new_entities = []
		for entity in entities :
			is_inclosed = False
			for entity2 in entities :
				if entity != entity2 and entity.start >= entity2.start and entity.end <= entity2.end :
					is_inclosed = True
					break
			if not is_inclosed :
				new_entities.append(entity)
		entities = new_entities

		filtered_entities = []
		for i in range(len(entities)) :
			is_filtered = False
			for j in range(i+1, len(entities)) :
				if entities[i].end > entities[j].start :
					if entities[i].confidence < entities[j].confidence :
						is_filtered = True
						break
				else :
					break

			for j in range(i-1, 0, -1):
				if entities[j].end > entities[i].start:
					if entities[i].confidence < entities[j].confidence:
						is_filtered = True
						break
				else:
					break

			if not is_filtered :
				filtered_entities.append(entities[i].jsonize())

		return filtered_entities

"""
print 'el'
entity_linker = EntityLinker('configuration/ko-config.json')
#sample_text = u'덕혜옹주는 조선의 제26대 왕이자 대한제국의 초대 황제 고종과 귀인 양씨의 황녀이다. 덕혜라는 호를 하사받기 전까지 ‘복녕당 아기씨’로 불렸고, 1962년에 ‘이덕혜’로 대한민국의 국적을 취득하였다.일제강점기 조선 경성부 덕수궁에서 태어나 경성일출심상소학교에 재학 중에 일본의 요구에 따라 유학을 명분으로 도쿄로 보내져 여자학습원에서 수학하였다. 1931년에 옛 쓰시마 번주 가문의 당주이자 백작 소 다케유키와 정략 결혼을 하여 1932년에 딸 소 마사에를 낳았다. 1930년에 정신분열증 증세를 처음 보였으며 결혼 이후 병세가 악화되었다. 1946년부터 마쓰자와 도립 정신병원에 입원하였고, 1955년에 이혼하였다. 1962년에 대한민국으로 귀국하여 창덕궁 낙선재 내의 수강재에서 거주하다가 1989년에 사망하였다. 유해는 경기도 남양주시 금곡동의 홍유릉 부속림에 안장되었다.'
sample_text = u'덕혜옹주는 ‘복녕당 아기씨’로 불리다가 소 마사에를 낳은 귀인 양씨의 딸이다.'
boundaries = entity_linker.entity_boundary(sample_text)
for boundary in boundaries :
	print sample_text[boundary.begin:boundary.end]
"""
#print json.dumps(entity_linker.entity_linking(sample_text), ensure_ascii=False)
#print entity_linker.entity_linking(u'덕혜옹주는 조선의 제26대 왕이자 대한제국의 초대 황제 고종과 귀인 양씨의 황녀이다.')

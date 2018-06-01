import json
import collections
import bottle
from subprocess import call

class relation_retrieval(object):
	def __init__(self, config):
		self.relation = collections.defaultdict(lambda:[])
		self.link = collections.defaultdict(lambda:[])
		#self.predicates = collections.defaultdict(lambda:{})
		self.uri_scores = collections.defaultdict(lambda:0)
		self.indirect = {}

		self.kb_addr = config['kb_addr']
		self.kb_id = config['kb_id']
		self.kb_passwd = config['kb_passwd']
		self.graph_iri = config['graph_iri']
		self.entity_header = config['entity_header']
		self.header_len = len(self.entity_header)
		self.filename = config['local_dump']['filename']
		self.filename_link = config['local_dump']['filename_link']
		self.filename_label = config['local_dump']['label_cache']

		is_reload = config['local_dump']['is_reload']
		if is_reload :
			print 'reloading from virtuoso'
			call(["java", "-Dfile.encoding=UTF-8", "-jar", "getTriple.jar", self.kb_addr, self.kb_id, self.kb_passwd, self.graph_iri, self.entity_header, self.filename, self.filename_link, self.filename_label])
			print 'file done'

		print 'loading from local dump'
		self.load_from_file()

	def get_labels(self) :
		f = open(self.filename_label)
		labels = []
		for line in f :
			cols = line.replace('\xef\xbb\xbf','').decode('utf-8').strip().split('\t')
			if len(cols) > 1:
				labels.append({'uri':cols[0], 'label':cols[1]})

		f.close()

		return labels

	def load_from_file(self):
		f = open(self.filename)
		f2 = open(self.filename_link)

		count = 0
		for line in f :
			cols = line.split('\t')
			if len(cols) > 0 :
				subject = cols[0].decode('utf-8')
				object = cols[2].strip().decode('utf-8')

				self.uri_scores[object] += 1

				"""
				predicate = cols[1]
				if object not in self.predicates[subject].keys() :
					self.predicates[subject][object] = []
				if predicate not in self.predicates[subject][object] :
					self.predicates[subject][object].append(predicate)

				if subject not in self.predicates[object].keys():
					self.predicates[object][subject] = []
				if predicate not in self.predicates[object][subject]:
					self.predicates[object][subject].append(predicate)
				"""
				self.relation[subject].append(self.entity_header + object)
				self.relation[object].append(self.entity_header + subject)

				count += 1
				if count%100000 == 0 :
					print count

		print 'relation done'
		for line in f2:
			cols = line.split('\t')
			if len(cols) > 0 :

				subject = cols[0].decode('utf-8')
				object = cols[1].strip().decode('utf-8')

				self.uri_scores[object] += 1

				"""
				predicate = 'http://dbpedia.org/ontology/wikiPageWikiLink'

				if object not in self.predicates[subject].keys():
					self.predicates[subject][object] = []
				if predicate not in self.predicates[subject][object] :
					self.predicates[subject][object].append('http://dbpedia.org/ontology/wikiPageWikiLink')

				if subject not in self.predicates[object].keys():
					self.predicates[object][subject] = []
				if predicate not in self.predicates[subject][object]:
					self.predicates[object][subject].append('http://dbpedia.org/ontology/wikiPageWikiLink')
				"""

				self.link[subject].append(self.entity_header + object)
				self.link[object].append(self.entity_header + subject)

				count += 1
				if count % 100000 == 0:
					print count

		print 'wikilink done'

		f.close()
		f2.close()

	def remove_header(self, entity):
		return entity[self.header_len:]

	def get_relations(self, entity):
		entity = self.remove_header(entity)
		return {'link':self.link[entity], 'relation':self.relation[entity]}

	""""
	def get_predicates(self, entity1, entity2) :
		entity1 = self.remove_header(entity1)
		entity2 = self.remove_header(entity2)
		if entity2 in self.predicates[entity1] :
			return self.predicates[entity1][entity2]
		else : 
			return []
	"""
	def get_uri_score(self, entity):
		return self.uri_scores[self.remove_header(entity)]

	def get_indirect(self, entity1, entity2):
		replaced_entity1 = self.remove_header(entity1)
		replaced_entity2 = self.remove_header(entity2)
		count = 0
		for mid_entity in self.relation[replaced_entity1] :
			count += 1
			if mid_entity in self.relation[replaced_entity2] :
				return 1
			if count == 10 :
				break
		return 0
import re
# custom imports
import collections
import sparql_endpoint
import time


def generate_query(query_template, entity1, entity2):
	# the entities have to be encoded strings, for the query to work.
	encoded_entity1 = encoded_string(entity1)
	encoded_entity2 = encoded_string(entity2)

	query = re.sub(r'\[\[X1\]\]', "<" + encoded_entity1 + ">", query_template)
	query = re.sub(r'\[\[X2\]\]', "<" + encoded_entity2 + ">", query)
	return query

def encoded_string(s):
	if isinstance(s, unicode):
		return s.encode('utf-8')
	else:
		return s

# might be changed
def get_relation_count(kb, uri1, uri2):
	relation_query = generate_query(kb.relation_query, uri1, uri2)
#	print relation_query
	results = sparql_endpoint.query(kb.endpoint, kb.graph_iri, relation_query)

#	return len([r['pred'] for r in results]
	return results

class RelationFinder(object):
	def __init__(self, kbs, relation_window):
		self.kbs = kbs
		self.relation_window = relation_window

	def find_relations(self, matches):
		relations = []
		relation_lists = []
		kb_links = self.kbs[0].relation_retrieval.link
		kb_relations = self.kbs[0].relation_retrieval.relation
		header_len = len(self.kbs[0].entity_header)

		relation_sum = {}

		for i in range(len(matches)):
			match = matches[i]
			for uri in match.uris:
				relation_sum[uri] = [0,0,0]

		for i in range(len(matches)):
			match1 = matches[i]
			for j in range(i+1, len(matches)) :
				match2 = matches[j]
				if match2.word >= match1.word + self.relation_window:
					break
				if match1.kb == match2.kb :
					for uri1 in match1.uris :
						cur_relations = kb_relations[uri1[header_len:]]
						cur_links = kb_links[uri1[header_len:]]
						for uri2 in match2.uris :
							#indirect_relations = match1.kb.relation_retrieval.get_indirect(uri1, uri2)
							#relation_sum[uri1][2] += indirect_relations
							#relation_sum[uri2][2] += indirect_relations
							if uri2 in cur_links :
								relation_sum[uri1][1] += 1
								relation_data = {}
								relation_data['from'] = uri1
								relation_data['to'] = uri2
								relation_data['type'] = 'link'
								relation_lists.append(relation_data)
							if uri2 in cur_relations :
								relation_sum[uri1][0] += 1
								relation_data = {}
								relation_data['from'] = uri1
								relation_data['to'] = uri2
								relation_data['type'] = 'relation'
								relation_lists.append(relation_data)

			relations.append(relation_sum)

		return relations, relation_lists

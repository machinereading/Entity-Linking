import re
import collections


def get_uri_scores(kb, uri):
	relation_sum = kb.relation_retrieval.get_uri_score(uri)

	return relation_sum


class BaseUriScorer(object) :
	def __init__(self, kbs) :
		self.kbs = kbs

	def calculate_scores(self, matches):
		uri_scores = {}
		for kb in self.kbs :
			uri_scores[kb.name] = {}

		for match in matches:
			for uri in match.uris:
				uri_scores[match.kb.name][uri] = get_uri_scores(match.kb, uri)
		return uri_scores



# -*- coding: utf-8 -*-
import json


class LabelTreeTraverser(object):
    def __init__(self, kb, start):
        self.start = start
        self.end = start
        self.kb = kb
        self.node = kb.label_tree.root
        self.currently_matching_uris = None
        self.alive = True
        self.text = ''

    def add_space(self):
        self.end += 1

    def traverse_character(self, character):
        if not self.alive:
            pass

        self.end += 1
        self.node = self.node.traverse(character)
        self.text += character

        if self.node is None:
            # the traverse has ended.
            self.currently_matching_uris = None
            self.alive = False

        elif len(self.node.uris) > 0:
            # the traverse is currently on a valid surface form.
            self.currently_matching_uris = self.node.uris

        else:
            # the traverse has not ended, but the current text is not a valid surface form.
            self.currently_matching_uris = None

    """
	def traverse_with_token(self, token, token_id, is_first=False):
		if not self.alive:
			print 'alive token traversing...'
			pass

		self.end_token_id = token_id

		# traverse the tree with the given token.
		# if the token is the start of a word, whitespace must be before it.
		traverse_text = token.text
		if not is_first and token.is_word_start:
			traverse_text = u" " + token.text

		self.traverse_text += traverse_text

		self.node = self.node.traverse(traverse_text)

		if self.node is None:
			# the traverse has ended.
			self.currently_matching_uris = None
			self.alive = False

		elif self.node.uris is not None:
			# the traverse is currently on a valid surface form.
			self.currently_matching_uris = self.node.uris

		else:
			# the traverse has not ended, but the current text is not a valid surface form.
			self.currently_matching_uris = None
	"""

    def is_alive(self):
        return self.alive

    def is_currently_valid(self):
        return self.currently_matching_uris is not None


"""
class Matches(object):
	def __init__(self, tokens, candidates):
		self.matches = []
		self._uri_id = 0
		self._uri_id_to_match = []

		for candidate in candidates:
			self.matches.append(Match(tokens, candidate['start'], candidate['end'], self._URIs(candidate['uris'])))

	def _URIs(self, candidate_uris):
		uris = []
		for candidate_uri in candidate_uris:
			uris.append({
				'uri': candidate_uri,
				'id': self._uri_id})

			# make a uriID -> match link.
			self._uri_id_to_match.append(len(self.matches))

			self._uri_id += 1

		return uris

	def Match_of_uri_id(self, uri_id):
		return self.matches[self._uri_id_to_match[uri_id]]

	def __iter__(self):
		self.index = -1
		return self

	def next(self):
		if self.index == len(self.matches) - 1:
			raise StopIteration
		else:
			self.index += 1
			return self.matches[self.index]

	def __getitem__(self, i):
		return self.matches[i]
"""


class Match(object):
    id_count = 0

    def __init__(self, traverser, morps, ori_text):
        self.start = traverser.start
        self.end = traverser.end
        self.text = traverser.text
        self.word = traverser.word
        self.uris = traverser.currently_matching_uris
        self.kb = traverser.kb
        Match.id_count += 1
        self.id = Match.id_count

        self.prev_pos = ''
        self.next_pos = ''
        self.last_pos = ''
        self.pos = []
        self.is_end = False
        self.match_morps(morps, ori_text)

    def match_morps(self, morps, ori_text):
        isMatched = False
        isBegun = False
        morp_length = 3
        for i in range(len(morps)):
            morp = morps[i]
            if not isBegun and morp['position'] + len(morp['lemma']) > self.start:
                isMatched = True
                isBegun = True
                if morp['position'] == self.start:
                    if i != 0:
                        self.prev_pos = morps[i - 1]['type'][:morp_length]
                else:
                    self.prev_pos = morp['type'][:morp_length]

            if isMatched:
                if i == len(morps) - 1:
                    self.is_end = True
                elif self.start + len(self.text) < len(ori_text):
                    if ori_text[self.start + len(self.text)] == ' ' or (
                                        self.start + len(self.text) == morps[i + 1]['position'] and morps[i + 1]['type'][
                                0] == 'S'):
                        self.is_end = True

                self.pos.append(morp['type'][0])
                self.last_pos = morp['type'][:morp_length]
                if morp['position'] + len(morp['lemma']) == self.end:
                    while i != len(morps) - 1:
                        self.next_pos = morps[i + 1]['type'][:morp_length]
                        if self.next_pos[0] != 'n':
                            break
                        i += 1
                    return

                elif morp['position'] + len(morp['lemma']) > self.end:
                    self.next_pos = morp['type'][:morp_length]
                    if self.next_pos == u'nunk'[:morp_length]:  # revert unknown pos
                        remaining_text = morp['lemma'][morp['position'] - self.end:]
                        if remaining_text in [u'은', u'는', u'이', u'가', u'을', u'를', u'의', u'로', u'에', u'에서', u'로서', u'로써',
                                              u'과', u'이다']:
                            self.next_pos = u'junk'[:morp_length]
                        else:
                            self.next_pos = u'nunk'[:morp_length]
                    return

    def __repr__(self):
        return json.dumps({'start': self.start, 'end': self.end, 'uris': self.uris})


class SurfaceMatcher(object):
    def __init__(self, kbs):
        self.kbs = kbs

    # returns: Matches
    def find_entity_candidates(self, pos_result, ori_text):

        current_traversers = []
        candidates = []
        word_index = 0

        for sentence in pos_result:
            # every beginning of candidate must be the first character of a word
            offset = sentence['morp'][0]['position']
            morp_index = 0
            for word in sentence['text'].split(' '):
                if len(word) == 0:
                    continue

                # remove smbol
                symbol_offset = 0
                try:
                    while sentence['morp'][morp_index]['position'] < offset:
                        morp_index += 1
                    while sentence['morp'][morp_index]['type'] in ['SS', 'SP']:
                        morp_index += 1
                        symbol_offset = sentence['morp'][morp_index]['position'] - sentence['morp'][morp_index - 1][
                            'position']

                except IndexError as e:
                    print e

                if sentence['morp'][morp_index]['type'] == "NNG" and sentence['morp'][morp_index]['weight'] > 0.3:
                    pass

                elif sentence['morp'][morp_index]['type'] in ["NNP", "NNG"]:
                # add new root node
                    for kb in self.kbs:
                        current_traversers.append(LabelTreeTraverser(kb, offset + symbol_offset))

                    for char_index, character in enumerate(word):
                        # ignore symbol
                        if char_index < symbol_offset:
                            continue

                        # traverse a token
                        for traverser in current_traversers:
                            traverser.traverse_character(character)

                        # remove dead traversers
                        current_traversers = filter(lambda t: t.is_alive(), current_traversers)

                        # add to canddiates
                        for traverser in current_traversers:
                            if traverser.is_currently_valid():
                                traverser.word = word_index
                                candidates.append(Match(traverser, sentence['morp'], ori_text))
                else:
                    pass
                word_index += 1
                offset += len(word) + 1
                for traverser in current_traversers:
                    traverser.add_space()
        return candidates

    def get_boundaries(self, pos_result, text):
        boundaries = []
        large_boundaries = []
        for match in self.find_entity_candidates(pos_result, text):
            boundaries.append({'start': match.start, 'end': match.end})

        for i in range(len(boundaries)):
            included = False
            for j in range(len(boundaries)):
                if i != j and boundaries[i]['start'] >= boundaries[j]['start'] and boundaries[i]['end'] <= \
                        boundaries[j]['end']:
                    included = True
                    break
            if not included:
                large_boundaries.append(boundaries[i])

        return large_boundaries

        """
		for token_id, token in enumerate(tokens):

			# continue existing traversers with the current token.
			for traverser in current_traversers:
				traverser.Traverse_with_token(token, token_id)

			# add a new traverser with the current token.
			for kb in self.kbs :
				current_traversers.append(LabelTreeTraverser(token, token_id, kb))

			# remove traversers that are dead.
			current_traversers = filter(lambda t: t.is_alive(), current_traversers)

			# get the token boundary and uris of traversers that are currently valid.
			for traverser in current_traversers:
				if traverser.is_currently_valid():
#					print "(", traverser.start_token_id, traverser.end_token_id, "," + traverser.traverse_text + ")",
					candidates.append(Match(traverser.start_token_id, traverser.end_token_id, traverser.currently_matching_uris, traverser.kb))

		print candidates
		merged_candidates = self.merge_candidates(candidates)
		if not overlapping :
			return self.remove_overlap(merged_candidates)
		else :
			return merged_candidates
		if not overlapping:
			# we need to remove overlapping tokens.
			# we do this in left-to-right order, greedily taking the longest ones.
			current_end_threshold = -1
			independant_candidates = []


			for candidate in sorted(candidates, key=lambda c: (c['start'], c['end'] * -1)):
				if candidate['start'] > current_end_threshold:
					independant_candidates.append(candidate)
					current_end_threshold = candidate['end']

			return Matches(tokens, independant_candidates)

		else:
			return Matches(tokens, candidates)
		"""

# the token template to use when transforming morph analysis data into tokens.

class TokenList(object):
	def __init__(self):
		self.tokens = []
		self.current_word_id = 0

	def add_token(self, start_offset, end_offset, text, pos, sentence_id, is_word_start, is_word_end):
		self.tokens.append(Token(start_offset, end_offset, text, pos, sentence_id, self.current_word_id, is_word_start, is_word_end))

	def response_repr(self):
		return [token.response_repr() for token in self.tokens]

	def increment_word_id(self):
		self.current_word_id += 1

	def text_of_token_offsets(self, start, end):
		text = ''
		for token in self.tokens[start:end+1]:
			if token.is_word_start and len(text) > 0:
				text += ' '

			text += token.text

		return text

	def pos_of_token_offsets(self, start, end):
		pos = []
		for token in self.tokens[start:end+1]:
			pos += token.pos

		return pos
		# return [token.pos for token in self.tokens[start:end+1]]

	def __iter__(self):
		self.index = -1
		return self

	def next(self):
		if self.index == len(self.tokens) - 1:
			raise StopIteration
		else:
			self.index += 1
			return self.tokens[self.index]

	def __getitem__(self, i):
		return self.tokens[i]

	def __len__(self):
		return len(self.tokens)


class Token(object):
	def __init__(self, start_offset, end_offset, text, pos, sentence_id, word_id, is_word_start, is_word_end):
		# offsets are in utf-8.
		self.start_offset = start_offset
		self.end_offset = end_offset
		self.text = text
		self.pos = pos # a LIST of pos tags.
		self.sentence_id = sentence_id
		self.word_id = word_id
		self.is_word_start = is_word_start
		self.is_word_end = is_word_end

	def response_repr(self):
		return {
			'start_offset': self.start_offset,
			'end_offset': self.end_offset,
			'text': self.text,
			'pos': self.pos,
			'sentence_id': self.sentence_id,
			'word_id': self.word_id,
			'is_word_start': self.is_word_start,
			'is_word_end': self.is_word_end
		}
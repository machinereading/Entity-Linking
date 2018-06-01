# detects possible entity candidates within text, based on exact string matching.
# more specifically, we use tokens representing text.

# a character -> tree recursive tree structure.
# "abcd" -> ["a"]["b"]["c"]["d"]
class LabelTree(object):
	def __init__(self, labels):
		self.root = LabelTreeNode()

		load_status = 0
		print 'loading label tree'
		for label in labels:
			load_status += 1
			if load_status % 100000 == 0:
				print load_status,
			self.root.add_child(label['label'].replace(' ', ''), label['uri'])
		print ''
 
class LabelTreeNode(object):
	def __init__(self):
		self.children = {}
		self.uris = []

	def add_child(self, remaining_text, uri):
		if len(remaining_text) > 0:
			if remaining_text[0] not in self.children:
				self.children[remaining_text[0]] = LabelTreeNode()

			self.children[remaining_text[0]].add_child(remaining_text[1:], uri)
		else:
			self.uris.append(uri)

	# traverse through tree node
	def traverse(self, character):
		if character not in self.children:
			return None
		else:
			return self.children[character]

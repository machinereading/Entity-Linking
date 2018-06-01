import json
import morph_analyzer
import label_tree
import exact_matching
import sparql_endpoint
import base_scoring
import relation_finding
import codecs
import relation_retrieval
import entity_detection
import entity_boundary
from collections import defaultdict


class KB:
    def __init__(self, kb):
        self.name = kb['name']
        self.entity_header = kb['entity_header']
        self.relation_retrieval = relation_retrieval.relation_retrieval(kb)

        self.label_tree = label_tree.LabelTree(self.relation_retrieval.get_labels())


class Config:
    def __init__(self, config_file):
        f = open(config_file)
        raw_data = f.read().replace('\xef\xbb\xbf', '')
        config = json.loads(raw_data)

        f.close()

        self.uri_type_cache = defaultdict(lambda : [])
        f = codecs.open(config['kb'][0]['local_dump']['uri_type_cache'], 'r', encoding="utf-8")
        for line in f.readlines():
            if line == "":
                break
            uri, type_, _ = line.split("\t")
            self.uri_type_cache[uri].append(type_)
        f.close()

        self.morph_analyzer = morph_analyzer.MorphAnalyzer(config['morph_analyzer'])
        self.training_morph_analyzer = morph_analyzer.MorphAnalyzer('ko_etri')
        self.overlapping = config['overlapping']

        self.kbs = []
        for kb in config['kb']:
            for prev_kb in self.kbs:
                if kb['name'] == prev_kb.name:
                    print 'same kb name exists'
                    raise Exception
            self.kbs.append(KB(kb))

        self.surface_matcher = exact_matching.SurfaceMatcher(self.kbs)
        self.entity_base_scorer = base_scoring.BaseUriScorer(self.kbs)
        self.relation_finder = relation_finding.RelationFinder(self.kbs, config['relation_window'])

        boundary_config = config['boundary']
        if boundary_config['method'] == 'crf':
            self.boundary_detector = entity_boundary.EntityBoundaryCRF(self.morph_analyzer, boundary_config['model'],
                                                                       self.surface_matcher)
        elif boundary_config['method'] == 'lstm':
            self.boundary_detector = entity_boundary.EntityBoundaryLSTM(self.morph_analyzer, self.surface_matcher)
        else:
            print 'boundary detection method must be CRF or LSTM'
            raise Exception

        if boundary_config['method'] == 'crf':
            if boundary_config['train']:
                print 'training boundary detector ... '
                self.boundary_detector.train(boundary_config['train_dir'], self.training_morph_analyzer)
            print 'opening boundary detection model'
            self.boundary_detector.open_model()
        else:
            print 'training boundary detector ... '
            self.boundary_detector.train(boundary_config['train_dir'], self.training_morph_analyzer)

        print 'boundary detection ready'

        dm_config = config['disambiguation']
        self.entity_detector = entity_detection.EntityDetector(dm_config['model'], self)
        if dm_config['train']:
            print 'training dm ... '
            self.entity_detector.train(dm_config['train_dir'])
        print 'opening dm model'
        self.entity_detector.open_model()

        """

		self.relation_window = config['disambiguation']['relation_window']
		self.feature_file = config['disambiguation']['feature']
		self.disambiguation_model = config['disambiguation']['model']

		self.answer_dir = config['answer_dir']
		self.text_dir = config['text_dir']

		self.surface_matcher = exact_matching.SurfaceMatcher(self.kbs)
		self.entity_base_scorer = base_scoring.BaseUriScorer(self.kbs)
		self.relation_finder = relation_finding.RelationFinder(self.kbs, self.relation_window)
		self.entity_detector = entity_detection.EntityDetector(self.feature_file, self.disambiguation_model)
		"""

        """
		entity_relations.Config.Init(config)
		entity_base_scoring.Config.Init(config)
		features.Config.Init(config)
		features.Features.Init()


		exact_surface_matching.Config.Init(labels)
		del labels
		"""

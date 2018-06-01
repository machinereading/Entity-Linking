from bottle import post, run, response, request
import json
import entity_linking

# define configuration
config_file = 'configuration/ko-config.json'
host_addr = '143.248.135.60'
port_num = 2229

# base class
entity_linker = None

# for CORS (to solve cross-domain issue)
def enable_cors(fn):
	def _enable_cors(*args, **kwargs):
		# set CORS headers
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)

	return _enable_cors

# retrieve all information of the found entities
@post('/entity_full', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_str = request.body.read()
	try :
		request_str = request_str.decode('utf-8')
	except :
		pass
	request_json = json.loads(request_str)

	result_str = json.dumps(entity_linker.entity_full(request_json['text']))

	return result_str

# retrieve list of found entities
@post('/entity_linking', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_str = request.body.read()
	try:
		request_str = request_str.decode('utf-8')
	except:
		pass
	request_json = json.loads(request_str)

	"""
	if 'text' in request_json :
		text = request_json['text']
		if 'lower_bound' in request_json :
			lower_bound = request_json['lower_bound']
			return json.dumps(entity_linker.entity_linking(text, lower_bound))
		return json.dumps(entity_linker.entity_linking(text))
	else :
		return json.dumps({'error':'no text given'})
	"""
	return json.dumps(entity_linker.entity_linking(request_json))

# retrieve list of entity candidate boudnaries
@post('/entity_boundary', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_str = request.body.read()
	try:
		request_str = request_str.decode('utf-8')
	except:
		pass
	request_json = json.loads(request_str)

	if 'text' in request_json :
		text = request_json['text']
		if 'lower_bound' in request_json :
			lower_bound = request_json['lower_bound']
			return json.dumps(entity_linker.entity_boundary(text, lower_bound))
		return json.dumps(entity_linker.entity_boundary(text))
	else :
		return json.dumps({'error':'no text given'})

@post('/random_entity_linking', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_json = json.loads(request.body.read())
	if 'text' in request_json:
		text = request_json['text']
		if 'lower_bound' in request_json:
			lower_bound = request_json['lower_bound']
			return json.dumps(entity_linking.random_entity_linking(text, lower_bound))
		return json.dumps(entity_linking.random_entity_linking(text))
	else:
		return json.dumps({'error': 'no text given'})

@post('/popular_entity_linking', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_json = json.loads(request.body.read())
	if 'text' in request_json:
		text = request_json['text']
		if 'lower_bound' in request_json:
			lower_bound = request_json['lower_bound']
			return json.dumps(entity_linking.popular_entity_linking(text, lower_bound))
		return json.dumps(entity_linking.popular_entity_linking(text))
	else:
		return json.dumps({'error': 'no text given'})

# retrieve all relation triples of the found entities
@post('/entity_graph', method=['OPTIONS', 'POST'])
@enable_cors
def do_request():
	if not request.content_type.startswith('application/json'):
		return 'Content-type:application/json is required.'

	request_json = json.loads(request.body.read())
	if 'text' in request_json :
		text = request_json['text']
		if 'lower_bound' in request_json :
			lower_bound = request_json['lower_bound']
			return json.dumps(entity_linker.entity_triple(text, lower_bound))
		return json.dumps(entity_linker.entity_triple(text))
	else :
		return json.dumps({'error':'no text given'})

entity_linker = entity_linking.EntityLinker(config_file)
#print json.dumps(entity_linker.entity_full(unicode("덕혜옹주는 조선의 제26대 왕이자 대한제국의 초대 황제 고종과 귀인 양씨의 황녀이다. 덕혜라는 호를 하사받기 전까지 ‘복녕당 아기씨’로 불렸고, 1962년에 ‘이덕혜’로 대한민국의 국적을 취득하였다.", 'utf-8')))


#sample_text = u'덕혜옹주는 조선의 제26대 왕이자 대한제국의 초대 황제 고종과 귀인 양씨의 황녀이다. 덕혜라는 호를 하사받기 전까지 ‘복녕당 아기씨’로 불렸고, 1962년에 ‘이덕혜’로 대한민국의 국적을 취득하였다.일제강점기 조선 경성부 덕수궁에서 태어나 경성일출심상소학교에 재학 중에 일본의 요구에 따라 유학을 명분으로 도쿄로 보내져 여자학습원에서 수학하였다. 1931년에 옛 쓰시마 번주 가문의 당주이자 백작 소 다케유키와 정략 결혼을 하여 1932년에 딸 소 마사에를 낳았다. 1930년에 정신분열증 증세를 처음 보였으며 결혼 이후 병세가 악화되었다. 1946년부터 마쓰자와 도립 정신병원에 입원하였고, 1955년에 이혼하였다. 1962년에 대한민국으로 귀국하여 창덕궁 낙선재 내의 수강재에서 거주하다가 1989년에 사망하였다. 유해는 경기도 남양주시 금곡동의 홍유릉 부속림에 안장되었다.'

print 'service'
run(host=host_addr, port=port_num, debug=True)
#except KeyError as keyerr:
#	print 'given configuration is not suitable.'
#	print keyerr
#except IOError as ioerr:
#	print 'no such file'
#	print ioerr
#except Exception as exception:
#	print exception

# Entity Linking Module

한국어 문장에 대한 ETRI parsing 결과를 입력받아 문장에서 발견된 모든 한국어 디비피디아 개체를 연결하여 출력하는 모듈입니다.

## 시작하기
아래 지침을 따라 모듈을 서버에 띄우고, 해당 주소로 HTTP POST 형식을 통해 원하는 문장을 입력할 수 있습니다.

### 시작하기에 앞서
본 프로젝트는 Python 2.7.6으로 개발되었습니다.

### 필요한 라이브러리 (Python)
+ bottle
+ nltk
+ pycrfsuite
+ pylab
+ scikit-learn

### 설치하기
설치하기 전, service.py 파일 line 6,7을 해당 모듈을 띄우는 서버의 host address와 port 번호로 바꿔주세요.

예시)

    host_addr = 'example.com'
    port_num = '9999'


필요한 라이브러리를 모두 설치한 뒤 다음 명령어로 모듈을 서버에 띄우세요.

    python service.py

### 입력과 출력 형식
입력 (json) : 한국어 문장 (혹은 문단)의 "etri_parser" 결과
method : POST 
Content-type : application/json

**입력 예시)**

입력하고 싶은 문장

```javascript
{"text" : "이순신은 조선의 장군이다."}
```

실제 입력

```javascript
[
  {
    "word": [
      {
        "text": "이순신은",
        "begin": 0,
        "end": 1,
        "type": "",
        "id": 0
      },
      {
        "text": "조선의",
        "begin": 2,
        "end": 3,
        "type": "",
        "id": 1
      },
      {
        "text": "장군이다.",
        "begin": 4,
        "end": 7,
        "type": "",
        "id": 2
      }
    ],
    "WSD": [
      {
        "begin": 0,
        "end": 0,
        "weight": 2.91226,
        "text": "이순신",
        "scode": "02",
        "position": 0,
        "type": "NNP",
        "id": 0
      },
      {
        "begin": 1,
        "end": 1,
        "weight": 1,
        "text": "은",
        "scode": "00",
        "position": 9,
        "type": "JX",
        "id": 1
      },
      {
        "begin": 2,
        "end": 2,
        "weight": 2.2,
        "text": "조선",
        "scode": "05",
        "position": 13,
        "type": "NNP",
        "id": 2
      },
      {
        "begin": 3,
        "end": 3,
        "weight": 1,
        "text": "의",
        "scode": "00",
        "position": 19,
        "type": "JKG",
        "id": 3
      },
      {
        "begin": 4,
        "end": 4,
        "weight": 8.1,
        "text": "장군",
        "scode": "04",
        "position": 23,
        "type": "NNG",
        "id": 4
      },
      {
        "begin": 5,
        "end": 5,
        "weight": 1,
        "text": "이",
        "scode": "01",
        "position": 29,
        "type": "VCP",
        "id": 5
      },
      {
        "begin": 6,
        "end": 6,
        "weight": 1,
        "text": "다",
        "scode": "00",
        "position": 32,
        "type": "EF",
        "id": 6
      },
      {
        "begin": 7,
        "end": 7,
        "weight": 1,
        "text": ".",
        "scode": "00",
        "position": 35,
        "type": "SF",
        "id": 7
      }
    ],
    "chunk": [],
    "text": "이순신은 조선의 장군이다.",
    "morp": [
      {
        "lemma": "이순신",
        "type": "NNP",
        "id": 0,
        "weight": 0.9,
        "position": 0
      },
      {
        "lemma": "은",
        "type": "JX",
        "id": 1,
        "weight": 0.0520511,
        "position": 9
      },
      {
        "lemma": "조선",
        "type": "NNP",
        "id": 2,
        "weight": 0.0441558,
        "position": 13
      },
      {
        "lemma": "의",
        "type": "JKG",
        "id": 3,
        "weight": 0.0987295,
        "position": 19
      },
      {
        "lemma": "장군",
        "type": "NNG",
        "id": 4,
        "weight": 0.869676,
        "position": 23
      },
      {
        "lemma": "이",
        "type": "VCP",
        "id": 5,
        "weight": 0.0177525,
        "position": 29
      },
      {
        "lemma": "다",
        "type": "EF",
        "id": 6,
        "weight": 0.353579,
        "position": 32
      },
      {
        "lemma": ".",
        "type": "SF",
        "id": 7,
        "weight": 1,
        "position": 35
      }
    ],
    "NE": [
      {
        "begin": 0,
        "end": 0,
        "weight": 0.520932,
        "text": "이순신",
        "common_noun": 0,
        "type": "PS_NAME",
        "id": 0
      },
      {
        "begin": 2,
        "end": 2,
        "weight": 0.295715,
        "text": "조선",
        "common_noun": 0,
        "type": "LCP_COUNTRY",
        "id": 1
      },
      {
        "begin": 4,
        "end": 4,
        "weight": 0.680429,
        "text": "장군",
        "common_noun": 0,
        "type": "CV_POSITION",
        "id": 2
      }
    ],
    "SRL": [],
    "ZA": [],
    "phrase_dependency": [
      {
        "begin": 0,
        "end": 0,
        "weight": 0,
        "text": "이순신은",
        "key_begin": 0,
        "label": "NP_SBJ",
        "sub_phrase": [],
        "head_phrase": 1,
        "element": [],
        "id": 0
      },
      {
        "begin": 0,
        "end": 2,
        "weight": 0,
        "text": "P#0@SBJ은 조선의 장군이다.",
        "key_begin": 1,
        "label": "S",
        "sub_phrase": [
          0
        ],
        "head_phrase": -1,
        "element": [
          {
            "text": "조선의 장군",
            "begin": 2,
            "end": 4,
            "ne_type": "",
            "label": "NP"
          },
          {
            "text": "이다.",
            "begin": 5,
            "end": 7,
            "ne_type": "",
            "label": "VP"
          }
        ],
        "id": 1
      }
    ],
    "dependency": [
      {
        "head": 2,
        "weight": 0.822925,
        "text": "이순신은",
        "label": "NP_SBJ",
        "id": 0,
        "mod": []
      },
      {
        "head": 2,
        "weight": 0.765701,
        "text": "조선의",
        "label": "NP_MOD",
        "id": 1,
        "mod": []
      },
      {
        "head": -1,
        "weight": 0.553482,
        "text": "장군이다.",
        "label": "VNP",
        "id": 2,
        "mod": [
          0,
          1
        ]
      }
    ],
    "relation": [],
    "SA": [],
    "reserve_str": "",
    "id": 0,
    "morp_eval": [
      {
        "target": "이순신은",
        "m_begin": 0,
        "result": "이순신/NNG+은/JX",
        "m_end": 1,
        "id": 0,
        "word_id": 0
      },
      {
        "target": "조선의",
        "m_begin": 2,
        "result": "조선/NNG+의/JKG",
        "m_end": 3,
        "id": 1,
        "word_id": 1
      },
      {
        "target": "장군이다.",
        "m_begin": 4,
        "result": "장군/NNG+이/VCP+다/EF+./SF",
        "m_end": 7,
        "id": 2,
        "word_id": 2
      }
    ]
  }
]
```

출력 (json) : 해당 문장 (혹은 문단)에서 감지된 모든 한국어 디비피디아 개체, 고유 id, 신뢰도, uri, score, type 목록

**출력 예시)**

```javascript
[
  {
    "text": "이순신",
    "start_offset": 0,
    "relation": 1,
    "end_offset": 3,
    "indirect": 0,
    "id": 41582,
    "confidence": 0.9911806629553932,
    "uri": "http://ko.dbpedia.org/resource/이순신",
    "score": 2.603144372620182,
    "link": 1,
    "type": [
      "http://www.w3.org/2002/07/owl#Thing",
      "http://wikidata.dbpedia.org/resource/Q5",
      "http://xmlns.com/foaf/0.1/Person",
      "http://dbpedia.org/ontology/Agent",
      "http://dbpedia.org/ontology/MilitaryPerson",
      "http://dbpedia.org/ontology/Person",
      "http://schema.org/Person",
      "http://wikidata.dbpedia.org/resource/Q215627",
      "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Agent",
      "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#NaturalPerson",
      "http://www.wikidata.org/entity/Q5",
      "http://www.wikidata.org/entity/Q215627"
    ]
  },
  {
    "text": "조선",
    "start_offset": 5,
    "relation": 0,
    "end_offset": 7,
    "indirect": 0,
    "id": 41583,
    "confidence": 1.0188057499689163,
    "uri": "http://ko.dbpedia.org/resource/조선",
    "score": 4.009663316679379,
    "link": 0,
    "type": []
  }
]
```

## Contact
김지호 (hogajiho@kaist.ac.kr)

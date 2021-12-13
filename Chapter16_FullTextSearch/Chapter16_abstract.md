# 16장 : Full-Text Search
- 사용자들이 관심있는 포스트들을 검색해서 찾을 수 있는 기능
- 다른 검색 엔진을 사용하려면 app/search.py 만 재작성
- 다른 모델에 대해서 검색기능을 지원하고 싶으면, 모델 클래스에 SearchableMixin 클래스 상속하고, \_\_searchable\_\_ 속성으로 인덱싱할 필드만 지정

## Full-Text Search Engine에 대한 소개
- full-text search 는 관계형 db처럼 표준화되어있지 않고, 여러 오픈소스 엔진들이 있음. Elasticsearch, Apache Solr, Whoosh, Xapian, Sphinx. 그리고 텍스트 검색을 지원하는 몇 개 db들이 있음. (SQLite, MySQL, PostgreSQL, MongoDB, CouchDB) 모두 Flask 앱에서 동작할 수 있음
- 그 중 Elasticsearch가 인기있음. (로그 인덱싱에 ELK 스택(Elasticsearch, Logstash, Kibana) 중에 E 임) 관계형 db의 검색 성능을 사용하는 것도 좋은 선택이지만, SQLAlchemy는 이 기능을 지원하지 않음. 그래서 raw SQL 문으로 검색하거나, SQLAlchemy 와 공존할 수 있는 high-level 텍스트 검색 패키지를 찾아야함.
- Elasticsearch를 사용하되, 다른 엔진으로 쉽게 바꿀 수 있도록 모든 text 인덱싱과 검색 함수들을 구현할 것임. 그래서 하나의 모듈(app/search.py)에서 몇 개 함수만 재작성해서 다른 엔진을 사용할 수 있도록 함.

## Elasticsearch 설치하기
1) https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html 에서 Elasticsearch 설치. 설치 후 http://localhost:9200 로 들어가면 서비스에 대한 기본 정보들을 json 형태로 볼 수 있음

2) 파이썬으로 Elasticsearch를 다루기 위한 파이썬 클라이언트 라이브러리 설치
```shell
pip install elasticsearch
```


## Elasticsearch 튜토리얼
- flask shell 에서 실행
1) Elasticsearch 클래스 생성 : 커넥션 url을 인자로 넘겨줌
```shell
>>> from elasticsearch import Elasticsearch
>>> es = Elasticsearch('http://localhost:9200')
```

2) 'my_index' 인덱스에 데이터 삽입 : Elasticsearch 의 데이터는 **indexes** 로 쓰여지고, 각 데이터는 JSON object 임
```shell
>>> es.index(index='my_index', id=1, body={'text': 'this is a test'})
>>> es.index(index='my_index', id=2, body={'text': 'a second test'})
```

3) 인덱스 이용하여 검색
```shell
>>> es.search(index='my_index', body={'query': {'match': {'text': 'this test'}}})
```

4) 검색 결과 분석
score 가 높을 수록 많이 일치함. 완벽하게 'this test'와 동일해야 1이 되고, 'this is a test' 면 0.8 정도 나옴. 결과의 [hits][hits]안에 나열됨
```json
{
    'took': 309,
    'timed_out': False,
    '_shards': {'total': 1, 'successful': 5, 'skipped': 0, 'failed': 0},
    'hits': {
        'total': {'value': 2, 'relation': 'eq'},
        'max_score': 0.82713,
        'hits': [
            {
                '_index': 'my_index',
                '_type': '_doc',
                '_id': '1',
                '_score': 0.82713,
                '_source': {'text': 'this is a test'}
            },
            {
                '_index': 'my_index',
                '_type': '_doc',
                '_id': '2',
                '_score': 0.1936807,
                '_source': {'text': 'a second test'}
            }
        ]
    }
}
```

5) 인덱스 삭제
```shell
>>> es.indices.delete('my_index')
```

## Elasticsearch 설정
1) config.py 에 ELASTICSEARCH_URL 변수 추가
```python
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
```
만약 .env에 ELASTICSEARCH_URL 변수가 없으면 None으로 세팅함=Elasticsearch를 사용하지 않겠음=그래서 앱을 돌릴 때 반드시 Elasticsearch 서비스를 돌리지 않아도 되게 함. 특히 단위 테스트를 돌릴 때의 용이함을 위함.

2) .env 파일에 ELASTICSEARCH_URL 변수 설정  
```env
ELASTICSEARCH_URL=http://localhost:9200
```

3) app/\_\_init\_\_.py 에서 app에 elasticsearch 속성 추가  
Elasticsearch 는 Flask extension으로 래핑되어있지 않음. 그래서 app/\_\_init\_\_.py 에서 전역으로 먼저 Elasticsearch 인스턴스를 생성할 수 없고, create_app(app factory func)에서 app 인스턴스가 생성된 후에 elasticsearch 속성을 추가해줌
```python
app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None
```

## Full-Text Search Abstraction
- Elasticsearch를 다른 엔진으로 쉽게 바꾸고 싶고, Post 모델만 인덱싱하고 싶지는 않기 때문에, 다른 모델로 쉽게 확장할 수 있는 구조를 만듦. 그래서 검색 기능을 위해 **abstraction** 을 생성

1) app/models.py 의 Post 클래스에 \_\_searchable\_\_ 클래스 속성 추가 : 어떤 모델, 어떤 필드가 인덱싱될 지 알려주는 일반적인 방법을 만듦. 
```python
class Post(db.Model):
    __searchable__ = ['body']  # Post 모델의 'body' 필드가 인덱싱되어야 함
```
이건 단순히 변수만 추가해준 것이고, 인덱싱 함수을 일반적인 방법으로 쓸 수 있도록 도움주는 것임.

2) app/search.py 모듈을 추가하고, Elasticsearch index 관련된 모든 코드를 담음. 그래서 나중에 다른 엔진으로 바꿀 때는 이 파일의 함수만 재작성하면 됨

    1. add_to_index(index, model) : full-text index에 엔트리 추가  
    2. remove_from_index(index, model) : 블로그 포스트 삭제 시 인덱스에서 엔트리 삭제  
    3. query_index(index, query, page, per_page) : 검색 쿼리 실행 후 검색 결과가 페이징 처리됨. 
    
```python
def add_to_index(index, model):
    if not current_app.elasticsearch:  # elasticsearch 속성이 없어도 에러 안 남
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)
    # model.id 사용 : SQLAlchemy 와 Elasticsearch의 id에 같은 값을 씀. 만약 기존에 쓰고 있는 id를 사용하는 경우, 업데이트됨.

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)
    # 저장할 때 model.id로 인덱스 엔트리 id를 지정해줬기 때문에, 삭제 시에도 model.id 로 지우면 됨

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
        # multi_match : 여러 필드에 걸쳐서 검색 가능
        # field * : 모든 필드
        # from, size : 전체 검색 결과 중에 어떤 서브셋이 반환되어야 하는가
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']  # 결과의 총 개수
```

## SQLAlchemy 에 Search 통합하기
- 문제점 및 해결방안
1) 결과가 숫자 id의 리스트로 반환됨 : 숫자 리스트를 db에서 해당하는 데이터로 추출해서 바꿔야함  
> DB에서 해당 포스트들을 읽을 수 있는 SQLAlchemy 쿼리를 생성함.(쿼리 하나로 효율적으로 이걸 하는 건 구현하기 어려운 부분이 있음) 
2) 포스트가 생성되거나 삭제될 때마다 앱이 인덱싱 호출을 해야 함 : 만약 SQLAlchemy 쪽에서 변화가 생겼는데 인덱싱 콜이 누락된 버그는 쉽게 찾기 어렵고, 이 버그가 생길 수록 두 db는 sync가 더 안 맞음. 그래서 SQLAlchemy db에서 변화가 생기면 자동으로 인덱싱 콜이 되는 게 더 나은 방안임.  
> SQLAlchemy **events** 로부터 Elasticsearch index를 업데이트  
예를 들어 세션이 커밋될 때마다 SQLAlchemy로부터 invoke되는 app 내부 함수를 만들어서, 그 함수 안에서 Elasticsearch index를 업데이트

- 두 가지 해결 책을 구현하기 위해 **mixin class** 사용 : Flask-Login의 UserMixin 클래스를 User 클래스가 상속받게 했던 것처럼, own SearchableMixin 클래스를 만들어서 Post 클래스가 상속받게 함. SearchableMixin 클래스에서 관련된 full-text 인덱스를 자동으로 다루는 기능을 넣어서, SQLAlchemy와 Elasticsearch 간에 "glue" 레이어 역할을 하게 함
- app/models.py 에 SearchableMixin 클래스 추가, db.event.listen 2개 추가, Post 클래스가 SearchableMixin 클래스 상속. 

```python
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        ## Flask-SQLAlchemy 가 관련 테이블에 부여한 이름으로 인덱싱을 하는 게 컨벤션임
        ...
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))  # when = [(30, 0), (4, 1)]
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total
        # 매칭 확률이 높은 순서로 id가 추출되었기 때문에, 그 순서대로 post들도 정렬해주기 위해서 db.case 문 사용
        # where post.id in ('30', '4')
        # order by
        #     case post.id
        #         when '30' THEN 0
        #         when '4' THEN 1
        #     END

    @classmethod
    def before_commit(cls, session):  # 커밋되고 나면 세션에서 다 사라지기 때문에, 커밋 전에 백업함
        session._changes = {
            'add': list(session.new),  # 세션에서 새로 추가된 것들을 'add' 라는 리스트로 저장해둠
            ...
        }

    @classmethod
    def after_commit(cls, session):  # 세션이 성공적으로 커밋되었을 때 불림
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        ...
        session._changes = None 
    ...

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
```
- **@classmethod** : 특정 인스턴스가 아닌 클래스와 관련됨. 그래서 self가 아니라 cls로 클래스를 넘겨줌. Post.search('안녕', 1, 5)로 바로 부름

## 검색 Form
- 위는 상당히 generic한 내용이고, 이제 블로그 post에 대한 자연어 검색을 앱에 통합할 차례
- 웹 기반 검색의 표준적인 방법은 URL의 쿼리 스트링으로 q라는 인자를 사용하는 것. URL에 키워드를 넣음으로써, 다른 사람에게 url을 공유해서 그 사람이 클릭하더라도 같은 검색 결과를 보여줄 수 있음
- 그러므로 다른 form들과는 달리, 검색 form에 대해서는 **GET request**로 보냄. 그리고 네비게이션 바 안에 검색 폼을 두어서, 앱의 모든 페이지에서 검색 폼이 보여지도록 함

1) app/main/forms.py 에 SearchForm 추가 : 엔터 누르면 검색되게 하려고 submit 안 넣음

```python
class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        # formdata : 어디서 Flask-WTF가 form 제출을 받았는지
        # POST일 때는 request.form , GET일 때는 request.args 에 Flask가 인자를 써줌
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
            # 다른 사람이 링크를 클릭해도 검색이 동작하게 하려면, CSRF 꺼야 함
        super(SearchForm, self).__init__(*args, **kwargs)

```

2) app/main/routes.py 의 before_app_request()에 g.search_form = SearchForm() 추가 : 모든 템플릿에 SearchForm을 주기 위해서 이 방식을 사용. Flask의 **g** 변수는 request가 살아있는 동안 데이터를 보관함. 그러므로 before_request를 거쳐서 Flask가 요청된 url을 다룰 수 있는 view func을 invoke시킬 때까지도 g 변수는 유지됨. g 변수는 각 요청에 대해 private한 저장공간을 보장함. 

3) app/templates/base.html 에 g.search_form 나타냄 : current_user.is_authenticated 가 아닌 상태에서 에러 페이지로 갔을 경우에는 g.search_form 이 없을 수 있으므로, {% if g.search_form %} 를 반드시 체크해야 함

## Search View 함수
- app/main/routes 에 '/search' url 매핑 추가 : 빈 form으로 제출하는 경우 explore로 리다이렉트

- form validation 체크
1) POST : form.validate_on_submit()
2) GET : form.validate(). 어떻게 데이터가 제출되었는지는 체크하지 않고, 필드값만 validate함

- app/templates/search.html 파일 추가

※ app/main/forms.py 에서 kwargs['csrf_enabled'] = False 로 적용해주었는데도 g.search_form.validate() 이 false로 나오는 문제가 있었음 >> Flask-WTF version 문제임. 1.XX 버전을 uninstall하고, 0.15.1 버전으로 install하니 해당 config가 정상 동작함.

## 이 챕터에서 추가된 파일
- app/search.py
- app/templates/search.html

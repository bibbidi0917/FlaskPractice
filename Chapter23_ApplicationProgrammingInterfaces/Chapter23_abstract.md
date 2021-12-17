# 23장 Application Programming Interfaces (APIs)

- 지금까지는 웹 브라우저가 유일한 클라이언트였음
- 만약 안드로이드 또는 iOS 앱을 만든다면? 
1) 웹 뷰 컴포넌트로 간단한 앱을 만듦. 이 방식은 웹 브라우저로 여는 것보다 베네핏이 적음
2) native app을 만듦. 그런데 이 앱이 HTML 페이지만 리턴하는 서버랑 어떻게 interact할 수 있는가? 이 문제를 API가 도와줄 수 있음
- API : 앱으로 들어오는 low level 엔트리 포인트들로 디자인된 HTTP 루트들의 집합. 웹 브라우저에 의해 소비되는, HTML을 리턴하는 루트와 view 함수를 정의하는 게 아님. API는 앱의 **resources**를 클라이언트가 직접 다룰 수 있도록 함. 어떻게 사용자들에게 정보를 보여줄 것인가에 대한 결정에서 벗어남  
예를 들어 API 가 사용자와 블로그 포스트 정보를 클라이언트에게 줄 수 있고, 사용자들에게 기존 포스트를 수정하게 할 수도 있음. 오직 데이터 레벨에서이고, HTML 로직과 절대 섞이지 않음. Chapter 14에서 만든 /translate 를 보면, 사용자에게 그 정보를 어떻게 보여줄 지에 대한 책임은 클라이언트에 넘기고, JSON 형식만 응답함.
- JSON 루트들이 API 같은 느낌을 주기는 하지만, 이것들도 모두 브라우저에서 돌아가는 웹 앱으로 디자인된 것임. 예를 들어 스마트폰으로 이 루트를 이용하려면 로그인된 사용자여야 하고, 로그인은 현재 HTML 폼으로만 할 수 있음
- 이 챕터에서는 웹 브라우저에 의존하지 않는 API 들을 만들어서, 클라이언트 종류에 어떠한 가정도 없는 microblog를 만들고자 함

## API 디자인의 기반인 'REST'
- REST API(Representational State Transfer) : Dr.Fielding의 박사 논문에서 제안된 아키텍처
- 주어진 API가 REST인지 아닌지에 대해서 치열한 논쟁이 있음
1) REST 순수주의자 : REST API 는 반드시 6가지 특징을 가져야 함. Dr.Fielding.
2) REST 실용주의자 : Dr.Fielding 의 논문을 가이드라인이나 추천 정도로 생각함. 대부분의 API가 실용주의적으로 구현되었음. Facebook, GitHub, Twitter 등 소위 "big players"의 API 들도 마찬가지임. 소프트웨어 업계에서는 실용적 관점에서 REST를 봄

- 6개의 원칙
1) Client-Server  
> 클라이언트와 서버의 역할이 구별되어야 함. TCP 기반의 HTTP 프로토콜처럼 클라이언트와 서버가 전송계층 위에서 분리된 프로세스로 통신해야 함

2) Layered System  
> 클라이언트가 서버와 통신할 때, 실제 서버가 아니라 매개체와 연결됨. 클라이언트 입장에서는 서버와 직접 연결되는지 여부가 서버에 요청을 보내는 방식에 영향이 없어야 함. 심지어는 자신이 타겟 서버와 연결되었는지 여부도 알 필요가 없음   
마찬가지로 서버는 클라이언트의 요청을 클라이언트한테 직접 받지 않고, 매개체로부터 받음. 그래서 서버 입장에서 연결의 상대방이 클라이언트라고 생각해서는 안 됨  
중간 노드를 추가하는 것이 앱 아키텍처를 크게 만들고, 로드 밸런서, 캐시, 프록시 서버들을 이용해서 많은 양의 요청을 처리할 수 있는 복잡한 네트워크를 만듦

3) Cache
> 이 원칙은 layered system을 확장한 것으로, 시스템 성능을 향상시키기 위해서 자주 받은 요청의 응답들을 서버나 매개체에 캐싱함. 예를 들어 웹 브라우저의 캐시 레이어에서는 이미지 같은 파일을 계속 요청보내지 않도록 함  
응답이 클라이언트에 돌아갈 때 매개체가 그 응답을 캐싱할 수 있도록, 타겟 서버가 **cache controls**를 사용하는 것을 명시해야 함. 그러나 보안상 운영에 배포되는 API 들은 암호화를 사용해야 하기 때문에, 매개 노드가 SSL 연결을 종료시키거나 복호화, 재암호화를 하지 않는 한, 캐싱이 매개 노드에서 되지는 않음. 

4) Code On Demand
> 서버가 클라이언트에게 주는 응답으로 실행가능한 코드를 제공해야한다는 선택적인 요구사항임. 클라이언트가 돌릴 수 있는 실행가능한 코드의 종류에 대해서 서버와 클라이언트가 동의를 가지고 있어야 하기 때문에, API 에서는 드물게 쓰임. 서버가 웹 브라우저에게 JavaScript 코드를 반환하면 된다고 생각할 수 있지만, REST는 웹 브라우저 클라이언트에만 위한 것이 아님. 예를 들어 JavaScript를 실행하는 것은 iOS 나 안드로이드 기기 클라이언트에는 복잡합만 가져올 뿐임

5) Stateless
> REST API 는 클라이언트가 요청을 보낼 때마다 재호출되는 클라이언트의 상태를 저장하면 안 됨. 웹 개발에서 공통적으로 쓰이는, 앱의 페이지를 돌아다닐 때 사용자를 "기억"하는 매커니즘들이 사용될 수 없음. 매 요청은 서버가 클라이언트를 식별하고 인증할 수 있는 정보를 포함하고 있어야 함. 그리고 서버가 클라이언트 연결과 관련된 어떠한 데이터도 db나 다른 형태의 저장장치에 저장해서는 안 됨  
> stateless 서버가 scale하기 편함. 그래서 로드 밸런서 뒤에 그냥 서버 인스턴스만 여러 개 띄우면 됨. 만약에 서버가 클라이언트의 상태를 저장한다면, 여러 서버가 그 상태에 접근하고 업데이트하는 방법, 또는 **sticky sessions**처럼 특정 클라이언트가 같은 서버에 의해 요청이 처리되도록 보장하는 방법 등을 찾아야 함  
ex) /translate 루트는 Flask-Login의 @login_required 데코레이터에 의존하고 있기 때문에, **RESTful**이 아님. Flask 사용자 세션에서 사용자의 로그인 상태를 저장하고 있는 것이므로.

6) Uniform Interface

> 1. unique resource identifiers  
각 리소스에 대해 유일한 URL 할당. 예를 들어 '/api/users/\<user-id>' 이 URL은 \<user-id> 가 db 테이블의 pk 값. 대부분 API 에서 잘 구현되어있음

> 2. resource representations  
서버와 클라이언트가 리소스에 대한 정보를 교환할 때, 반드시 합의된 포맷을 사용해야 함. 대부분의 모던 API 들에서는 JSON 포맷이 리소스 표현에 사용됨. 하나의 API 가 여러 리소스 표현 포맷을 지원할 수도 있고, 이 경우에는 HTTP 프로토콜의 **content negotiation** 옵션이 사용되어 클라이언트와 서버가 모두 선호하는 포맷으로 합의할 수 있음

> 3. self-descriptive messages  
클라이언트와 서버 간에 교환된 요청된 응답은 상대방이 필요한 모든 정보를 담고 있어야 함. 전형적인 예로 HTTP 요청 함수는 클라이언트가 서버의 어떤 오퍼레이션을 실행하고 싶은지 나타나있음. 'GET' 요청은 클라이언트가 리소스에 대해 정보를 얻고 싶다는 것, 'POST' 요청은 클라이언트가 새로운 리소스를 만들고 싶다는 것, 'PUT' 또는 'PATCH' 요청은 존재하는 리소스에 대해서 수정하고 싶다는 것, 'DELETE' 요청은 리소스를 삭제하고 싶다는 것임. 타겟 리소스는 요청 URL, HTTP 헤더의 부가 정보, URL의 쿼리 스트링, 요청 body에 명시되어있음

> 4. hypermedia  
API 구현에 잘 쓰이지 않고, REST 순수주의자들만 사용함. 앱의 리소스들은 모두 상호 관련되어있기 때문에, 이 관계들이 리소스 표현에 포함되어야 한다는 것임. 그래서 (링크 클릭해서 다음 페이지로 가는 것처럼) 클라이언트가 관계들을 traversing해서 새로운 리소스를 찾을 수 있도록 함  
클라이언트가 리소스에 대한 사전 지식없이 API를 사용할 수 있고, hypermedia link를 따라가면서 리소스들에 대해 배울 수 있다는 것임. 이 hypermedia 구현이 어려운 이유는, HTML 과 XML 과는 달리 JSON 포맷은 표준적으로 링크를 포함하는 방식이 정의되어있지 않기 때문임. 그래서 커스텀 구조를 사용하거나 JSON_API, HAL, JSON_LD 같은 JSON 확장자를 사용해야 함

## API Bluprint 구현하기
- 사용자와 관련된 모든 함수들을 API로 구현해보고자 함
- 모든 API 루트들을 담은 새로운 블루프린트만듦. app/api 폴더 만듦
- app/api/\_\_init\_\_.py 파일 생성
- app/api/users.py 에 6개 함수 생성
- app/api/errors.py 에 bad_request() 생성
- app/api/tokens.py 에 get_token(), revoke_token() 생성. 인증 서브시스템이 정의될 예정. 웹 브라우저를 사용하지 않는 클라이언트가 로그인할 수 있는 다른 방법을 제공함
- app/\_\_init\_\_.py 에 api 블루프린트 등록

## 사용자를 JSON 객체로 표현하기
- API를 구현할 때 가장 먼저 생각해야 하는 포인트가, 리소스를 어떻게 표현할 지 결정하는 것임
- 사용자에 대한 API를 구현할 것이므로, 사용자 리소스를 어떻게 표현할지 결정해야 하고, 아래와 같이 JSON 방식을 사용하기로 함. 서버에 실제 리소스가 정의된 양식과  매칭될 필요가 없음

```json
{
    "id": 123,
    "username": "susan",
    "password": "my-password",  //신규 사용자 등록 시에만 사용(db에 해시값만 있고, 비밀번호는 절대 리턴되지 않음)
    "email": "susan@example.com", //본인 정보 요청 시에만 리턴되도록
    "last_seen": "2021-06-20T15:04:27Z",
    "about_me": "Hello, my name is Susan!",
    "post_count": 7, // 이하 세 필드는 db에는 없는 "가상" 필드
    "follower_count": 35,
    "followed_count": 21,
    "_links": { // hypermedia requirements. 나중에 포스트 관련 API가 추가된다면, 사용자가 작성한 포스트 목록에 대한 링크도 여기에 추가되어야 함
        "self": "/api/users/123",
        "followers": "/api/users/123/followers",
        "followed": "/api/users/123/followed",
        "avatar": "https://www.gravatar.com/avatar/..."
    }
}
```

- JSON 형식의 좋은 점은 Python 딕셔너리나 리스트로 항상 변환할 수 있다는 것. Python의 json 패키지는 Python 데이터구조 <-> JSON 변환을 관장함. 
- app/models.py 의 User 클래스에 to_dict() 추가 : 사용자 정보를 Python 딕셔너리로 반환(나중에 JSON으로 변환될 예정)

```python
def to_dict(self, include_email=False):
        data = {
            ...
            '_links': {  # 이렇게 url_for 를 사용하여 표기 가능
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128)
            }
        }
       ...
```

- app/models.py 의 User 클래스에 from_dict() 추가 : 클라이언트가 사용자 representation을 넘기면 서버가 파싱해서 User object로 변환

```python
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])  # setattr()으로 값 세팅
        ...
```

## 사용자 집합을 표현하기
- app/models.py 에 PaginatedAPIMixin 클래스 생성 : Chapter 16에서 SearchableMixin 클래스를 만들어서, full-text index가 필요한 모델이 상속받을 수 있도록 함. 마찬가지로 PaginatedAPIMixin 이라는 공통 클래스를 만들어서, API 에서 페이지 관련 표현이 필요하다면 이 클래스를 상속받도록 할 것임  
※ User 클래스 앞 쪽에 PaginatedAPIMixin 클래스가 위치해야 함

```python
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                ...
            },
            '_links':{
                # endpoint='api.get_users'를 넘겨서
                # url_for('api.get_users', id=id, page=page)
                # id 같은 변수는 **kwargs 로 받음
                 'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
               ...
            }
        }
```

- app/models.py 의 User 클래스가 PaginatedAPIMixin 상속

## 에러 다루기
- Chapter7에서 정의한 에러 페이지들은 웹 브라우저로 앱과 통신하는 사용자에게만 적절함. API가 에러를 반환할 때는, 클라이언트 앱이 쉽게 인터프리트할 수 있는 "기계 친화적"인 에러 타입이 필요함. 그래서 JSON 형태로 반환.

- app/api/errors.py 에 error_response() 추가, bad_response는 error_response(400, message) 를 반환하도록 함. error(HTTP 에러코드에 대한 설명), message가 JSON으로 들어있고, status_code가 세팅된 response가 반환됨

## 사용자 리소스 Endpoints
- app/api/users.py 의 함수 채우기

### 1. 사용자 1명 정보 반환
```python
@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())
```
- get_or_404(id) : 반환될 정보가 없으면 None을 반환하는 게 아니라, 요청을 abort하고 404에러를 반환. 그냥 get()을 사용하면 쿼리의 결과가 있는지 체크를 해야함

- api 테스트 방법 2가지
1) 웹 브라우저 주소창에 http://localhost:5000/api/users/1 입력
2) HTTPie : API 요청을 보낼 수 있는 command-line HTTP 클라이언트 설치

```shell
(venv) $ pip install httpie
```

- 첫번째 터미널에서 서버 띄우고, 두번째 터미널에서 다음과 같이 요청

```shell
> http GET http://localhost:5000/api/users/2

HTTP/1.0 200 OK
Content-Length: 362
Content-Type: application/json
Date: Fri, 17 Dec 2021 01:54:42 GMT
Server: Werkzeug/2.0.2 Python/3.8.6

{
    "_links": {
        "avatar": "https://www.gravatar.com/avatar/9006ce0f8f021b22cd25154cea63a07f?d=identicon&s=128",
        "followed": "/api/users/2/followed",
        "followers": "/api/users/2/followers",
        "self": "/api/users/2"
    },
    "about_me": "bibbidi bobbidi boo~!!!!",
    "followed_count": 1,
    "follower_count": 2,
    "id": 2,
    "last_seen": "2021-12-16T07:00:51.000858Z",
    "post_count": 20,
    "username": "jihyun"
}
```

### 2. 사용자 집합 정보 반환

- PaginatedAPIMixin 클래스의 to_collection_dict() 사용
- get_users(), get_followers(), get_followed()

```python
@bp.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    # per_page 를 100으로 제한 걸어줌
    
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)
```

```python
@bp.route('/users/<int:id>/followers', methods=['GET'])
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                  'api.get_followers', id=id)
    # query 부분에 user.followers 와 같은 관계가 들어갈 수 있음
    return jsonify(data)
```

※ base.html 에 보면 'user.followers.count()' 할 수 있듯이, user.followers도 쿼리 역할임

### 3. 새로운 사용자 등록하기

```python
@bp.route('/users', methods=['POST'])
def create_user():
    ...
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201  # 201 Created = 요청이 성공적으로 처리되었으며, 자원이 생성되었음
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    # 201 response 의 Location 헤더는 새로 생성된 리소스의 URl임
    return response
```

```shell
> http POST http://localhost:5000/api/users username=alice password=dog email=alice@example.com "about_me=Hello, my name is Alice!"

HTTP/1.0 201 CREATED  # 201로 응답되고
Content-Length: 360
Content-Type: application/json
Date: Fri, 17 Dec 2021 03:58:03 GMT
Location: http://localhost:5000/api/users/7  # Location으로 리소스 위치 파악
Server: Werkzeug/2.0.2 Python/3.8.6
...
```

### 4. 사용자 수정하기
- update_user()

```shell
> http PUT http://localhost:5000/api/users/7 "about_me=Hi, I am Miguel"
```

## API Authentication
- AuthN=Authentication=인증, AuthZ=Authorization=AuthZ=권한부여
- 현재는 update_user() 같은 함수가 모든 클라이언트에 열려있음. 요청한 액션이 해당 사용자에게 허락되는지 여부를 검증하는 과정이 필요함. 이러한 API endpoint들을 보호하기 위해서 Flask-Login의 @login-required 데코레이터를 사용하지만 문제가 있음  
인증되지 않은 사용자를 발견했을 때, 사용자를 HTML 로그인 페이지로 이동시킴. HTML 또는 로그인 페이지 개념이 없는 API에서는, 클라이언트가 invalid한 credential을 보내거나 credential을 안 보냈을 경우 서버가 그 요청을 401 상태코드로 거절해야 함. API 클라이언트가 웹 브라우저이거나 API 클라이언트가 리다이렉트를 다룰 수 있다거나, HTML 로그인 폼을 렌더링할 수 있다고 서버가 가정할 수 없음. API 클라이언트가 401 상태 코드를 받으면, 클라이언트는 서버 측의 로직은 몰라도 credential이 필요하다는 것은 앎

### 1. User 모델의 Token
- 클라이언트가 API로 통신하고 싶을 때, 클라이언트가 username과 password로 인증하면서 임시 토큰을 요청함 > 클라이언트가 토큰을 넘기면서 API 요청을 보냄. 토큰이 만료되면 새로운 토큰이 요청되어야 함

- app/models.py 의 User 모델에 토큰 관련 필드 2개(token, token_expiration), 함수 3개(get_token=토큰반환, revoke_token, check_token) 추가

```python
def get_token(self, expires_in=3600):
    now = datetime.utcnow()
    if self.token and self.token_expiration > now + timedelta(seconds=60):
        return self.token  # 만료까지 적어도 1분은 남았다면 이 토큰 그대로 반환
    
    self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
    # base64로 인코딩해서, 모든 문자가 읽을 수 있는 범위에 있도록 함
    
    self.token_expiration = now + timedelta(seconds=expires_in)
    db.session.add(self)
    return self.token

def revoke_token(self):
    # 만료시간을 현재로부터 1초 전으로 넣어서, 토큰을 invalid하게 만듦
    self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

@staticmethod
def check_token(token):
    user = User.query.filter_by(token=token).first()
    if user is None or user.token_expiration < datetime.utcnow():
        return None
    return user
```

- db 마이그레이션

※ Base 64 : 화면에 표시되는 ASCII 영역의 문자들로만 이루어진 일련의 문자열로 바꾸는 인코딩 방식

### 2. Token 요청
- API의 진정한 파워는 스마트폰 앱, 브라우저 기반 SPA 같은 standalone 클라이언트들이 백엔드 서비스에 접근할 때 나옴. 전통적인 웹 앱에서는 로그인 폼을 쓰지만, 이 특화된 클라이언트들은 API 서비스에 접근하기 위해 토큰을 요청하는 것부터 시작함

1) Flask-HTTPAuth : 토큰 인증이 사용될 때 client와 서버 간 상호작용을 단순화하기 위해서 이 extension을 사용함. API 친화적인 여러 인증 매커니즘을 지원함. 클라이언트가 표준적인 Authorization HTTP 헤더 안에 사용자의 credential을 보내는 HTTP Basic Authentication을 사용할 예정. 

```shell
(venv) $ pip install flask-httpauth
```

2) app/api/auth.py : Flask-HTTPAuth 를 통합하기 위해서 앱이 2개의 함수를 제공해야 함. 아래 두 함수는 Flask-HTTPAuth 에 데코레이터를 통해 등록되고, 인증 과정 동안 extension이 필요로 할 때 자동으로 불림  

```python
basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user  # 인증된 사용자는 basic_auth.current_user() 로 사용가능.

@basic_auth.error_handler
def basic_auth_error(status):  # 인증 실패 시 에러 응답을 반환함
    return error_response(status)  # invalid 인증의 경우 401 상태 코드로 반환됨
```

3) app/api/tokens.py : get_token 함수를 토큰 검색 루트로 만듦

```python
@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required  # Flask-HTTPAuth 에게 @basic_auth.verify_password 로 인증을 검증하고, credential이 valid할 때만 이 함수를 돌릴 수 있게 함
def get_token():
    token = basic_auth.current_user().get_token()  # User클래스의 get_token()
    db.session.commit()  # User클래스의 get_token()에서는 db.session.add(self)만 해주기 때문에, 여기서 커밋해줌
    return jsonify({'token': token})
```

- auth 정보를 보내지 않은 경우, 401 에러

```shell
> http POST http://localhost:5000/api/tokens

HTTP/1.0 401 UNAUTHORIZED
Content-Length: 25
Content-Type: application/json
Date: Fri, 17 Dec 2021 05:19:11 GMT
Server: Werkzeug/2.0.2 Python/3.8.6
WWW-Authenticate: Basic realm="Authentication Required"

{
    "error": "Unauthorized"
}
```

- auth 정보를 보낸 후, 200 응답 및 토큰값 정상 회신

```shell
> http --auth <username>:<password> POST http://localhost:5000/api/tokens

HTTP/1.0 200 OK
Content-Length: 45
Content-Type: application/json
Date: Fri, 17 Dec 2021 05:20:39 GMT
Server: Werkzeug/2.0.2 Python/3.8.6

{
    "token": "<certain-token>"
}
```

### 3. 토큰으로 API Routes 보호하기
- API endpoint에 토큰 검증 부분 추가. Flask-HTTPAuth extention의 HTTPTokenAuth 클래스가 토큰 검증 콜백 기능을 제공함

1) app/api/auth.py

```python
token_auth = HTTPTokenAuth()

@token_auth.verify_token
def verify_token(token):
    ...

@token_auth.error_handler
def token_auth_error(status):
    ...
```

2) app/api/users.py : API 루트를 토큰으로 보호하기 위해 데코레이터 추가  
create_user 빼고 @token_auth.login_required 추가

```python
@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if token_auth.current_user().id != id:  # 다른 사람 정보 변경 시도 시
        abort(403)  # 403 Forbidden : 클라이언트가 서버에 도달할 수 있어도, 서버가 그 요청을 허용하지 않음=클라이언트가 권한이 없는 요청을 함
    ...
```

- 이제 전처럼 인증없이 api 요청을 보내면, 401 에러 코드 반환

```shell
> http GET http://localhost:5000/api/users/2

HTTP/1.0 401 UNAUTHORIZED
Content-Length: 25
Content-Type: application/json
Date: Fri, 17 Dec 2021 05:44:47 GMT
Server: Werkzeug/2.0.2 Python/3.8.6
WWW-Authenticate: Bearer realm="Authentication Required"

{
    "error": "Unauthorized"
}
```

- 아래와 같이 사용자 이름, 비밀번호로 토큰을 받고, 해당 토큰을 Authorization Bearer 에 넣어주어야 API에서 응답을 정상적으로 받을 수 있음

```shell
> http --auth <username>:<password> POST http://localhost:5000/api/tokens
HTTP/1.0 200 OK
Content-Length: 45
Content-Type: application/json
Date: Fri, 17 Dec 2021 05:46:38 GMT
Server: Werkzeug/2.0.2 Python/3.8.6

{
    "token": "<certain-token>"
}

> http GET http://localhost:5000/api/users/2 "Authorization:Bearer <certain-token>"

HTTP/1.0 200 OK
Content-Length: 362
Content-Type: application/json
Date: Fri, 17 Dec 2021 05:47:31 GMT
Server: Werkzeug/2.0.2 Python/3.8.6
```

### 4. 토큰 Revoke하기
- authorization 헤더로 들어온 그 토큰이 없어지게 됨

```python
@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204  # 204 No Content : 요청이 성공했으나 클라이언트가 현재 페이지에서 벗어나지 않아도 됨(response body 없음)
```

```shell
> http DELETE http://localhost:5000/api/tokens "Authorization:Bearer <certain-token>"

HTTP/1.0 204 NO CONTENT
Content-Type: text/html; charset=utf-8
Date: Fri, 17 Dec 2021 05:54:42 GMT
Server: Werkzeug/2.0.2 Python/3.8.6
```

## API 친화적인 에러 메시지
- 앞서서 브라우저에서 invalid user URL (http://localhost:5000/api/users/96546 )로 요청을 보내면 서버가 404 에러를 리턴하는데, 포맷이 404 HTML 에러 페이지임. 에러들은 API 블루프린트 안의 JSON 버전으로 바뀌어야하는데, Flask에 의해 다뤄지는 몇 에러들은 여전히 앱 전체에 등록되어있어서 HTML을 반환함(app/errors/handlers.py 의 @bp.app_errorhandler(404)같은 것)
- HTTP 프로토콜은 클라이언트와 서버가 **content negotiation** 으로 응답에 대한 최선의 포맷을 합의할 수 있음. 클라이언트는 요청에 **Accept header**로 선호하는 형식을 담아서 보내면, 서버는 그 리스트를 보고 서버가 지원하는 최선의 포맷을 이용해서 응답함
- app/errors/handlers.py : 클라이언트의 선호에 맞게 HTML 또는 JSON 으로 응답하는 content negotiation을 사용하도록 전역 앱 에러 핸들러를 수정함

```python
def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.html'), 404
```

- Before : request.accept_mimetypes를 사용하지 않았을 때 HTML이 반환됨

```shell
> http GET http://localhost:5000/api/users/456 "Authorization:Bearer <certain-token>"
HTTP/1.0 404 NOT FOUND
Content-Length: 5831
Content-Type: text/html; charset=utf-8
Date: Fri, 17 Dec 2021 06:09:54 GMT
Server: Werkzeug/2.0.2 Python/3.8.6

<!DOCTYPE html>
<html>
  <head>
    <title>
    Welcome to Microblog
</title>
```

- After : request.accept_mimetypes을 사용했을 때 JSON이 반환됨

```shell
> http GET http://localhost:5000/api/users/456 "Authorization:Bearer <certain-token>"
HTTP/1.0 404 NOT FOUND
Content-Length: 22
Content-Type: application/json
Date: Fri, 17 Dec 2021 06:08:24 GMT
Server: Werkzeug/2.0.2 Python/3.8.6

{
    "error": "Not Found"
}
```

## 이 챕터에서 새로 생성된 파일
- app/api/\_\_init\_\_.py
- app/api/users.py
- app/api/errors.py
- app/api/tokens.py
- app/api/auth.py
- migrations/versions "user tokens" 관련 파일

## 이 챕터에서 수정된 파일
- app/\_\_init\_\_.py
- app/models.py
- requirements.txt
- app/errors/handlers.py

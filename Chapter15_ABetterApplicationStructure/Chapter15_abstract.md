# 15장 : A Better Application Structure

- 큰 앱에 적용할 수 있는 Pattern들
- 3개 서브시스템에 blueprint를 도입하고, 앱 factory 함수를 만들어서 앱 리팩토링

## 현재의 한계
1. 서브시스템의 코드들이 섞여있음  

- 사용자 인증 서브시스템 : view function은 app/routes.py, form은 app/forms.py, 템플릿은 app/templates, 이메일은 app/email.py  
- 에러 서브시스템 : 에러 핸들러는 app/errors.py 에 정의, 템플릿은 app/templates
- 앱의 핵심 기능인 블로그 포스트 쓰고 읽기, 유저 프로필, 팔로잉, 포스트에 대한 실시간 번역도 다양한 모듈과 템플릿에 흩어져있음.  
앱이 커지면 app/routes.py, forms.py 이런 모듈들은 엄청나게 크고 지저분해짐

- 다음 프로젝트에서 이 앱의 사용자 인증 부분을 재사용하고 싶어졌을 때, 여러 모듈에 들어가서 적절한 부분만 copy/paste해서 새 프로젝트에 이식해야 함 > 그러므로 사용자 인증 관련 파일을 별도로 분리해놓고 싶음

2. Flask 앱 인스턴스가 전역 변수로 1개 생성됨
- Flask 앱 인스턴스가 app/\_\_init\_\_.py 에서 전역 변수로 만들어지고, 많은 모듈들에게 import됨. 이것 자체로는 문제가 아닌데, 앱을 전역변수로 가지는 것은 특히 테스트할 때 복잡해짐. 
    1) 다른 configuration에서 이 앱을 테스트하고 싶다면, 앱이 전역으로 되어있기 때문에, 다른 configuration을 가지는 2개의 앱을 객체화하는 것 밖에 방법이 없음.
    2) 모든 테스트가 같은 앱을 사용하기 때문에, 한 테스트가 앱에 변화를 줄 수 있고, 나중에 수행되는 다른 테스트에도 영향을 줄 수 있음. 
- tests.py 모듈 : 디스크 기반의 디폴트 SQLite db 대신에 인메모리 db를 사용하도록 config를 변경함. 앱에 config가 이미 적용된 후에, config를 수정하는 게 이번 경우에는 잘 동작하는 것처럼 보이지만, 다른 경우에는 찾기 어려운 버그를 만들어낼 수도 있음

- 그러므로 **application factory** 함수 사용 : config object를 argument로 받으면, 해당 config가 적용된 Flask 앱 인스턴스를 반환하는 함수.  (이 프로젝트에서는 app/\_\_init\_\_.py 의 create_app 함수)
그러면 각 테스트가 own 앱을 생성할 수 있기 때문에, 특별한 config를 요구하는 테스트를 작성하기 편해짐.

## Blueprints
- **blueprint** = 앱의 서브셋을 나타내는 논리적인 구조. routes, view function, forms, templates, static files를 포함하고 있음. 분리된 파이썬 패키지에 씀
- 블루프린트가 앱에 등록되어야 함. 등록되는 동안 블루프린트에 추가된 모든 요소는 앱에 전달됨. 그러므로 블루프린트는 코드 조직화를 돕는, 앱 기능의 임시 저장소로 생각하면 됨.

### Error Handling Blueprint
```
app/
    errors/               <-- blueprint package
        __init__.py       <-- blueprint creation
        handlers.py       <-- error handlers
    templates/
        errors/           <-- error templates
            404.html
            500.html
    __init__.py           <-- blueprint registration
```

1) app/errors/\_\_init\_\_.py 에서 블루프린트 생성 후, 핸들러들을 등록함.

```python
from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.errors import handlers
```

2) app/\_\_init\_\_.py 에서 앱 인스턴스 생성 후 블루프린트 등록. 등록되고 나면, 그 안의 모든 view function, templete, static file, error 핸들러 등을 앱에 다 연결됨. 

```python
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)
```

3) app/errors.py >> app/errors/handlers.py  
@app.errorhandler(404)를 **@bp.app_errorhandler(404)** 로 변경 : 결과는 같으나, 블루프린트를 앱에 독립적으로 만들어서 더 portable 하게 만듦. 그리고 error 템플릿 반환 경로도 errors/ 붙임

4) app/templates/errors 로 404.html, 500.html 이동

- Flask blueprint 에서 templates 나 static 디렉토리 구성방식 2가지
1) 'templates' 안을 블루프린트 별로 서브 디렉토리로 나눔. 그래서 모든 템플릿이 'templates'라는 하나의 위계 안에 있게 할 수 있음. 여기서는 첫번째 방식을 택함
2) 블루프린트 패키지 안에 템플릿을 각각 둠(app/errors/templates). 이 경우에는 Blueprint() 생성자에 template_folder='templates' 라는 인자를 추가하면 됨

### Authentication Blueprint
```
app/
    auth/                       <-- blueprint package
        __init__.py             <-- blueprint creation
        email.py                <-- authentication emails
        forms.py                <-- authentication forms
        routes.py               <-- authentication routes
    templates/
        auth/                   <-- blueprint templates
            login.html
            register.html
            reset_password_request.html
            reset_password.html
    __init__.py                 <-- blueprint registration
```

1) app/auth/\_\_init\_\_.py : 블루프린트 생성 후 routes 등록

2) app/auth/email.py 에 send_password_reset_email()을 옮기고 current_app 사용  
프로젝트 루트의 email.py는 app이 아닌 current_app._get_current_object()을 사용하도록 변경(이유는 아래 Application Factory Pattern 부분에 기술함)

3) app/auth/forms.py 에 LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm 4개 옮김. 

4) app/auth/routes.py 에 login, logout, register, reset_password_request, reset_password 옮김  
@app.route() >> **@bp.route()** 로 변경.  
url_for('login') >> url_for('auth.login') 으로 변경. **url_for('블루프린트 이름.viewfunction이름')**  

5) app/\_\_init\_\_.py : 블루프린트 등록. 그리고 login.login_view = 'auth.login' 이렇게 auth.login으로 변경해야 함

```python
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
```

**url_prefix** : auth_bp 하에 있는 모든 routes에 /auth 를 붙여줌. 그래서 app/auth/routes.py 에는 @bp.route('/login', methods=['GET', 'POST']) 이렇게 /login 으로만 되어있지만, 실제로 url_for 로 불러줄 때는 url_for('auth.login') 로 함.

## Main Application Blueprint
- main 폴더에 옮김
- 모든 html 에서 url_for 수정

## Application Factory Pattern
- 이전에는 모든 view function과 에러 핸들러가 app에서 온 데코레이터였지만, 지금은 모두 블루프린트 데코레이터로 변경됨. 그래서 앱을 전역으로 가지고 있을 이유가 더 적어짐
- app/\_\_init\_\_.py 에 Flask 앱 인스턴스를 만드는 create_app 함수를 추가하고, 전역 변수를 지움

1) 전에는 Flask extension이 앱을 argument로 받아서 인스턴스를 만들었음. (moment = Moment(app)) 그런데 전역 앱이 없으므로 다른 방식으로 초기화됨. 전역 범위로 앱에 붙지 않은 채 extension 인스턴스가 만들어지고(moment = Moment()), 앱이 factory 함수에서 만들어질 때, init_app() 함수로 지금 알게 된 앱 인스턴스와 바인드 되어야 함

```python
from config import Config
from flask_moment import Moment
moment = Moment()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    moment.init_app(app)
```

2) test할 때는 로깅하지 않도록 함(not app.testing)

- 누가 이 앱 factory 함수를 부르는가?  
    1. 평소에는 microblog.py 에서 app = create_app(). 특별히 config 인자를 주지 않으면, 디폴트로 config.py의 Config 클래스가 들어감.
    2. test할 때는 tests.py 에서 self.app = create_app(TestConfig) 으로 부름.

- app 을 직접적으로 참조하는 부분이 블루포인트 도입으로 많이 없어지기는 했지만, 여전히 남아있음. app/models.py, app/translate.py, and app/main/routes.py 등에서 app.config를 참조함  
**current_app** 변수 : Flask가 요청을 dispatch하기 전에 앱으로 초기화해주는 변수  
※ "magical" 변수 : Flask 의 g, current_app, Flask-Login 의 current_user처럼 전역 변수처럼 쓰이는 변수들. 그러나 리퀘스트를 핸들링하는 동안 또는 리퀘스트 핸들링하는 쓰레드 안에서만 접근가능함. 

1) app/email.py : 왜 쓰레드에서 실행하는 send_async_email()에서 직접 current_app을 사용하지 않고, send_email()에서 current_app 오브젝트를 쓰레드에 넘겨주는가?  
current_app 변수는 클라이언트 요청을 핸들링하는 쓰레드에 묶여있는 context-aware 변수임. 다른 쓰레드에서는 current_app 이 할당된 값이 없음. 
그리고 current_app은 앱 인스턴스와 매핑된 proxy 오브젝트이기 때문에, 쓰레드 오브젝트에 직접 넘겨주는 것도 동작하지 않음. 그냥 current_app 만 넘겨주는 건, 쓰레드 안에서 current_app 을 직접 쓰는 것이랑 같음. 원하는 건 메일보내는 쓰레드가 currrent_app 이라는 프록시 오브젝트안에 저장된 실제 앱에 접근하는 것임. 그래서 프록시 오브젝트 안에 있는 실제 앱을 꺼내려고 **current_app._get_current_object()** 표현을 써서, 인자로 전달해주는 것임.  
※ 실제 앱 인스턴스를 감싸고 있는 current_app 프록시 변수

2) app/cli.py : 이 명령들은 리퀘스트를 핸들링할 때가 아니라, 앱이 시작할 때 등록되기 때문에, current_app 변수를 못 씀. 이 모듈에서 app 에 대한 참조를 없애기 위해서, def register(app) 이라는 함수로 감쌈

3) microblog.py
```python
app = create_app()
cli.register(app)
```

## 단위 테스트 개선사항
- 앱이 생기기 전에 내 test 설정을 지정하고 싶음
- tests.py  
1) Config를 상속하는 TestConfig 클래스 생성. 나중에 앱 생성 시에 이 TestConfig 객체를 create_app의 인자로 넘길 것임
2) UserModelCase 클래스 안의 setUp과 tearDown 메소드를 앱 인스턴스를 생성하고 제거하는 데 사용

```python
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
```
- self.app()에 새 앱이 저장되어있음. db 인스턴스는 app.config로부터 db URI를 얻어야 해서 앱 인스턴스를 알아야 함. 그런데 앱 인스턴스가 여러 개 있는 것 중에, db 한테 내가 방금 만든 앱 인스턴스를 어떻게 인식시키는가?  
- 정답은 앱 context임. current_app 변수는 현재 쓰레드 안에서 active 앱 context를 먼저 찾고, 찾으면 거기서 앱을 얻음. 만약 context가 없으면 어떤 앱이 active인지 알 수 없어서 exception을 발생시킴. 그래서 create_app()만 해서는 앱 인스턴스만 하나 더 느니까, 이 앱을 app_context에 푸시해주어야 함.  
- 지금까지 view function을 invoke하기 전에, Flask가 앱 context를 푸시하고 있었고, 그래서 current_app 과 g를 쓸 수 있었던 것임. 요청이 완료되면 다시 context는 current_app, g와 함께 사라짐. 

- Flask가 사용하는 context 2가지
1) application context
2) request context : 요청이 다뤄지기 바로 전에 request context가 활성화되면, Flask-Login의 current_user, Flask 의 request, session 변수를 사용할 수 있음

## 환경 변수
- 서버 시작 전에 환경에 변수들을 가지고 있어야 하는 몇 개 설정 옵션이 있음  
ex) SECRET_KEY, 이메일 서버, DB url, MS Translator API 키
- 이 환경변수들을 앱 루트 디렉토리에 **.env** 파일로 저장
- python-dotenv 패키지가 .env 파일을 지원함. 
1) .env : 앱 설정 변수. secret을 보호하기 위해서 소스제어에 추가되는 걸 지원하지 않음. 앱 인스턴스와 설정 오브젝트가 존재하기 전에, 앱 bootstrap 과정에서 매우 일찍 필요한 Flask 의 FLASK_APP, FLASK_DEBUG 환경 변수는 .env에 선언하면 안 됨.
2) .flaskenv : Flask 만의 설정변수, secrets나 비밀번호가 없기 때문에 소스 제어에 추가될 수도 있음

- flask 명령어는 .flaskenv 와 .env 파일에 정의된 모든 변수들을 자동으로 import함. 평소에 flask run 할 때는 상관이 없지만, 이 앱을 운영에 디플로이할 때는 flask 명령어를 안 써서 .env 파일은 읽히지 않음
- 그래서 config.py 에서 Config 클래스가 만들어지기 전에 .env 파일을 명시적으로 import 해서, 이 Config 클래스가 만들어질 때 이 변수들이 이미 세팅되어있도록 함

```
SECRET_KEY=<your-secret-key>
MAIL_SERVER=localhost
MAIL_PORT=8025
EMAIL=<email1@example.com,email2@example.com>
MS_TRANSLATOR_KEY=<your-ms-translator-key>
```

## Requirements File
- requirements.txt 파일 만들기 : 다른 머신에서 환경을 재생성할 때, 내가 어떤 패키지를 설치해야하는지 기억하기 어려움. 그래서 모든 dependencies를 나열한 requiremets.txt 파일을 프로젝트 루트 폴더에 만듦. 'pip freeze' 명령어로 내 가상환경에 설치된 모든 패키지를 덤프 뜸.

```shell
pip freeze > requirements.txt
```

- requirements.txt 파일 이용하여 패키지 설치하기
```shell
pip install -r requirements.txt
```

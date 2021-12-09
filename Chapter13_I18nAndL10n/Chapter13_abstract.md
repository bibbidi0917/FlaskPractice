# 13장 : I18n and L10n
- 다양한 언어 지원
- flask 명령에서 나만의 CLI extension을 만드는 방법
- I18n(국제화), L10n(지역화)

## Flask-Babel
- 번역을 지원하는 Flask extension

```shell
pip install flask-babel
```

- app/\_\_init\_\_.py 에 initialize하고,@babel.localeselector 등록  

```python
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
```
HTTP request header를 보면, Accept-Language가 아래와 같이 나옴.  
Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7  
클라이언트 언어와 위치가 weighted list로 나옴. OS의 언어 세팅을 디폴트로 가져와서 브라우저가 기억하고 있음. 'ko-KR'이 디폴트 weight인 1이고, 'ko'는 0.9 이런 식임.  

best 언어를 선택하기 위해서 클라이언트로부터 받은 accept-language 리스트와 앱이 지원하는 언어를 비교하고, 클라이언트가 준 weight를 이용해서 best를 찾음. 

- config.py 에 LANGUAGES 변수 추가

## Python 소스 코드에서 번역할 text 표시하기
- 소스코드에 번역한 모든 텍스트를 넣고 > Flask-Babel이 gettext tool을 이용해서 모든 파일을 스캔하고 별도의 번역파일로 텍스트를 추출함
1) 
```python
from flask_babel import _
_('Hello!')
```

기본 언어로된 text를 _() 함수로 감쌈. 이 함수는 app/\_\_init\_\_.py 에 @babel.localeselector 로 등록한 get_locale()이 선택해준 언어를 이용하여, 번역된 텍스트를 리턴해줌

2) 
```python
from flask_babel import _
_('User %(username)s not found.', username=username)
```

dynamic 요소가 들어가는 경우에는, .format을 못 쓰고, %()를 써주어야 함. 

3) 
```python
from flask_babel import lazy_gettext as _l 
_l('Username')
```
리퀘스트 밖에서 텍스트가 번역되어쓰여야 하는 경우. 예를 들어 app/forms.py 에 LoginForm 의 label 같은 것은, 어떤 언어를 사용해야할 지 아직 모름. 따라서 실제 리퀘스트 하에서 이 String이 사용되기 전까지 evaluation을 지연시켜야 함. _()의  lazy evaluation 버전이 lazy_gettext().

- Flask-Login extension은 사용자의 login 페이지로 리다이렉트할 때마다 메시지를 flash함. 이 메시지는 영어이고, extension이 자체로 가지고 있는 것임. 따라서 이 메시지가 번역되게 하려면, app/\_\_init\_\_.py 에서 lazy_gettext를 사용하여 메시지를 감싸주고, 이 메시지에 대한 번역도 제공해줘야 함.

- app/\_\_init\_\_.py 에서 로그인 메시지, email.py에서 메일 제목, forms.py 전체, routes.py title 부분.

## 템플릿에서 번역할 text 표시하기
1) 
```html
<h1>{{ _('File Not Found') }}</h1>
```

2) 
```html
<h1>{{ _('Hi, %(username)s!', username=current_user.username) }}</h1>
```

3) 
```html
        {% set user_link %}
            <a href="{{ url_for('user', username=post.author.username) }}">
                {{ post.author.username }}
            </a>
        {% endset %}
        {{ _('%(username)s said %(when)s',
            username=user_link, when=moment(post.timestamp).fromNow()) }}
```

**{% set user_link %}, {% endset %}** : user_link라는 중간 변수를 만듦. set 부분은 화면에 안 나옴

- app/templates 이하 모든 html 수정

## 번역할 text 추출하기
- _(), _l()로 쓴 것들을 .pot 파일(portable object template)로 추출하기 위해서  PyBabel 명령을 사용할 수 있음. 번역이 필요한 모든 텍스트들을 담은 파일임. 
- 1) babel.cfg 파일 생성 : 추출을 위해서 pybabel에 어떤 파일이 번역을 위해 스캔되어야하는지 설정해주어야 함. 

```cfg
[python: app/**.py]
[jinja2: app/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```
extensions : Flask-Babel이 템플릿 파일들을 적절히 파싱할 수 있도록 extension을 표기해줌.

- 2) 아래 명령어를 (venv)에서 입력

```shell
> pybabel extract -F babel.cfg -k _l -o messages.pot .
```
\-F babel.cfg(babel.cfg configuration 파일 읽어라), -k _l(lazy version도 같이 찾아달라), -o messages.pot(결과파일 이름은 messages.pot으로 해달라)

- 이 messages.pot 파일은 빈번하게 재생성되기 때문에 소스제어할 필요가 없어서 커밋하지 않음

## Language Catalog 생성하기
- 
```shell
> pybabel init -i messages.pot -d app/translations -l es
creating catalog app/translations\es\LC_MESSAGES\messages.po based on messages.pot
```

messages.pot 파일을 인풋으로 사용하고, 새로운 언어 카탈로그는 app/translations 의 디렉토리에 쓰고, es 스페인 언어임.
- 이렇게 생성된 messages.po 파일은 gettext 유틸리티에서 사용되는 포맷임.

```po
#: app/email.py:21
msgid "[Microblog] Reset Your Password"  # base 언어로된 text
msgstr ""
```

- 이 po 파일에서 msgstr 부분을 채워주는 전문적인 에디터들이 있고, poedit이 가장 유명함. 

- .po 파일에 번역이 다 되고 나면, 이 번역된 text들이 런타임에 앱에서 효율적으로 사용될 수 있도록 compile되어야 함.

 ```shell
> pybabel compile -d app/translations
 ```
 컴파일하고나면 .mo(컴파일된 번역) 파일이 생성됨. Flask-Babel은 이 .mo 파일을 앱에서 번역 load할 때 사용함.
 
- 스페인어로 설정된 것을 보고 싶다면, 잠시 app/\_\_init\_\_.py의 get_locale함수에서 'es'가 리턴되도록 바꿈.

## 번역 업데이트하기
```shell
> pybabel extract -F babel.cfg -k _l -o messages.pot .
> pybabel update -i messages.pot -d app/translations
> pybabel compile -d app/translations
```

## 날짜와 시간 번역하기
- Flask-Moment와 moment.js 에서 만들어진 타임스탬프들은 앞선 방식으로는 번역이 되지 않았음.
- moment.js 라이브러리는 지역화와 국제화를 지원함. Flask-Babel은 get_locale() 함수를 통해서 언어와 위치를 반환하고, 이걸 'g' object의 locale에 넣어줌. 
- app/routes.py 의 @app.before_request 에서 flask.g.locale 에 선택된 언어를 저장함.
- app/templates/base.html 에서 g.locale을 접근할 수 있으므로, moment.lang에 g.locale을 넣어줌


## Command-Line 개선사항
- 'flask' 명령어에 통합될 수 있는 커스텀 명령어들을 만드는 방법  
ex) flask run, flask shell, flask db 처럼 flask와 같이 쓸 수 있는 명령어
- 이 앱에 특화된 argument들을 가지고 pybabel 명령어를 트리거할 수 있는 간단한 명령어를 만들고 싶음  
1) flask translate init LANG : 새 언어 추가
2) flask translate update : 모든 언어 repository들을 업데이트
3) flask translate compile : 모든 언어 repository 컴파일  

pybabel init 이나 pybabel update를 수행하기 전에 항상 pybabel extract 로 만들어진 messages.pot 파일이 필요하므로, 별도의 명령어로 분리하지 않고 translate init, translate update 안에 각각 pybabel extract를 넣음

- Flask는 Click 패키지를 신뢰함.(Command Line Interface Creation Kit)  
Click은 명령어에 대한 임의 nesting이 가능하고, 자동으로 헬프 페이지를 만들며, 런타임에 sub명령어에 대한 lazy loading을 지원함
- app/cli.py 파일에  
1) @app.cli.group()으로 translate() 등록.  

```python
@app.cli.group()
def translate():
```
'translate'는 여러 sub 명령어를 가진 루트이며, @app.cli.group() 을 통해 만들어짐. translate 자체는 sub명령어들의 base만 제공할 뿐 이 함수 자체로는 아무것도 할 수 없음

2) @translate.command() 로 sub 명령어 등록

```python
@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    # 에러 안 나면 0
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    os.remove('messages.pot')  # 필요할 때 쉽게 재생성 가능해서, 지워버림
```
함수명이 데코레이터의 일부로 쓰이는 것이, Click이 명령어 그룹을 만드는 방식임.  
※ --help 결과로 docstring 들이 나옴

- microblog.py 에 cli 모듈 import : import만 하면 명령어 데코레이터들이 돌아가고, 명령어를 등록함
- 이 상태에서 flask --help 치면 Commands에 translate 보이고, flask translate --help 하면 sub 명령어들의 docstring이 보임

## 이 챕터에서 추가된 파일
- babel.cfg
- app/translations/es/LC_MESSAGES/messages.po
- app/cli.py

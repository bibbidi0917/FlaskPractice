# 14장 : Ajax

- Microsoft 번역 서비스와 약간의 JavaScript를 이용한, 실시간 언어 번역 기능

## Server-side vs. Client-side
- 전통적인 Server-side 모델에서는 클라이언트가 앱 서버에 HTTP 리퀘스트를 보냄 > 서버는 바로든 리다이렉트를 하든 새로운 웹 페이지를 클라이언트에 보내면서 요청을 완료함 > 클라이언트는 현재 페이지를 새로운 것으로 바꿈  
이 모델에서는 서버가 모든 일을 하고, 클라이언트는 웹 페이지를 보여주고 사용자 입력을 받는 것만 함. 
- Client-side 모델에서는 클라이언트가 서버로 요청보내고 서버가 웹 페이지로 응답을 하는 것은 맞지만, 페이지 데이터가 자바스크립트 코드가 포함된 html일 수 있음. 클라이언트가 페이지를 받으면 HTML 부분을 보여주고 코드를 실행시킴 > active client가 되어서 서버와의 연결없이 스스로 동작할 수 있음. 엄격한 client-side 앱에서는 전체 앱이 첫 페이지 요청에 클라이언트에게 다운로드되고, 앱 전체가 클라이언트에서 돌아감. 데이터 저장하거나 appearance에 큰 변화가 있을 때만 서버와 연결함. 이런 형태의 앱을 'Single Page Applications'(SPA)라고 부름
- 대부분의 앱은 두 모델을 섞은 것임. microblog는 사용자 post의 실시간 번역을 하기 위해서 클라이언트 브라우저에서 비동기 요청을 서버에 보내고 > 서버는 페이지 리프레쉬없이 응답 > 클라이언트는 현재 페이지에 동적으로 번역을 삽입. 이것이 **Ajax**= Asynchronous JavaScript and Xml.(요즘에는 xml 대신 json을 씀)

## 실시간 번역 Workflow
- 지금도 Flask-Babel 덕에 다국어 지원을 하지만, 사용자들이 올린 post는 미리 번역해둘 수 없어서 다국어 지원이 안 되는 상황
- 각 포스트에 대한 번역이라는 행위가 페이지 전체의 리프레쉬까지는 필요없고, 동적으로 원래 언어 텍스트 밑에 삽입되면 됨  
1. 번역할 텍스트 식별
2. 각 유저에 대한 선호 언어를 앎.(다른 언어로 쓰여진 post에만 'translate' 링크를 보여주려고 함)
3. Ajax 요청을 서버에 보냄
4. 서버는 제 3자 번역 API에 연결
5. 서버가 번역된 텍스트를 클라이언트에 보냄
6. 클라이언트의 JavaScript 코드가 번역된 텍스트를 페이지 안에 동적으로 삽입

## 1. 언어 식별
- 각 post가 어떤 언어로 쓰여졌는지 식별
- langdetect 언어 탐지 라이브러리

```shell
pip install langdetect
```
- 포스트가 렌더링될 때마다 이 라이브러리를 통해서 언어를 탐지하는 게 시간낭비이기 때문에, 포스트가 등록되었을 때 언어를 Post 테이블에 저장해놓고자 함
- app/models.py Post 클래스에 language 컬럼 추가
- db 마이그레이션 ( flask db migrate, upgrade)
- app/routes.py index()에서 language 식별해서 저장. 식별할 수 없는 언어로 쓰여진 것은 '' 빈 String으로 둠

## 2. "Translate" 링크 보여주기
- app/templates/_post.html 에 translate 버튼 부분 추가  
※ app/routes.py 의 @app.before_request 에서 g.locale에 사용자 선호 언어 넣어줌

## 3. 제 3자 번역 서비스 사용하기
- Google Cloud 번역 API, Microsoft Translator Text API. 마이크로소프트만 낮은 단계 서비스로 공짜 번역이 있음. 그래서 MS 것을 사용. 
1) Azure 계정에서 free tier로 등록하고, translator 리소스 만들어서 배포. 키 값 2개 중에 아무거나 1개 복사해서 아래 코드를 (venv)에 입력

```shell
set MS_TRANSLATOR_KEY=<paste-key>
```
2) config.py 에 MS_TRANSLATOR_KEY 추가

3) Microsoft Translator API 는 HTTP 리퀘스트를 받아들이기 때문에, Python 안에 HTTP 클라이언트가 필요함. 그래서 requests 패키지를 install 함

```shell
pip install requests
```

4) app/translate.py 파일을 만들어서, API 호출하여 번역된 텍스트 받아오는 translate() 구현  
(여기서 requests.post() 안에 verify=False 옵션 넣어서, SSL Error 해결함)

## 4. 서버 측의 Ajax
- 클라이언트에서 비동기 요청이 왔을 때, 서버에서 처리하는 로직
- app/routes.py 에 '/translate' url 매핑함 : 데이터만을 리턴함. 

```python
@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],  # jsonify : 딕셔너리를 JSON으로 변경
                                      ...
```
- request.form : form 데이터를 딕셔너리로 만듦. web form이 없기 때문에, request의 데이터를 직접 접근하였음  
※ 지금까지 이렇게 쓰지 않았던 이유는, form = ResetPasswordRequestForm() 이런 web form이 있어서, Flask-WTF 에 의해 form.email.data 이런 식으로 데이터를 꺼낼 수 있었기 때문임.

## 5. 클라이언트 측의 Ajax
- 사용자가 'translate' 링크를 클릭하면, text, source language, dest language 데이터를 가지고 서버로 /translate 요청 보냄
- 브라우저에서 JavaScript가 동작할 때, 페이지는 Document Obejct Model(DOM) 으로 표현됨. DOM은 페이지 안의 모든 요소들을 위계적 구조로 가진 것. JavaScript는 이 페이지에서 DOM을 변경하는 데에 사용함

1) DOM 노드를 구별하기 위해서, app/templates/_post.html 에서 post.body를 span으로 감싸서 post id로 unique한 span id를 부여함(span을 사용해서 보여지는 것의 변화는 없지만, id를 삽입하는 용도로 씀)  
※ $ : Flask-Bootstrap 안에 있는 jQuery 라이브러리에서 제공하는 함수의 이름.  
그리고 번역된 텍스트가 오면 Translate 링크를 번역된 텍스트로 변경할 것임. 이 때도 수많은 post들 중에 해당 post를 찾아야 하기 때문에 span id 부여.

2) app/templates/base.html 에서 서버로 post 요청(**$.post(url, {dictionary})**)보내고, 응답 받아서 표시하는 translate() 함수 추가

```javascript
function translate(sourceElem, destElem, sourceLang, destLang){
            $(destElem).html('<img src="{{ url_for('static', filename='loading.gif') }}">');
            ...
```

3) app/static/loading.gif 파일 추가 : base.html의 translate 함수 안에서, post 요청 보내고 응답받기 전까지 띄우는 임시 이미지(spinner)

4) app/templates/_post.html 에서 translate의 href로 base.html의 translate()함수 호출

※ config.py에 언어를 'en', 'es'로 정의했기 때문에, 요청 헤더의 'Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7' 를 참고해서 베스트 언어는 en으로 결정됨. 그래서 한국어로 포스트를 남기면, translate 버튼을 눌러서 영어 번역을 볼 수 있음

- 새롭게 사용된 단어들이 있기 때문에, https://github.com/miguelgrinberg/microblog/blob/v0.14/app/translations/es/LC_MESSAGES/messages.po 에서 messages.po 파일을 받아서 업데이트하고, flask translate update, flask translate compile을 수행하여 새로운 번역을 publish함.

# 이 챕터에서 추가된 파일
- migrations/versions/037a69b9d1e5_add_language_to_posts.py
- app/translate.py
- app/static/loading.gif

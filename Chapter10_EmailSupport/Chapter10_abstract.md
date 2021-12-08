# 10장 : Email Support
- 인증 관련 문제를 해결하기 위해서 이메일 기능이 필요함
- 비밀번호 리셋 기능 추가 = 비밀번호 리셋을 사용자가 요청했을 때, 앱이 특정 링크를 포함한 이메일을 보냄. 사용자는 그 링크를 클릭해서 새 비밀번호를 세팅하는 양식에 들어가게 됨

## Flask-Mail
```bash
pip install flask-mail
```
- 비밀번호 리셋 링크는 보안토큰을 가지고 있는데, 이 토큰을 생성하기 위해서 JSON Web Token을 사용함. 아래 pyjwt 설치
```bash
pip install pyjwt
```
- Flask-Mail extension에 대한 설정값은 config.py에 이미 있음.(7장에서 추가) 이 extension 역시 \_\_init\_\_.py 에서 Mail인스턴스를 만들어줌.  
※ 7장 Email로 Error 보내기 부분 참고

## 간단한 Email Framework
- app/email.py 파일 생성

## 비밀번호 리셋 요청하기
- app/templates/login.html 에 리셋링크 추가
- app/forms.py 에 ResetPasswordRequestForm 클래스 추가
- app/templates/reset_password_request.html 파일 추가
- app/routes.py 에 reset_password_request() 추가  
로그인 안 된 사람만 이 기능을 사용할 수 있게 함. 그래서 @login_required 를 떼고, if current_user.is_authenticated: 이렇게 로그인된 사용자인지 확인하여 홈화면으로 보냄.  
사용자가 입력한 이메일이 실제 db에 있는 유저의 이메일이든 아니든, 동일하게 이메일을 확인하라는 메시지를 띄워줌. 그래서 사용자들이 특정 이메일을 가진 사람이 멤버인지 아닌지 확인하는 데 이 양식을 이용하지 못하도록 함.

## 비밀번호 리셋 토큰(JWT)
- 토큰은 비밀번호 변경 전에, 사용자가 해당 이메일 주소 계정에 접근했음을 보장하는 증거임. 굉장히 유명한 토큰이 JSON Web Token(JWT)이고, 이 자체로 검증이 가능함. 이메일에 토큰을 넣어서 사용자에게 보내고, 사용자가 링크를 클릭하면 그 토큰이 어플리케이션으로 들어오고, 그 토큰으로 검증이 가능함.

```shell
token = jwt.encode({'a': 'b'}, 'my-secret', algorithm='HS256')
jwt.decode(token, 'my-secret', algorithms=['HS256'])
```

토큰을 안전하게 만들기 위해서 여기서는 'my-secret'이라는 걸 썼지만, 앱에서는 SECRET_KEY 를 이용함.  
- 토큰 자체는 JWT 사이트에 가서 누구나 쉽게 decoding할 수 있음. 이 토큰을 안전하게 만드는 것은 '서명'임. 누가 토큰 안의 payload 위조를 시도할 때 서명이 invalid하면, 새 서명을 만들기 위해서 secret key가 필요함. 토큰이 검증되어야, payload 내용이 decode됨. 즉 토큰의 서명이 검증되어야, payload를 믿을 수 있음.
- app/models.py 의 User 클래스에 get_reset_password_token(), verify_reset_password_token() 추가. 토큰은 사용자와 밀접한 관련이 있으므로 user 클래스에 추가함  
verify_reset_password_token() : 사용자가 이메일의 링크를 클릭하는 순간, 토큰이 URL의 일부로 앱에 들어와서, 이 토큰을 검증할 때 사용하는 함수. 서명이 맞으면 id로 사용자 객체를 불러옴. 이 함수에서 사용자 객체가 잘 리턴되면, 앱은 새로운 패스워드를 묻고, 해당 사용자의 계정에 새로운 패스워드를 세팅할 것임.
```python
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return  # exception 발생 시 None을 리턴함.
        return User.query.get(id)
```
- **@staticmethod** : 인스턴스가 아닌, 클래스에서 바로 호출 가능. self를 첫번째 argument로 안 받는 게 특징임.   
ex) User.verify_reset_password_token(token)

## 비밀번호 리셋 메일 보내기
- app/email.py 에 send_password_reset_email() 추가
```python
text_body=render_template('email/reset_password.txt', user=user, token=token)
```
render_template을 이용해서 이메일의 body를 만듦.
- app/templates/email/reset_password.txt, reset_password.html 파일 추가
```python
url_for('reset_password', token=token, _external=True)
```
_external=True : 절대경로로 만들어줌. url_for는 디폴트가 상대경로이고, 웹 페이지 안에서 만들어질 때는 상대경로만 있어도 웹 브라우저가 url을 완성시켜줌. 그런데 이메일은 context가 없기 때문에 절대경로를 주어야 웹브라우저가 이동할 수 있음.

## 사용자 비밀번호 리셋하기
- 사용자가 이메일의 링크를 클릭하면, 비밀번호 입력 창이 뜨고, 제출하면 비밀번호 리셋
- app/routes.py 에 '/reset_password/<token\>' 매핑 추가
- app/forms.py 에 ResetPasswordForm 클래스 추가
- app/templates/reset_password.html 파일 추가

## 비동기로 메일 보내기
- 이메일을 보내는 것이 앱을 느리게 만듦. 그래서 app/email.py의 send_email() 을 쓰레드를 이용하여 비동기로 만들고 싶음.  

```python
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    ...
    Thread(target=send_async_email, args=(app, msg)).start()
```

- Thread를 시작할 때 app 인스턴스를 같이 넘겨주는 이유 : 
2개 타입의 application context / request context가 있음. Flask는 context를 사용해서, 앱 인스턴스를 함수 간 인자로 넘겨주지 않아도 됨. 이 두 context는 프레임워크에 의해 자동으로 관리되지만, 앱이 custom 쓰레드를 시작할 때는 이 쓰레드들을 위한 context를 수동으로 만들어줘야함.
- 많은 extension들이 동작하기 위해서 앱 context를 필요로 함. 왜냐하면 Flask 앱 인스턴스를 인자로 전달받지 않아도 인스턴스를 찾을 수 있기 때문임. 
- 그럼 extension 입장에서 앱 인스턴스는 왜 필요한가? 모든 config가 app.config 오브젝트(\_\_init\_\_.py에서 app.config 오브젝트를 config.py의 Config 클래스로부터 만듦)에 있기 때문임.  
ex) Flask-Mail extension에서 메일을 보내려면 메일 서버에 대한 정보가 필요한데, 이건 app 을 알아야지만 해결됨. 'with app.app_context()'로 앱 context를 만들면, Flask의 current_app 변수를 통해 extension이 앱 인스턴스에 접근할 수 있음
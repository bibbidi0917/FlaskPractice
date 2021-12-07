# 7장 : Error Handling

## Debug Mode
- 운영 시에는 사용자가 모호한 에러페이지만 보고, 에러에 대한 중요 정보들은 서버 output이나 로그파일에 남기면 됨.
- 개발 시에는 아래와 같이 환경변수를 설정하면 debug mode가 됨. 
```bash
set FLASK_ENV=development
```
1) Error에 대한 stack trace들을 바로 볼 수 있음
2) 서버에 원격으로 코드를 실행시킬 수 있음
3) reloader : 소스파일이 변경되어 저장되면 자동으로 어플리케이션을 재시작함

## Custom Error Pages
- app/errors.py 파일을 추가하여 **@errorhandler(404)** 데코레이터 : custom error handler를 등록함  
```python
return render_template('404.html'), 404
```
두번째 리턴값은 응답코드임. 지금까지의 view function들은 디폴트로 200이었기 때문에 써주지 않았음.
- app/templates/404.html 500.html 파일을 추가함
- app/\_\_init\_\_.py 에 errors 모듈도 import

## Email로 Error 보내기
- 운영 서버의 output을 계속 보고 있지는 않기 때문에, 운영 서버 에러났을 때 바로 이메일을 보냄.
- config.py 에 메일 관련 config 추가
- email.json 파일만들어서 이메일 json 추가
- app/\_\_init\_\_.py 에 운영서버인 경우 app.logger(Flask logger object)에 SMTPHandler 인스턴스를 추가하여 로그 전송하는 부분 추가
- 테스트 방법 2가지  
1) Python의 SMTP debugging 서버 사용 : fake 이메일 서버이고, 이메일을 보내는 대신 콘솔에 프린트함.
    1. 두번째 터미널 세션을 열어서 아래 코드를 돌림
```bash
python -m smtpd -n -c DebuggingServer localhost:8025
```
    2. 첫번째 터미널에서 아래 환경변수를 세팅함
```bash
set MAIL_SERVER=localhost
set MAIL_PORT=8025
```
    3. 디버깅 모드 꺼졌는지 확인(개발 모드에서는 메일 전송 안 됨)  
    4. 두번째 터미널에서 stack trace 확인

2) 실제 이메일 서버를 설정함  
    1. 환경변수 세팅
```bash
    set MAIL_SERVER=smtp.googlemail.com
    set MAIL_PORT=587
    set MAIL_USE_TLS=1
    set MAIL_USERNAME=<your-gmail-username>  #full email address
    set MAIL_PASSWORD=<your-gmail-password>
```
    2. 구글 계정에서 'less secure apps'이 Gmail 계정에 접속할 수 있도록 설정

3) 'SendGrid' : 매일 100통의 메일을 공짜로 보낼 수 있음

## 파일에 로그 남기기
- app/\_\_init\_\_.py 의 app.logger에 RotatingFileHandler 추가
- logging level : DEBUG, INFO, WARNING, ERROR, CRITICAL
- 서버가 리스타트 될 때마다 로그를 남김( INFO: Microblog startup )
```python
file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
```
  10KB씩 최대 10개 파일이며, microblog/logs 밑에 microblog 라는 텍스트 파일로 생성됨
  
## 중복된 Username 버그 고치기
- app/forms.py 에서 EditProfileForm 에 \_\_init\_\_, validate_username 함수 추가. (고친 이름이 원래 자기 이름이랑 다른 경우에만, 기존 db에 바꾼 이름이 없는지 확인함.)
- app/routes.py 의 edit_profile()함수에서 EditProfileForm 생성 시 original_name argument 추가
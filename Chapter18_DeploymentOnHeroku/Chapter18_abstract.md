# 18장 : Deployment On Heroku
- 제 3자 클라우드 호스팅 제공자
- PaaS(Platform as a Service) : 많은 클라우드 호스팅 제공자들은 앱이 돌 수 있는 플랫폼을 제공함. 이 플랫폼에 앱을 배포하기만 하면, HW, OS, scripting 언어 인터프리터, db 등은 모두 서비스에서 관리해줌

- Heroku(헤로쿠) : 파이썬 앱 친화적인 클라우드 호스팅 서비스. 유명하고 공짜 서비스 tier가 있음

## Heroku 에 호스팅하기
- Heroku 에서 웹 앱을 배포하기 위해서는 반드시 git repository에 앱이 있어야 함
- Heroku는 어떻게 앱을 시작할 지 알기 위해서, 앱의 루트 디렉토리에서 **Procfile** 파일을 찾음. 파이썬 프로젝트에서는 Heroku가 requirements.txt 파일도 찾음. git push 동작으로 Heroku 서버에 앱이 업로드된 후에는 앱이 온라인이 될 때까지 몇 초 기다리면 끝임.

## Heroku 계정 생성하기
- https://signup.heroku.com/identity

## Heroku CLI 설치하기
1) https://devcenter.heroku.com/articles/heroku-cli 에서 설치
2) cmd에서 'heroku login' 입력 후 계정 정보 입력

※ 'heroku Login' 입력 시 'Error: self signed certificate in certificate chain'  해결방법
1. 크롬에서 heroku.com 을 염
2. F12 > 보안 탭 > 개요 > 인증서 보기 클릭
3. 인증서 팝업에서 '인증 경로' 탭 클릭
4. 목록 가장 위에 뜨는 인증서 클릭하고 '인증서 보기' 버튼 클릭
5. 다시 뜬 인증서 팝업에서 '자세히' 탭 클릭
6. '파일에 복사' 버튼 클릭
7. 인증서 내보내기 마법사에서 'Base 64로 인코딩된 X.509(.CER)' 선택하고 다음
8. 인증서 저장할 위치 선택하고, 확장자 cer로 되어있는지 확인 후 저장
9. cmd에서 'SET NODE_EXTRA_CA_CERTS=<인증서 저장 위치>' 명령어 실행

## Git 세팅하기
```shell
git clone https://github.com/bibbidi0917/FlaskPractice
cd FlaskPractice/Chapter17_DeploymentOnLinux/microblog
```

## Heroku 앱 생성하기
- 프로젝트 루트 디렉토리에서 apps:create 명령어를 사용하되, 뒤의 앱 이름은 unique해야함 > heroku가 앱에 할당한 URL(https://flask-microblog-jh.herokuapp.com/)이 나오고, Heroku 서버에 있는 깃 레파지토리(https://git.heroku.com/flask-microblog-jh.git)가 나옴

```shell
heroku apps:create flask-microblog-jh
```

## Ephemeral File System
- 가상화된 플랫폼에서 돌아가는 ephemeral 파일 시스템 : 언제든 Heroku가 가상서버를 리셋할 수 있음. 그래서 파일시스템에 영원히 데이터를 저장할 수 있다고 가정하면 안 되고, Heroku는 서버를 매우 자주 recycle함
- 이 특성은 3가지 문제를 낳음  
1) 디폴트 SQLite DB 엔진은 디스크 파일에 데이터를 씀
2) 로그가 파일 시스템에 쓰여짐
3) 컴파일된 언어 번역 레포지토리가 로컬 파일로 쓰여짐

### 1. Heroku Postgres Database 사용하기
- 파일 기반의 SQLite를 피하기 위해서, Heroku 에서 제공하는 Postgres DB 기반의 db로 바꿈
- free tier의 db 생성

```shell
$ heroku addons:add heroku-postgresql:hobby-dev -a flask-microblog-jh

Creating heroku-postgresql:hobby-dev on ⬢ flask-microblog-jh... free
Database has been created and is available
 ! This database is empty. If upgrading, you can transfer
 ! data from another database with pg:copy
Created postgresql-shaped-13169 as DATABASE_URL
Use heroku addons:docs heroku-postgresql to view documentation
```

- 새롭게 만들어진 db의 URL은 DATABASE_URL 환경변수에 있음(이 환경변수는 앱이 Heroku 플랫폼에서 돌 때 쓰임) 아래 명령어로 DATABASE_URL 확인 가능

```shell
$ heroku config -a flask-microblog-jh

=== flask-microblog-jh Config Vars
DATABASE_URL: postgres://~
```

- config.py 에서 SQLALCHEMY_DATABASE_URI 변수 변경 : SQLAlchemy 최근 버전에서는 Postgres db url이 'postgres://'가 아니라 'postgresql://'로 시작하기를 바람 > 그래서 앱이 db와 연결되려면 SQLAlchemy가 요구하는 URL 포맷으로 변경해주어야함

### 2. stdout 에 Log 남기기
- Heroku는 앱이 stdout에 직접적으로 로그를 남기는 걸 기대함. 앱이 standard output으로 프린트하는 모든 것은 저장되고, 'heroku logs' 명령어를 사용하면 반환됨
1) config.py 에 'LOG_TO_STDOUT' 변수 추가

2) app/\_\_init\_\_.py 에서 app.config['LOG_TO_STDOUT'] 가 존재할 경우에는 앱의 logger를 다르게 추가함.

3) Heroku config에 LOG_TO_STDOUT 환경 변수 설정

```shell
$ heroku config:set LOG_TO_STDOUT=1

Setting LOG_TO_STDOUT and restarting ⬢ flask-microblog-jh... done, v5
LOG_TO_STDOUT: 1
```

### 3. 컴파일된 번역
1) 직접적 : ephemeral file 시스템에서 절대 사라지면 안 된다는 옵션을 주어서 깃 레포지토리에 올림
2) Heroku 의 start up 명령에 'flask translate compile' 명령을 포함시켜서, 언제든 서버가 재시작될 때 이 파일이 다시 컴파일될 수 있도록 함. 여기서는 이 옵션을 채택하였음. (Procfile 파일을 작성할 때 이 부분을 포함시킬 예정)

## Elasticsearch 호스팅
- Elasticsearch 는 Heroku 프로젝트에 많이 같이 쓰이지만, Postgres와는 달리 Heroku 에서 제공되는 서비스는 아님. 통합된 Elasticsearch 서비스를 제공하는 3개의 제공자가 있음
- Heroku 에서 제 3자 add-on 을 설치하려면 신용카드 정보가 필요하여, 해당 챕터 실습은 진행하지 않음.

1) 'SearchBox'를 계정에 추가 > 'SEARCHBOX_URL' 환경변수가 세팅됨
```shell
$ heroku addons:create searchbox:starter
```

2) 위의 'SEARCHBOX_URL'을 'ELASTICSEARCH_URL' 환경변수로 세팅
```shell
$ heroku config:get SEARCHBOX_URL
<your-elasticsearch-url>
$ heroku config:set ELASTICSEARCH_URL=<your-elasticsearch-url>
```

- .env 파일에 있는 환경변수들을 'heroku config:set' 으로 Heroku 에 복사해야함. SECRET_KEY, MAIL_SERVER, MAIL_PORT, EMAIL, MS_TRANSLATOR_KEY 세팅함

## Requirements 업데이트하기
- Heroku는 requirements.txt 파일에 dependencies가 있을 것으로 기대함. 그런데 Heroku에서 앱을 돌리려면 2개가 더 추가해야 함

1) gunicorn : Heroku 는 웹 서버를 제공하지 않고, 대신에 'PORT'라는 환경변수로 주어진 포트번호로 이 앱이 뜰거라고 예상함. Flask 개발 웹 서버는 견고하지 않기 때문에, gunicorn을 씀
2) psycopg2-binary : 앱이 Postgres db를 쓰기 때문에 SQLAlchemy 가 psycopg2 또는 psycopg2-binary 패키지를 필요로 함. 그런데 바이너리 패키지가 이미 이 패키지의 built 버전을 설치하고, 따로 C 컴파일러도 필요로 하지 않기 때문에 psycopg2-binary 를 사용함

## Procfile 파일
- heroku 가 어떻게 앱을 실행할 지 알아야하기 때문에, 앱 루트 디렉토리에 'Procfile'이라는 파일이 필요함
1) 'Procfile' 파일 생성 : db 마이그레이션, 언어 번역 컴파일, 서버 시작

```
web: flask db upgrade; flask translate compile; gunicorn microblog:app
```

2) FLASK_APP 환경변수 세팅 : 처음 2개는 flask 명령어에 기반하고 있기 때문에.

```shell
heroku config:set FLASK_APP=microblog.py -a flask-microblog-jh
```

- 동시접속을 관리하기 위해서 gunicorn 의 -w 옵션이 아니라, heroku 에서 config set으로 'WEB_CONCURRENCY' 를 사용하면 됨

## 앱 배포하기

0) 로컬 저장소 만들기

```shell
$ git init
$ cd <내 microblog 경로>
$ heroku git:remote -a flask-microblog-jh
$ git remote -v  # remote 가 heroku 로 나오는 것 확인
$ git add .
```

1) 코드 변경 사항 커밋

```shell
$ git commit -a -m "heroku deployment changes"
```

2) heroku 에 푸시함

```shell
$ git push heroku master
```

3) https://flask-microblog-jh.herokuapp.com/ 와 같은 주소로 접속

- 코드를 업데이트할 때도 동일하게 커밋, 푸시 반복함

※ git push할 때 'SSL certificate problem: self signed certificate' 에러 뜨는 경우, 'set GIT_SSL_NO_VERIFY=0' 환경변수 세팅으로 해결

※ 'psycopg2.errors.UndefinedTable: relation "user" does not exist' 와 같이 테이블이 만들어지지 않았다는 에러가 뜨는 경우, migrations 폴더에 alembic.ini, env.py, script.py.mako 와 같은 파일이 모두 들어있는지 확인


## 이 챕터에서 추가된 파일
- Procfile

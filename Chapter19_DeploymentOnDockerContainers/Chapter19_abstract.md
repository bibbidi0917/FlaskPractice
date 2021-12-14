# 19장 : Deployment on Docker Containers
- Container : 경량의 가상화 기술. 완전하게 격리되어 dependencies와 설정이 관리됨. 컨테이너 호스트로 설정된 시스템은 많은 컨테이너를 실행할 수 있으며, 이 컨테이너들은 호스트의 커널과 호스트의 하드웨어로 직접 접근하는 것을 공유함.  
※ Virtual machine(VM) : 많은 리소스를 필요로 하고 호스트와 비교하여 상당한 성능 저하를 일으킬 수 있는 전체적인 가상화 솔루션. CPU, 디스크, 다른 하드웨어, 커널 등을 포함한 완전한 시스템에서 에뮬레이트 되어야 함

- 커널을 공유해야함에도 불구하고, 컨테이너의 격리 수준은 상당히 높음. 컨테이너는 own 파일 시스템을 가지고 있고, 컨테이너 호스트에서 사용되는 것과는 다른 OS를 사용할 수 있음. (예를 들어 Fedora 컨테이너 호스트에서, Ubuntu Linux 컨테이너를 run할 수 있음) 컨테이너는 Linux OS 에서 나왔지만, Windows 나 Mac OS X 호스트 위에서도 Linux 컨테이너가 run될 수 있음.

## Docker 설치하기
- Docker는 단순히 컨테이너 플랫폼이 아니지만, 지금까지 가장 유명하기 때문에 이것을 사용함. 
1) https://docs.docker.com/get-docker/ 도커 설치  
※ Windows 에서는 Docker가 Hyper-V 를 사용하는데, 이 Hyper-V는 VirtualBox 같은 가상화 기술을 막음

2) cmd 에 'docker version' 입력

## 컨테이너 이미지 만들기
- 컨테이너 이미지 : 컨테이너를 만들기 위해 사용되는 템플릿. 네트워킹, start up 옵션 등 다양한 설정과 컨테이너 파일 시스템에 대한 완전한 표현체임

### 1. Dockerfile 만들기
- **Dockerfile** : docker build 명령어는 이 파일을 읽어서 빌드 instruction을 실행함. 기본적으로 앱이 배포되기 위한 설치 단계들을 실행하는 설치 스크립트이고, 몇몇 컨테이너 특화 설정들이 담겨있음

1) FROM name:tag.  
FROM = 새 이미지가 built될 기본 컨테이너 이미지를 지정  
name = 이미지 이름  
tag = 컨테이너 이미지의 버전. 인터프리터 버전이나 기본 os 등을 명시하는 용도로 사용

2) RUN : 컨테이너 context에서 임의의 명령어 실행

3) WORKDIR : 앱이 설치될 디폴트 디렉토리를 지정. 이 디렉토리에서 Dockerfile의 명령어들이 적용되고, 컨테이너가 실행됨  

4) COPY source dest : 내 머신에서 컨테이너 파일 시스템으로 파일을 옮김. source 파일은 반드시 Dockerfile이 있는 디렉토리와 관련이 있어야 함. destination은 절대경로가 될 수도 있고, WORKDIR 에서 지정한 경로에 대한 상대경로여도 됨.  

5) ENV : 컨테이너 안에서 환경변수를 설정함

6) USER a : a 사용자를 아래 명령들을 수행하는 디폴트 사용자로 지정함

7) EXPOSE : 이 컨테이너가 이 서버를 위해 사용할 포트번호. Docker가 컨테이너 안에서 네트워크를 설정하기 위해 필요함. 포트 5000번이 표준적인 Flask 포트이나, 어떤 포트번호라도 상관없음

8) ENTRYPOINT : 컨테이너가 시작할 때 실행되어야 할 디폴트 명령어를 정의함

```
FROM python:slim
# 'python'이라는 파이썬을 위한 공식적인 도커 이미지를 사용하며, slim version=파이썬 인터프리터가 동작하는 최소한의 패키지만을 담은 컨테이너 이미지 버전을 선택함.

RUN useradd microblog  
# microblog 라는 이름의 새로운 사용자를 만듦

WORKDIR /home/microblog  
# 위에서 사용자를 만들면서 홈디렉토리가 만들어졌기 때문에, 그 홈 디렉토리를 디폴트로 지정함. 

COPY requirements.txt requirements.txt
# requirements.txt 파일을 컨테이너 파일 시스템의 사용자 홈디렉토리인 microblog로 복사함

RUN python -m venv venv
# 가상환경 생성

RUN venv/bin/pip install -r requirements.txt
# 모든 requirement를 설치함

RUN venv/bin/pip install gunicorn
# requirements.txt에는 일반적인 패키지들만 담겨있기 때문에, 웹 서버로 쓸 gunicorn 별도 설치

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./

RUN chmod +x boot.sh
# boot.sh 파일을 실행가능한 파일로 설정함. Unix 기반 파일시스템(Mac OS X 또는 Linux)이라면 소스파일이 이미 실행가능한 것으로 되어있을 것이고, 그러면 복사된 파일도 실행가능함. 그런데 윈도우에서는 이처럼 명시적으로 해주는 게 좋고, 유닉스에서도 이 코드를 실행한다고 문제가 생기지 않으므로 넣음.

ENV FLASK_APP microblog.py
# FLASK_APP 환경변수를 microblog.py 로 지정함

RUN chown -R microblog:microblog ./
# /home/microblog 에 저장된 모든 디렉토리와 파일들의 owner를 microblog 로 설정함. 컨테이너가 시작되었을 때, microblog 사용자가 이 파일들을 다룰 수 있도록 하기 위함

USER microblog
# microblog 사용자로 변경하여, 컨테이너 안에서 이 사용자가 디폴트 사용자로 동작하게 함

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
# 앱 웹 서버를 시작하는 명령어들을 잘 조직화하기 위해서 별도의 스크립트를 만듦. 
```
### 2. boot.sh 파일 만들기
- **boot.sh** : Docker 컨테이너 start-up 스크립트

```
#!/bin/bash
source venv/bin/activate  # 가상환경 활성화
flask db upgrade  
flask translate compile
exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app
# gunicorn 으로 서버 돌림. 
```

- exec : 새로운 프로세스를 스타트하는 게 아니라, boot.sh을 실행하는 프로세스가 주어진 명령어로 대체되는 것을 트리거함. Docker 는 컨테이너의 첫 프로세스를 그 컨테이너의 생명과 관련짓기 때문에 중요함. 이처럼 start up 프로세스(boot.sh 실행)가 컨테이너의 메인 프로세스가 아닌 경우, 메인 프로세스가 그 첫번째 프로세스를 대체하도록 해서 컨테이너가 Docker에 의해 빨리 종료되지 않는 것을 보장해야 함.

- --access-logfile - --error-logfile - : 컨테이너가 stdout 또는 stderr 에 쓰는 모든 것은 '컨테이너'의 로그로 저장됨 > --access-logfile 과 --error-logfile 을 '-'(standard output으로 로그를 보냄) 로 설정해서, Docker에 의해 로그들이 저장되도록 함

### 3. 컨테이너 이미지 빌드하기
```shell
$ docker build -t microblog:latest .
```
-t : 새로운 컨테이너 이미지에 대한 이름과 태그 설정. 이름은 microblog, 태그는 latest  
. : 컨테이너가 built 되는 기본 디렉토리. 이 경우에는 Dockerfile이 위치한 그 디렉토리임. 

### 4. Docker 이미지 확인하기
```shell
$ docker images 
```

## 컨테이너 시작하기
```shell
$ docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    microblog:latest
```

- --name microblog : 새로운 컨테이너의 이름을 microblog로 해라
- -d : 컨테이너를 백그라운드로 돌려라(-d 가 없으면 컨테이너가 foreground 앱으로 돌아서 내 command prompt 에서 끌 수 있음)
- -p 8000:5000 : 호스트 포트와 컨테이너 포트를 매핑함. 8000번으로 호스트에서 접근하면, 내부적으로는 컨테이너가 5000번 포트를 이용함
- --rm : 종료되면 컨테이너 삭제해라. 끝나거나 interrupt된 컨테이너는 대개 더이상 필요가 없기 때문에, 자동으로 지워지도록 함
- -e : 런타임 환경변수 설정. SECRET_KEY 같은 것을 Dockerfile에 build-time 환경변수인 ENV 로 명시하지 않는 이유는, 컨테이너의 이식성 때문임. 만약에 다른 사람에게 앱을 컨테이너 이미지로 준다면, 같이 넘겨주면 안 되는 값들이기 때문임(.env 파일에 선언되어 있는 것들) 

- 컨테이너가 시작되면 http://localhost:8000 으로 접속
- docker run의 결과가 새로운 컨테이너에 부여된 id. 
- docker ps : 돌아가고 있는 컨테이너들을 볼 수 있음
- docker stop ~ : docker ps에서 나오는 짧은 컨테이너 id를 뒤에 명시해줌

## 제 3자 "Containerized" 서비스 사용하기
- DATABASE_URL 환경 변수를 세팅하지 않았기 때문에, 앱이 디폴트인 SQLite db(디스크의 파일)를 가지고 있음. 컨테이너의 파일 시스템은 ephemeral 함=컨테이너가 사라지면 파일도 사라짐.
- 앱 컨테이너를 **stateless**로 만듦 = 컨테이너에는 앱 코드만 담고, 데이터는 아예 안 가지고 있다면 컨테이너를 삭제해도 무방함. 도커 컨테이너 레지스트리는 Microblog 컨테이너의 base 이미지인 Python 컨테이너 이미지처럼 많은 컨테이너 이미지들을 담고 있음.  도커는 많은 다른 언어, db, 서비스들을 위한 이미지를 Docker 레지스트리에 가지고 있고, 회사들이 자신의 상품의 컨테이너 이미지를 레지스트리에  publish 할 수 있음. 즉 제 3자 서비스를 설치하려면 레지스트리에서 적절한 이미지를 찾고 docker run 으로 실행하면 됨
- MySQL db, Elasticsearch 서비스를 위한 2개의 부가적인 컨테이너를 생성한 후, 이 2개 새로운 컨테이너들에 접근할 수 있는 옵션을 붙여서 Microblog 컨테이너를 실행시키고자 함

### MySQL 컨테이너 추가
- MySQL은 도커 레지스트리에 public 컨테이너 이미지를 가지고 있음. 
1) MySQL 배포

```shell
$ docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    mysql/mysql-server:latest
```

2) Dockerfile 에서 pip install 목록에 MySQL 클라이언트 패키지(pymysql, cryptography) 추가

3) 앱이나 Dockerfile 변경하면 컨테이너를 재빌드 해줘야 함(docker build -t microblog:latest .)

4) 아래 옵션 추가하여, microblog 컨테이너 시작하기

```
--link mysql:dbserver \
-e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
```

- --link <컨테이너의 이름 또는 id>:<호스트이름> : Docker 에게 다른 컨테이너가 이 컨테이너에 접근할 수 있다고 말해줌  
ex) --link mysql:dbserver > mysql 컨테이너를 dbserver라고 부를 거고, microblog 컨테이너는 이 mysql 컨테이너와 링크를 가지고 있음

5) boot.sh 에 retry 루프 추가 : MySQL 컨테이너가 시작되고 앱 컨테이너의 연결을 받아들일 준비가 되지 않았을 때, 앱 컨테이너가 시작하면서 boot.sh 의 flask db upgrade 를 실행하면 에러남

```
...
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then  # 정상 동작
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
...
```

### Elasticsearch 컨테이너 추가
- 개발을 위한 싱글 노드와 운영-ready 의 2개 노드 서비스가 있는데, 싱글 노드 옵션을 사용하고, 유일한 오픈 소스 엔진인 oss 이미지를 사용함

1) elasticsearch 배포 : 9200, 9300 2개 포트로 들음. 

```shell
$ docker run --name elasticsearch -d -p 9200:9200 -p 9300:9300 --rm \
    -e "discovery.type=single-node" \
    docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2
```
- 컨테이너 이미지를 지정하는 문법
    1. 로컬 : \<name>:\<tag>  
    microblog:latest
    2. 도커 레지스트리에 있는 컨테이너 이미지 : \<account>/\<name>:\<tag>  
    mysql/mysql-server:latest
    3. 도커 레지스트리에서 host되지 않는 이미지 : \<registry>/\<account>/\<name>:\<tag>  
    docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2 : Elasticsearh는 도커에 의해서 유지되는 메인 레지스트리를 사용하는 것이 아니라, 그들 own 컨테이너 레지스트리 서비스인 docker.elastic.co 에서 돌아감

2) 아래 옵션 추가하여, microblog 컨테이너 시작하기

```
--link elasticsearch:elasticsearch \
-e ELASTICSEARCH_URL=http://elasticsearch:9200 \
```

- 로그 보기

```shell
$ docker logs microblog
```

## Docker Container Registry
- own 컨테이너를 다른 사람들도 이용하게 하고 싶다면 도커 레지스트리에 push 하면 됨
1) https://hub.docker.com 에서 계정 만듦
2) 도커 로그인

```shell
$ docker login
```

3) 계정을 포함하여 이미지 이름을 재정의함 > docker images 해보면 Microblog로 2개가 보이는데, 같은 이미지를 2개의 alias로 부르는 것 뿐임

```shell
$ docker tag microblog:latest <your-docker-registry-account>/microblog:latest
```

4) Docker 레지스트리에 이미지 publish

```shell
$ docker push <your-docker-registry-account>/microblog:latest
```

## Containerized Application 배포
- 도커 컨테이너로 앱을 돌리면, 이 앱을 Docker가 지원되는 어떤 플랫폼에서도 돌릴 수 있음. 
- Amazon Container Service(ECS) : 스케일링, 로드밸런싱, 내 컨테이너를 위한 private한 컨테이너 레지스트리 옵션 등 완전히 통합된 AWS 환경에서 컨테이너 클러스터를 생성함. 
- Kubernetes 같은 컨테이너 오케스트레이션 플랫폼을 이용하면, YAML 파일로 멀티 컨테이너 배포를 설정할 수 있음. 로드밸런싱, 스케일링, secrets 관리, 롤링 업데이트, 롤백 등도 지원함


## 이 챕터에서 추가/수정된 파일
- Dockerfile 추가
- boot.sh 추가
- requirements.txt 에서 heroku 부분의 psycopg2, gunicorn 주석처리

# 17장 : Deployment On Linux

- 실제 사용자들이 접근할 수 있도록 운영 서버에 deploy하는 방법

## Traditional Hosting
- traditional hosting : 앱이 수동설치되거나 stock server 에 스크립트된 installer를 이용하는 것. 이 과정은 앱, dependencies와 운영 스케일 웹 서버를 설치하고, 안전한 시스템을 설정하는 것
- Vagrant 와 VirtualBox : 내 컴퓨터에 가상 서버를 만들 수 있는 공짜 툴
- OS X, Windows는 데스크톱 OS로서 서버로 최적화되지는 않았기 때문에 이 옵션은 버리고, Linux나 BSD OS(유닉스 계열)를 사용함.

## Ubuntu 서버 만들기

1) Vagrant(https://www.vagrantup.com/downloads) 와 VirtualBox(https://www.virtualbox.org/wiki/Downloads) 설치

2) 프로젝트 루트에 'Vagrantfile' 설정 파일 만듦
ubuntu 20.04 server with 2GB of RAM, 호스트 컴퓨터 ip 지정
```
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.network "private_network", ip: "192.168.33.10"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end
end
```

3) vagrant up 으로 서버 생성

## SSH client 사용하기
- OpenSSH
1) Linux, Mac OS X  : OpenSSH 가 이미 설치됨
2) Windows : Cygwin, Git, Windows subsystem for Linux 가 OpenSSH 를 제공하기 때문에, 이들 중 하나를 설치해야함

1) 새 서버의 터미널 세션을 염
```shell
ssh root@<server-ip-address>
```

2) 비밀번호 입력

- Windows 에 Vagrant VM 을 사용한다면, vagrant ssh 를 실행하면 됨

## 패쓰워드 없는 로그인
- Vagrant VM 을 사용한다면 필요없음. Vagrant에 의해서 자동으로 패쓰워드 없는 'ubuntu'라는 이름을 사용하기 때문

- 가상 서버를 사용한다면, 배포할 사용자 계정을 만들고, 패쓰워드 없이 로그인되도록 설정함. 이게 훨씬 편하고 안전함
1) 'ubuntu' 사용자 계정 생성 : 앞선 ssh 명령어를 이용해 루트 계정으로 들어가서  아래 코드 실행
```shell
$ adduser --gecos "" ubuntu  # user 만들고
$ usermod -aG sudo ubuntu  # sudo 권한 주고
$ su ubuntu  # ubuntu 계정으로 들어감
```

2) ubuntu 계정이 공개키 인증을 사용해서 패쓰워드 입력 없이 로그인할 수 있도록 설정.  
두번째 터미널 열어서 ssh 명령어로 연 터미널이어야 함(bash 같은 것, Windows native 터미널이 아니어야함) > ~/.ssh 폴더 안에 id_rsa(비밀키=공유되지 않음), id_rsa.pub(공개키=제 3자에게 나를 identify함) 파일 확인(이 파일이 없다면 'ssh-keygen' 명령어를 실행해서 SSH 키쌍을 만들어야 함 > 이 공개키를 서버에 인증된 호스트로 설정해주어야 함. 공캐키 값을 복사한 다음 ~/.ssh/authorized_keys 에 저장하고 권한 설정  

ssh 가 비밀키를 이용해서 서버에 스스로 identify 하도록 함. 서버는 공개키를 이용해서 로그인을 검증하도록 함.

## 서버 보안
1. SSH를 통해 루트 로그인을 disable  
패쓰워드 없이 ubuntu 계정에 접속할 수 있고, 관리자 명령도 이 계정에서 sudo 로 돌리면 되기 때문에, 루트 계정을 노출할 필요가 없음.  그래서 서버의 /etc/ssh/sshd_config 파일 수정(PermitRootLogin no) 

2. 모든 계정에서 패스워드 로그인을 disable
- /etc/ssh/sshd_config 파일에서 PasswordAuthentication no

- SSH 설정을 변경하고 나면, 서비스가 재시작되어야함
```shell
sudo service ssh restart
```

3. 방화벽 설치 : 22, 80, 443 빼고 다른 포트는 모두 막음
```shell
$ sudo apt-get install -y ufw
$ sudo ufw allow ssh  # 22번 포트
$ sudo ufw allow http  # 80번
$ sudo ufw allow 443/tcp
$ sudo ufw --force enable
$ sudo ufw status
```

## Base Dependencies 설치하기
- 서버에 기본적인 파이썬 인터프리터는 설치되어있지만, 다른 부가적인 패키지들은 안 깔려있음. 그리고 파이썬 외에도 여러 패키지들이 필요함
1) mysql-server
2) postfix : 메일. 운영서버에서 메일 보낼 때는 이것만 이용해서는 안 됨. 스팸 메일을 막으려고, 서버에 대한 도메인 네임을 가지고 있어서 security extension을 통해 스스로 identify 할 수 있는 서버를 요구함. 
3) supervisor : Flask 서버의 동작을 모니터링하다가, crash 되면 자동 리스타트
4) nginx : 외부로부터 오는 모든 요청을 받아들이고 app 에 전달
5) git : 깃 repository에서 앱을 바로 다운받음  
※ Elasticsearch는 RAM 용량을 많이 요구하기 때문에 설치하지 않음. 

```bash
$ sudo apt-get -y update
$ sudo apt-get -y install python3 python3-venv python3-dev
$ sudo apt-get -y install mysql-server postfix supervisor nginx git
```

## 앱 설치하기
1) ubuntu 홈 디렉토리에서 깃 레파지토리 소스코드를 다운
```bash
$ git clone <your-github-address>
$ cd microblog
$ git checkout v0.17
```

2) 가상환경 만들고, 모든 패키지 dependencies를 가상환경에 설치
```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

3) 운영 디플로이에 특화되어 필요한 3개 패키지 설치
    1. gunicorn : 파이썬 앱을 위한 운영 웹 서버
    2. pymysql : SQLAlchemy 가 MySQL db와 같이 동작할 수 있게 MySQL 드라이버를 가지고 있음
    3. cryptography : MySQL db 서버에 대해 인증하기 위해 pymysql에 의해 사용됨

```bash
(venv) $ pip install gunicorn pymysql cryptography
```

4) 환경변수 설정을 위해 /home/ubuntu/microblog/.env 파일 생성
```bash
SECRET_KEY=<your-secret-key>
MAIL_SERVER=localhost
MAIL_PORT=25
DATABASE_URL=mysql+pymysql://microblog:<db-password>@localhost:3306/microblog
MS_TRANSLATOR_KEY=<your-translator-key-here>
```
여기서 SECRET_KEY 를 생성하기 위해 python3 -c "import uuid; print(uuid.uuid4().hex)" 를 사용함

5) ubuntu 계정의 ~/.profile 파일에 FLASK_APP 환경변수 설정 : 로그인할 때마다 자동으로 설정되도록 함
```bash
$ echo "export FLASK_APP=microblog.py" >> ~/.profile
```

6) 다국어 번역 컴파일
```bash
(venv) $ flask translate compile
```

## MySQL 설정하기
1) mysql root 사용자로 접속 : db 서버를 다루기 위해 mysql 명령어 사용(이미 서버에 설치되어있는 명렁어임)

```bash
$ sudo mysql -u root  # MySQL root 유저로 접근하려면 sudo 명령어 필수
```

2) db 설정

```bash
# microblog 라는 새로운 db 생성
mysql> create database microblog character set utf8 collate utf8_bin;

# 사용자 생성
mysql> create user 'microblog'@'localhost' identified by '<db-password>';

# full access 할 수 있음
mysql> grant all privileges on microblog.* to 'microblog'@'localhost';
mysql> flush privileges;
mysql> quit;
```

3) db 마이그레이션
```bash
(venv) $ flask db upgrade
```

## Gunicorn 과 Supervisor 설정하기
- flask run 으로 서버를 돌릴 때 Flask에서 나온 웹서버를 사용했었는데, 이 서버는 개발할 때는 유용하나 성능과 robustness 측면이 부족함. Flask 개발서버 대신, gunicorn(구니콘) 사용
- gunicorn : 순수한 파이썬 웹 서버. 많은 사람들이 사용할 수 있는 견고한 운영서버
- gunicorn 하에서 Microblog를 시작
```bash
(venv) $ gunicorn -b localhost:8000 -w 4 microblog:app
```
    1. -b localhost:8000 : localhost:8000 에서 요청을 들어라. 클라이언트로부터 요청이 왔을 때 static 파일을 최적으로 제공해주는 매우 빠른 웹 서버가 됨. 내부 서버에 요청을 빠르게 전달함. nginx 를 public facing server로 설정하는 방법에 대해서는 다음 섹션에 설명.
    
    2. -w 4 : gunicorn을 돌릴 때 동시 요청자를 몇 명 허용할 것인가? (worker)
    3. microblog:app : gunicorn 에 앱 인스턴스를 어떻게 load할 지 알려줌. 앱을 담고 있는 모듈:앱의 이름
    
- supervisor : 운영서버를 command-line으로 run하는 것은 좋은 방법이 아님. 서버가 백그라운드에서 돌면서, 지속적인 모니터링 하에 있고, 만약에 crash 발생하면 자동으로 새 서버가 시작하는 것을 바람
1) supervisor 는 config 파일을 사용함. 반드시 /etc/supervisor/conf.d/microblog.conf 경로에 생성

```conf
[program:microblog]
command=/home/ubuntu/microblog/venv/bin/gunicorn -b localhost:8000 -w 4 microblog:app
directory=/home/ubuntu/microblog
user=ubuntu
autostart=true  # 컴퓨터가 시작하거나 crash되었을 때 자동 시작
autorestart=true
stopasgroup=true  # supervisor가 새시작을 위해 앱을 멈춰야할 때, 탑레벨 gunicorn 프로세스에서 자식 프로세스까지 도달할 수 있도록 함
killasgroup=true
```


2) 설정파일 고쳐서, supervisor 서비스 리로드해야 함
```bash
$ sudo supervisorctl reload
```

## Nginx 설정하기
- gunicorn에 의해 켜진 microblog 앱 서버가 로컬 8000번에서 돌고 있음. 외부로 이 앱을 노출시키기 위해서는 내 public facing web server 가 80과 443 포트에서 가능해야 함.
- 안전한 배포를 위해 80포트로 오는 모든 트래픽을 443으로 보내도록 설정. 자체 서명된 SSL 인증서를 생성함. 신뢰받는 인증 기관에서 발급된 인증서가 아니면 웹브라우저가 사용자에게 경고를 주기 때문에, 실제 배포에는 적합하지 않음

1) SSL 인증서 생성

```bash
$ mkdir certs
$ openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
  -keyout certs/key.pem -out certs/cert.pem
```
SSL 인증서에 포함될 몇 개 정보들을 입력하면, key.pem과 cert.pem 파일이 생성됨

2) 웹사이트가 nginx 로 서비스되도록 하려면, 설정 파일을 써야함. /etc/nginx/sites-enabled 경로.
    1. /etc/nginx/sites-enabled/default 에 있는 필요없는 test site 삭제
    ```bash
    $ sudo rm /etc/nginx/sites-enabled/default
    ```
    2. /etc/nginx/sites-enabled/microblog 파일 생성
    
3) 설정 파일 reload
```bash
$ sudo service nginx reload
```

- 도메인을 가지면 'Let's Encrpyt' 의 공짜 SSL 인증서를 요청할 수 있음.(https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https 참고)

## 앱 upgrade해서 배포하기
```bash
(venv) $ git pull                              # download the new version
(venv) $ sudo supervisorctl stop microblog     # stop the current server
(venv) $ flask db upgrade                      # upgrade the database
(venv) $ flask translate compile               # upgrade the translations
(venv) $ sudo supervisorctl start microblog    # start a new server
```

## Raspberry Pi 호스팅
- Raspberry Pi : 저비용, 저전력의 혁신적인 작은 리눅스 컴퓨터. 웹 서버가 있기에 가장 완벽한 장치. 
1) Raspberry Pi OS 설치(데스크탑 사용자 인터페이스가 필요없어서 Lite 버전 설치)
2) SD 카드에 Respberry Pi OS 이미지를 복사하여 설치
3) Raspberry Pi를 처음으로 부팅시킬 때는 키보드나 모니터에 연결되게 해야 함. SSH를 가능하게 해서 컴퓨터에서 로그인이 가능하도록 하면 배포가 더 편리해짐.

## 이 챕터에서 추가된 파일
- Vagrantfile
- deployment/nginx/microblog
- deployment/supervisor/microblog.conf

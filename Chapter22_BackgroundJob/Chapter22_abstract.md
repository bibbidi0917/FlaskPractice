# 22장 : Background Jobs
- 웹 서버와 독립적으로 돌아가는 백그라운드 잡을 생성하는 방법
- 태스크를 수행하는 동안 클라이언트에게 응답이 가는 것을 막아서, request context에서는 동기적으로 실행될 수 없는 프로세스들. Chapter 10에서 사용자들이 이메일 보내는 동안 3~4초를 기다리지 않게 하려고 이메일 보내는 것을 백그라운드 쓰레드로 옮겼지만, 프로세스가 이보다 더 길어지면 이 방법도 적절치 않음
- export 기능 도입 : Microblog에 사용자가 본인의 블로그 포스트를 데이터 파일로 요청하는 'export' 기능을 도입함. export 태스크 시작하면 사용자의 모든 포스트를 JSON 파일로 만들고 > 사용자에게 이메일로 보내줌. 이 모든 동작은 worker 프로세스에서 이루어질 것이고, 사용자는 완료 퍼센트를 notification으로 볼 수 있음

## Task Queues
- Task Queue : 앱이 **worker process**에 의해 태스크가 실행되도록 요청하는 편리한 방법. worker 프로세스들은 앱과 독립적으로 돌아가며, 심지어 다른 시스템에 위치할 수도 있음. 앱과 workers 와의 통신은 **message queue**를 통해 함. 앱이 job을 제출하고 queue와 통신하면서 그것의 progress나 result를 받음.  

※ **App server** --submit job--> **Message Queue** --Accept Job--> **Worker**  
**App server** <--Get Progress/Results-- **Message Queue**  <--Write Progress/Results-- **Worker** 

- python의 태스크 큐
1) Celery : 가장 유명. 많은 옵션과 여러 메시지 큐를 지원함. 
2) Redis Queue(RQ) : 오직 Redis 메시지 큐만 지원하나, Celery 보다는 셋업이 간단함

- 둘다 Flask 앱에 적절하나, RQ가 간단하기 때문에 RQ를 선택함. 

## RQ 사용하기
- RQ 설치

```shell
(venv) $ pip install rq
(venv) $ pip freeze > requirements.txt
```

- 앱 - Redis 메시지 큐 - RQ workers
- Redis server 필요 : Windows OS이면 https://github.com/MicrosoftArchive/redis/releases 에서 다운로드 받음(Redis-x64-3.0.504.msi). Redis과 interact 할 필요없이, RQ를 통해서 접근할 것임.
- Windows native 파이썬 인터프리터에서는 RQ가 돌아가지 않음. Unix 에뮬레이션 아래에서만 RQ가 돌아가므로, Cygwin 이나 Windows Subsystem for Linux (WSL) 같은 유닉스 에뮬레이션 레이어를 깔아야 함

※ WSL을 사용하여 이하 실습을 진행함

### 1. Task 만들기
- app/tasks.py 에 example(seconds) 함수 생성

### 2. RQ Worker 돌리기

```shell
(venv) $ rq worker microblog-tasks  # 'microblog-tasks' 큐를 바라보는 worker 생성
```
- worker 프로세스가 Redis에 연결되었고, worker 프로세스들은 이 'microblog-tasks' 큐로 할당되는 job들이 있는지 지켜보고 있음. 만약 여러 worker 들을 만들고 싶다면, 똑같이 위 명령어를 수행해서 똑같은 'microblog-tasks' 큐에 연결된 worker를 만들면 됨 > 나중에 큐에 job이 들어오면 가능한 worker 프로세스 중에 아무나 job을 집어서 함. 운영 환경에서는 CPU가 허락하는 한 많은 worker들이 필요할 것임.

### 3. Task 실행하기
- 두번째 터미널을 열어서 가상환경을 실행시키고, flask shell 세션으로 들어가서 아래 코드 실행

```python
>>> from redis import Redis
>>> import rq
>>> queue = rq.Queue('microblog-tasks', connection=Redis.from_url('redis://'))
>>> job = queue.enqueue('app.tasks.example', 23)  # 큐에 job 넣기
>>> job.get_id()
'68fdf44f-c347-4ec6-93ea-e87bd5f1317a'
>>> job.is_finished
False
>>> job.is_finished  # enqueue 23초 뒤
True
```
※ AttributeError: module 'os' has no attribute 'fork' >> os.fork()가 리눅스 명령어이기 때문에 Windows 환경에서 실행하면 에러가 남. 위의 '※ Windows 10 에서 WSL 사용' 부분을 참고할 것.

- rq.Queue('큐 이름', Redis 연결 오브젝트) : 앱에서 바라보는 task queue 생성
- enqueue('실행하고 싶은 함수 오브젝트나 import string') : import string(app.tasks.example 형태)이 편리함. 추가로 넘어가는 인자들은 worker에서 함수가 돌아갈 때 전달됨. enqueue 하자마자 첫번째 터미널에서 RQ worker가 job을 수행함. 그리고 두번째 터미널은 enqueue하고 멈추지 않고, 계속 다른 명령어(job.get_id())를 쓸 수 있는 상태임
- 큐에 있는 태스크들은 디폴트로 500초 동안 머물고, 결국엔 없어짐. 중요한 건, 이 태스크 큐는 실행한 job에 대한 히스토리를 보관하지는 않는다는 점

### 4. Task Progress 리포트하기
- job.meta : 딕셔너리 형태. 태스트가 앱과 소통을 원하는 어떤 커스텀 데이터도 모두 쓸 수 있음

```python
def example(seconds):
    ...
    for i in range(seconds):
            job.meta['progress'] = 100.0 * i / seconds
            job.save_meta()
            # RQ 에서 Redis에 데이터를 Write하라고 알려줌. 그래서 나중에 앱이 그 메타데이터를 찾을 수 있음
    ...
```

- 앱에서는 아래와 같이 확인 (뒤에 구현된 코드를 보면, 정적으로 표시해주기 위해서는 job.meta.get('progress', 0) 이걸 쓰지만, 동적으로 할 때는 job.meta['progress'] 이걸 불러서 아는 게 아니라 직접 계산해서 나온 것을 바로 Noti에 넣어줌)

```shell
job = queue.enqueue('app.tasks.example', 23)
>>> job.meta
{}
>>> job.refresh()  # Redis로부터 content를 업데이트 받기 위해서 반드시 불러야 함!
>>> job.meta
{'progress': 13.043478260869565}
```

## Tasks 에 대한 Database 표현
- 태스크들 중 하나가 시작할 때 request는 끝나고, 태스크에 대한 모든 context들이 사라짐. 각 사용자가 돌리는 태스크들을 추적하기 위해서, Task 모델을 만듦
- app/models.py 에 Task 모델 추가, User 클래스에 Task와의 db.relationship 추가

```python
class Task(db.Model):
    # db에서 제공하는 PK를 쓰지 않고, RQ에서 생성된 Job id 사용
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)  # app.tasks 안의 함수명
    description = db.Column(db.String(128))  # 사용자들에게 보여주는 내용
    # name=export_posts 이면, description=Exporting posts...
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # running 태스크들은 progress를 보여주기 위해 특별한 핸들링이 필요하기 때문
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
            # id가 일치하며, Redis 에 존재하는 Job 인스턴스를 반환
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
        # job이 rq에 없다는 건 이미 끝났다는 것
        # job.meta에 'progress' 값이 없다는 건, job이 rq에서 기다리고 있다는 것
```

- db 마이그레이션
- microblog.py 에서 Task 도 쉘 스크립트에 추가

## Flask 앱에 RQ 통합하기
- config.py : 'REDIS_URL' 변수 추가
- app/\_\_init\_\_.py : Redis, RQ 초기화 추가. current_app.task_queue 로 RQ 접근가능

- app/models.py User 클래스 : 앱에서 태스크를 submit하거나 체크하기 편하려고 User에 launch_task(RQ에 태스크 submit), get_tasks_in_progress(본인의 진행중인 task들), get_task_in_progress(해당 이름을 가진 태스크 검색. 같은 이름 태스크 여러 개 못 돌리게 하기 위함) 함수 추가  
launch_task 함수에서는 db.session.add(task)만 하고 커밋은 안 하고 있음. low level 함수들의 update들을 모아서, 높은 레벨 함수에서 한 번에 커밋할 예정

## RQ 태스크에서 이메일 보내기
- export 태스크가 끝나면, 모든 포스트를 담은 JSON 파일이 사용자에게 메일로 보내져야함
1) 파일 첨부 기능
2) 현재의 send_email()은 항상 백그라운드 쓰레드를 이용해서 비동기로 이메일을 보냄 > 동기와 비동기 메일을 둘다 지원

- app/email.py

```python
def send_email(subject, sender, recipients, text_body, html_body,
               attachments=None, sync=False):
    ...
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
            # 함수의 인자로 리스트나 튜플을 넣을 때, *args 사용.
            # attach(attachment[0], attachment[1], attachment[2])를 줄여쓴 것
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
            args=(current_app._get_current_object(), msg)).start()
```
- attachment 의 인자 3가지 
1) filename : 받는 사람이 첨부파일 이름으로 보는 것
2) media type : ex) image/png, application/json
3) file data : string or byte sequence

## Task helpers
- app/tasks.py : 태스크들이 db 접근(Flask-SQLAlchemy)이나 이메일(Flask-Mail) 보내는 기능이 필요함. Flask-SQLAlchemy 나 Flask-Mail을 사용하려면, Flask 앱 인스턴스에 있는 설정값이 필요하기 때문에 tasks.py 에 앱 인스턴스와 context를 추가해줌

```python
app = create_app()
app.app_context().push()
```

- tasks.py 에서 앱을 만드는 이유 : RQ worker 가 import할 유일한 모듈이기 때문. flask 명령어를 치면 루트 디렉토리의 microblog.py 모듈에서 앱을 만드는데, RQ worker는 아무것도 모름. 그래서 고유한 앱 인스턴스를 tasks.py에서 쓸 수 있게 만들어주는 것임
- context를 푸시하면 이 앱을 "현재" 앱 인스턴스로 만들어줌. 그래서 current_app 이라는 표현을 쓸 때, 방금 생성된 이 앱 인스턴스를 받아올 수 있음.

- job.meta 딕셔너리로 progress 정보를 얻는 것에 추가로, 클라이언트한테 notification을 푸시하고 싶음. 그래서 사용자가 페이지를 리프레시하지 않고 동적으로 완료 퍼센티지를 업데이트 받도록 하고 싶음  
서버가 템플릿을 렌더링 > job.meta 에서 받은 정보로 "static"한 progress 정보를 보여줌 > 알림 기능을 이용해서 동적으로 사용자 화면에 progress 정보 업데이트. 
- 이를 위해 app/tasks.py 에 _set_task_progress(progress) 함수 추가. 받은 progress를 meta에 저장하고, user.add_notification함. 

```python
def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()
        # 부모 태스크에서 db 변화를 만들지 않도록 디자인함. 왜냐하면 이 커밋이 부모 태스크 쪽까지 같이 커밋하기 때문.
```

## Export 태스크 구현하기
- app/tasks.py 에 export_posts(user_id) 함수 추가

```python
def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                        'timestamp': post.timestamp.isoformat() + 'Z'})  # UTC
            time.sleep(5)  # 그냥 progress를 화면에서 천천히 보려고 추가한 것
            i += 1
            _set_task_progress(100 * i // total_posts)
            
        send_email('[Microblog] Your blog posts',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html', user=user),
                attachments=[('posts.json', 'application/json',
                              json.dumps({'posts': data}, indent=4))],
                sync=True)
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)
```

- 왜 try/except 블록으로 감싸는가? request 핸들러에 존재하는 앱 코드는 예상치 못한 에러들로부터 보호받음. 왜냐하면 Flask가 exception을 잡아서 에러를 핸들링하고 로그도 남겨줌. 그런데 이 함수는 Flask가 아니라 RQ에 의해 컨트롤되는 분리된 프로세스에서 돌아감. 그래서 예상치 못한 에러가 발생하면 태스크가 abort 되고, RQ가 콘솔에 에러를 보여주며, 새로운 job을 기다리러 가버림. 그래서 RQ worker의 결과를 보거나 그걸 파일로 로깅하지 않으면, 에러를 찾을 수 없음

- 이메일 양식 2개 추가. app/templates/email/export_posts.txt, app/templates/email/export_posts.html

## 앱에서의 Export 기능
- app/main/routes.py : '/export_posts' 루트 추가. 이미 export 태스크를 실행했는지 확인하고, 없으면 태스크를 시작함
- app/templates/user.html : 로그인된 본인의 프로필 화면이고, export 태스크가 실행중이지 않으면 'Export your posts' 링크 추가

※ 테스트 방법 : 3개의 powershell  
1) 앱 서버 : flask run
2) 메일 서버 : python3 -m smtpd -n -c DebuggingServer localhost:8025
3) Redis : rq worker microblog-tasks

## Progress 알림
- 사용자에게 백그라운드 태스크가 몇 퍼센트 돌아가고 있는지 알려주고 싶음
- app/templates/base.html : flash 메시지 위쪽에 progress 메시지를 초록색 배경으로 표시

```html
{% if current_user.is_authenticated %}
    {% with tasks = current_user.get_tasks_in_progress() %}
        {% if tasks %}
            {% for task in tasks %}
           <div class="alert alert-success" role="alert"> <!-- alert-success, alert-info 로 색깔 구분 -->
                {{ task.description }}
                <span id="{{ task.id }}-progress">{{ task.get_progress() }}</span>%
            </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
{% endif %}
```

- app/templates/base.html : set_task_progress 함수로 \<span id="{{ task.id }}-progress"> 의 값 변경
- $('#' + task_id + '-progress').text(progress) 이런 걸 할 때, 그 요소가 존재하는지 검증할 필요가 없음. jQuery는 주어진 선택자에 아무런 요소도 없으면, 아무것도 하지 않음.

※ app/tasks.py 의 export_posts < 포스트 하나당 _set_task_progress 호출 < _set_task_progress 안에서 task.user.add_notification 함. 즉, 포스트 하나씩 뽑고 있을 때마다 'task_progress' 알림이 업데이트 됨

- app/templates/base.html : ready function에서 10초에 한 번씩 알림 가져올 때, done 함수에 'task_progress' 로직도 switch 문으로 추가

```html
...
switch (notifications[i].name) {
    case 'unread_message_count':
        set_message_count(notifications[i].data);
        break;
    case 'task_progress':
        set_task_progress(
            notifications[i].data.task_id,
            notifications[i].data.progress);
        break;
}
...
```

- flask translate update 후, messages.po 파일을 업데이트하고 flask translate compile

## Deployment Considerations
- Redis 서버와 RQ worder를 앱에 추가해서, 이것도 배포에 들어가야함. 
### 1. Linux Server에서 배포
1) sudo apt-get install redis-server
2) deployment/supervisor/microblog-tasks.conf 파일을 추가하여 아래 내용 넣음

```conf
[program:microblog-tasks]
command=/home/ubuntu/microblog/venv/bin/rq worker microblog-tasks
numprocs=1  # numprocs : worker의 수
directory=/home/ubuntu/microblog
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```

### 2. Heroku 에서 배포
1) 내 계정에 Redis service 추가

```shell
$ heroku addons:create heroku-redis:hobby-dev
```
※ 이 add-on 설치를 위해서는 신용카드 정보 입력이 필수이므로, 실습 제외

2) REDIS_URL 환경변수 추가

```shell
$ heroku config:set REDIS_URL=<redis url>
```

3) Procfile 에 아래 내용 추가(무료 버전에서는 1개의 worker만 가능)

```
...
worker: rq worker -u $REDIS_URL microblog-tasks
```

4) deploy 할 때, 아래 명령어로 worker 시작

```shell
$ heroku ps:scale worker=1
```

### 3. Docker 에서 배포
1) Redis 컨테이너 만들기 : Docker 레지스트리에서 공식 Redis 이미지를 이용할 수 있음

```shell
$ docker run --name redis -d -p 6379:6379 redis:3-alpine
```

2) docker run할 때 redis에 대한 link와 REDIS_URL 환경변수 추가

```shell
$ docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --link mysql:dbserver --link redis:redis-server \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
    -e REDIS_URL=redis://redis-server:6379/0 \
    microblog:latest
```

3) RQ worker를 위해 여러개의 컨테이너가 필요한 경우, start up 명령어를 아래와 같이 override해서 worker가 앱 대신에 시작되게 할 수도 있음 : rq-worker 컨테이너가 시작될 때, start up 명령어가 venv/bin/rq 임

```shell
$ docker run --name rq-worker -d --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --link mysql:dbserver --link redis:redis-server \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
    -e REDIS_URL=redis://redis-server:6379/0 \
    --entrypoint venv/bin/rq \
    microblog:latest worker -u redis://redis-server:6379/0 microblog-tasks
```

## 이 챕터에서 추가된 파일
- app/tasks.py
- migrations/versions 에 "tasks" 스크립트
- app/templates/email/export_posts.txt
- app/templates/email/export_posts.html
- deployment/supervisor/microblog-tasks.conf


## 이 챕터에서 변경된 파일
- microblog.py
- config.py
- app/\_\_init\_\_.py
- app/models.py
- app/email.py
- app/main/routes.py
- app/templates/user.html
- app/templates/base.html
- requirements.txt
- Procfile
- app/translations/es/LC_MESSAGES/messages.po

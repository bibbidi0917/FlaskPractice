# 21장 : User Notifications
- private message : 다른 사람의 프로필 화면 링크를 클릭하여, 그 사용자에게 메시지를 보낼 수 있는 기능
- 페이지 리프레시 없이 네비게이션 바에 읽지 않은 메시지 수를 표시하는 알림 배지가 나오도록 함. 이 배지를 클릭하면 자신에게 온 메시지를 읽을 수 있음

## Private Message

### 1. Database
- app/models.py 에 Message 클래스 추가, User 클래스에 보낸 메시지/받은 메시지 db.relationship 추가, 마지막으로 메시지 읽은 시간 컬럼 추가, new_messages()= last_read_time 이후로 읽지 않은 메시지 개수 리턴하는 함수 추가
- db 마이그레이션

### 2. Private Message 보내기
- app/main/forms.py 에 MessageForm 클래스 추가
- app/templates/send_message.html 파일 추가
- app/main/routes.py 에 '/send_messages/\<recipient>' url 매핑 추가
- app/templates/user.html 에 'Send Private Message' 링크 추가

### 3. Private Message 보기
- app/main/routes.py 에 '/messages' 루트 추가
- app/templates/messages.html 파일 추가
- app/templates/base.html 에 "Messages" 링크 추가
- flask translate update 해서 언어 카탈로그 업데이트하고, messages.po 에 새로운 번역 넣은 후 flask translate compile 실행

## 정적인 Message 알림 배지
- Bootstrap 배지 위젯 > 새로운 페이지가 로드될 때만 배지가 업데이트되며, 그 페이지가 로드될 당시에 읽지 않은 메시지가 있는 경우에만 배지가 보임
```html
<li>
    <a href="{{ url_for('main.messages') }}">
        {{ _('Messages') }}
        {% set new_messages = current_user.new_messages() %}
        {% if new_messages %}
        <span class="badge">{{ new_messages }}</span>
        {% endif %}
    </a>
</li>
```

## 동적인 Message 알림 배지
- app/templates/base.html 에  \<span id="message_count"> 추가, set_message_count 함수 추가로 읽지 않은 메시지가 있는 경우에만 배지가 보이도록 함

## 알림을 클라이언트에 전달하기
- 클라이언트가 주기적으로 읽지 않은 메시지의 수를 업데이트 받는 기능. 업데이트 되면 set_message_count 함수를 불러서 사용자 화면에 표시함
- 서버가 클라이언트에 업데이트해주는 방법 2가지 : 장단점이 존재하여 프로젝트에 맞는 것을 선택하면 됨
1) **Ajax** : 클라이언트가 서버에 비동기 요청을 보내서 받아온 데이터로 화면 일부를 업데이트함 : 구현하기 쉬움. 예를 들어 /notifications 를 불러서 알림의 JSON 리스트를 받아온 다음 화면에 뿌림.  
클라이언트가 주기적으로 서버를 불러서 결과를 얻기 때문에, 실제 메시지가 온 시간과 알림이 오는 시간이 다를 수 있음.  
ex) Twitter, Facebook(long pulling=서버가 HTTP 요청을 붙잡고 새로운 정보가 생길 때까지 기다림. 기다리는 시간에 대해 time limit을 줌)

2) **WebSocket** : 서버가 자유롭게 클라이언트에 데이터를 푸시할 수 있는 특별한 유형의 연결이 필요함. HTTP는 클라이언트의 요청 없이 서버가 클라이언트한테 데이터를 못 보냄. 반면 Websocket은 서버와 클라이언트 간의 영속적인 연결을 만들어서, 요청없이도 서버와 클라이언트 모두 데이터를 보낼 수 있음.  
딜레이 없이 서버가 알림을 보낼 수 있지만, WebSocket은 훨씬 복잡한 셋업이 필요함. 왜냐하면 서버가 모든 각 클라이언트와 영속적인 연결을 유지해야하기 때문. 예를 들어 4개의 worker process를 가진 서버가 몇 백명의 HTTP 클라이언트에게 서비스를 제공하고 있을 때, HTTP 연결은 짧기 때문에 그 4개가 계속 재활용될 수 있음. 그런데 같은 서버가 4개의 웹소켓 클라이언트로 다뤄진다면, 대부분의 경우에는 연결이 부족함. 웹소켓 앱은 많은 worker와 active 연결을 다루는 데에 효율적인 '비동기 서버'로 주로 디자인됨. zero-latency에 가깝게 업데이트가 전달되어야하는 앱에서 사용함  
ex) Stack Overflow, Trello
- 어떤 방식을 사용하든, 클라이언트에서는 업데이트 리스트와 같이 invoke되는 콜백 함수가 있어야 함

1) app/models.py 에 Notification 클래스 추가, User 클래스와의 관계 추가

```python
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)  # 알림 종류. ex) 'unread_message_count'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)  # time.time()
    payload_json = db.Column(db.Text)  # 알림의 유형마다 달라질 수 있어서, json 스트링 사용. 싱글 밸류, 딕셔너리, 리스트 모두 작성 가능

    def get_data(self):
        return json.loads(str(self.payload_json))  # JSON 을 deserialization함
```

2) db 마이그레이션

3) microblog.py : 편의상 shell context에 Message와 Notification 모델도 추가해서, flask shell 명령어로 쉘을 시작했을 때 자동으로 import 되도록 함

4) app/models.py 의 User 클래스에 add_notification(self, name, data) 함수 추가 : 같은 이름으로 알림이 있으면, 지우고 새로 알림을 만들어서 세션에 추가함

5) app/main/routes.py 의 send_message() 함수에서, 메시지 보내지면 user.add_notification 호출 : 메시지 받는 사람의 notification에 읽지 않은 메시지 수(user.new_messages())를 저장함

6) app/main/routes.py 의 messages() : 메시지 화면에 들어가기 전에 읽지 않은 메시지 수를 0으로 만들고, last_message_read_time 도 현재 시각으로 저장  
user.add_notification()이 불리면서 payload_json의 data가 0으로 들어감. 그래서 notifications의 timestamp인 since도 0이 됨 > 이 상태에서 한 번 더 /notifications 가 불리면 since보다 큰 timestamp 다 가져오니까, 결국 since는 알림 받은 최신 timestamp로 다시 바뀜

7) app/main/routes.py 에 '/notifications' 루트 추가 : 알림 배지의 중복 업데이트를 막기 위해서 현재 로그인된 사용자의 알림 중 since보다 이후 것만 JSON 형태로 리턴함

> Q. since가 왜 필요한가?  
A. 읽지 않은 메시지 수를 나타내는 배지 영역을 10초에 한 번씩 갱신할 필요가 없기 때문.  
다른 사람이 메시지를 보내서 내 Notification 테이블 행의 timestamp 가 1639556961.1422994 로 갱신되면, 내 since는 이전의 1639556389.3228135 이기 때문에 새로운 노티를 가지고 base.html로 감. done 함수에서 set_message_count 함수가 불리면서 배지 영역이 업데이트됨. 그리고 since 데이터가 새로운 노티의 timestamp인 1639556961.1422994 로 갱신됨. 그래서 다음 번 /notifications가 돌 때는 since보다 timestamp값이 큰 noti가 없기 때문에 계속 갱신되지 않고, 리턴 값이 없어서 set_message_count 함수도 불리지 않으며 since도 갱신되지 않음


> Q. base.html 에서 current_user.new_messages() 는 왜 필요한가?  
A. new_messages로 세팅하는 부분이 빠지면, 메인 화면에 진입해서 최초 Ajax를 부르기 전까지 읽지 않은 메시지 개수가 뜨지 않음. 그래서 정적인 Message 알림 배지로 초기 화면에서 배지를 표시해준 다음에, 동적인 Message 알림 배지 로직(Ajax)를 돌려서 그 숫자를 변경해주는 것

> Q. since가 언제 갱신되는가?  
A. 다른 사람이 나한테 메시지를 보내서 Noti가 생겼고, 그 값이 배지로 표시되고 난 후에 갱신됨

8) app/templates/base.html 알림을 위한 Polling 추가 : query string은 url_for()를 사용할 수 없기 때문에, since 변수는 동적으로 붙여줘야 함

※ 하나는 Edge, 하나는 크롬으로 서로 다른 사용자로 로그인함  
※ 서버 단의 에러 로그 없이 기능이 정상 동작하지 않을 경우, F12 켜보기(JavaScript 단에서 값이 없는 변수를 참조하는 오류 때문에 기능이 정상 동작하지 않았음)

## 이 챕터에서 추가된 파일
- migrations/versions 에 "private messages", "notifications" 관련 파일
- app/templates/send_message.html
- app/templates/messages.html


## 이 챕터에서 변경된 파일
- microblog.py
- app/models.py
- app/main/forms.py
- app/main/routes.py
- app/templates/user.html
- app/templates/base.html
- app/translations/es/LC_MESSAGES/messages.po

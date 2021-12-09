# 12장 : Dates and Times

- 사용자들이 어디에 사는지에 관련없이, 모든 사용자들에게 dates와 times를 적합하게 보여주고 싶음.

## Timezone Hell
- 날짜와 시간을 렌더링하기 위해서 서버의 Python을 사용하는 것은 좋은 생각이 아님.

```shell
>>> from datetime import datetime
>>> str(datetime.now())  # 내 위치의 시간
'2021-12-09 09:04:56.705637'
>>> str(datetime.utcnow())  # UTC
'2021-12-09 00:05:06.462606'
```
※ UTC = Universal Time Coordinated = 협정 세계시. 그리니치 평균시(GMT)에 기반하나 초의 소숫점 단위 정도 차이남.
- 서버는 시간을 위치 독립적으로 관리해야함.  
만약 이 앱이 세계의 서로 다른 지역에 여러 대의 운영 서버를 가지고 있을 때, 각 서버가 다른 타임존으로 db에 timestamp를 남기게 하고 싶지 않음. UTC는 가장 많이 사용되는 uniform한 타임존이고, datetime 클래스에서 지원되므로 UTC를 사용함.
- 그러나 UTC 시간을 그대로 사용자에게 보여주는 것은 문제가 있음. 

## Timezone 전환
- UTC로 저장된 모든 타임스탬프를, 각 로그인한 사용자의 지역 시간으로 변경해서 보여줌. 이 방식에서는 각 사용자의 위치를 아는 것이 어려운 부분임.
- 많은 웹사이트에서는 가입할 때 사용자들이 자신의 타임존을 지정할 수 있는 설정페이지를 가지고 있음. 그런데 사용자들이 직접 입력하게 하는 것보다는, 사용자들의 os에 있는 타임존을 가지고 오는 게 더 나음.
- 웹 브라우저가 사용자들의 타임존을 알고 있고, 그걸 JavaScript API로 제공하고 있음  
1) "old school" approach : 사용자가 최초로 앱에 로그인했을 때, 웹 브라우저가 타임존 정보를 Ajax나 meta refresh tag를 이용해서 서버에 보냄. 서버는 유저의 세션이나 db에 타임존을 저장하고, 시간이 렌더링될 때마다 모든 타임스탬프를 조정해줌.  
※ meta refresh tag : 주어진 시간 이후 현재 웹페이지나 프레임의 새로고침을 웹 브라우저에 지시하는 방식. 대체 url을 지정할 수 있음.  
ex) \<meta http-equiv="refresh" content="5; url=https://example.com/"> = redirect to https://example.com/ after 5 seconds
2) "new school" approach : UTC에서 로컬 타임존으로의 변환을 서버가 아니라, JavaScript를 이용해서 클라이언트 단에서 이루어지게 함.  
브라우저는 단순히 타임존 뿐만 아니라, 시스템 locale 설정에도 접근할 수 있어서 AM/PM vs 24시간 표기, DD/MM/YYYY vs MM/DD/YYYY 같은 표기 형태까지 알 수 있음. 그리고 오픈소스 라이브러리가 있음.

## Moment.js 와 Flask-Moment
- Moment.js : 날짜와 시간을 다루는 작은 오픈소스 JavaScript 라이브러리.
- Flask-Moment : moment.js 을 앱에 쉽게 통합할 수 있도록하는 Flask Extension

```shell
pip install flask-moment
```
- app/\_\_init\_\_.py 에 Flask-Moment 인스턴스를 추가해줌.
- app/templates/base.html 에 scripts block 추가.  
다른 extension이랑은 다르게, Flask-Moment는 moment.js랑 같이 동작하고, 그래서 앱의 모든 템플릿이 이 라이브러리를 포함하고 있어야함. 이 라이브러리가 항상 available한 걸 보장하기 위해서, base.html에 포함시킴.

```python
{% block scripts %}
    {{ super() }}
    {{ moment.include_moment() }}  # 라이브러리를 import하는 <script> 태그를 만들어 냄
{% endblock %}
```
- Q. super() 가 정확히 어떤 부분을 가리키는가?  
A. 부모 템플릿에 정의된 블락 내용. app/templates/base.html 에서 부모 템플릿은 bootstrap/base.html 임. bootstrap/base.html 내용을 잃어버리지 않고, moment.js 라이브러리만 추가하고 싶기 때문에, block scripts 안에 super를 써줌.

## Moment.js 사용하기
- Moment.js는 브라우저가 사용할 수 있는 moment 클래스를 만듦. 타임스탬프를 렌더링하기 위해서는 이 클래스의 객체부터 만들어야 함. ISO 8601 에 맞는 형태로 타임스탬프를 넘겨주어 생성함.   
※ ISO 8601 포맷 : {{ year }}-{{ month }}-{{ day }}T{{ hour }}:{{ minute }}:{{ second }}{{ timezone }}  
ex) t = moment('2021-06-28T21:45:23Z'). 여기서 맨 끝에 'Z'가 UTC 타임존을 나타냄
- moment 객체의 렌더링 포맷 : L, LL, LLL, LLLL, dddd, fromNow(), calendar()

```console
moment('2021-06-28T21:45:23Z').format('L')
'06/29/2021'
```
- moment.js가 삽입된 microblog 페이지에서 F12 눌러서 콘솔에 입력해보거나, https://momentjs.com/. 들어가서 확인함.
- app/templates/user.html 에서 user.last_seen 보여주는 부분 변경

```python
{{ moment(user.last_seen).format('LLL') }}
```
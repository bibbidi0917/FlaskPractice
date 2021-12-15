# 20장 : Some JavaScript Magic
- 사용자 이름에 마우스를 올리면, 그 사용자에 대한 간단한 팝업이 나오도록 함
- JavaScript 가 웹 브라우저에서 native하게 돌아가는 유일한 언어

## Server-side Support
- app/main/routes.py 에 '/user/\<username>/popup' url 매핑 추가
- app/templates/user_popup.html 파일 추가

## Bootstrap Popover 컴포넌트
- Bootstrap documentation https://getbootstrap.com 
- 대부분의 Bootstrap 컴포넌트는 HTML 마크업을 통해 정의되고, 스타일링을 위해 Bootstrap CSS 정의를 참조하고 있음. 그리고 어떤 것들은 JavaScript를 사용하는데, 초기화하거나 activate할 때 JavaScript 함수를 사용함
- Popover : https://getbootstrap.com/docs/3.3/javascript/#popovers 부가적인 정보를 담은 작은 오버레이. popover() JavaScript 함수를 호출해야 initialize 됨
- 문제점 및 해결방안
1) 페이지의 포스트마다 username link가 있음. 이 페이지가 모두 렌더링된 다음에 JavaScript로부터 이 링크들을 찾고, 이 위치에 popover를 초기화해야함 > ready function 이용
2) Bootstrap 문서의 popover 예시를 보면, popover의 content가 'data-content' 속성으로 타겟 HTML 요소에 추가됨. 그래서 hover 이벤트가 트리거되었을 때, data를 받아오는 게 아니라 이미 정의된 data-content를 보여줄 뿐임. 나는 컨텐츠를 얻기 위해 서버에 Ajax call을 보내고, 서버로부터 받은 데이터로 팝업을 보여주고 싶음 > Ajax로 컨텐츠를 받아온 다음, 동적으로 popover 요소 만들어서 HTML에 삽입
3) hover 모드를 사용할 때, 팝업은 타겟 요소 안에 마우스 포인터가 있을 때만 보임. 마우스를 움직이면 팝업은 사라짐. 그런데 사용자가 popup 안으로 마우스를 옮겼을 때도 팝업이 사라짐 > hover 행위를 사용자 이름 뿐만 아니라 팝업 전체를 포함하는 것으로 확장하기 위해, 이벤트의 상속을 이용함

## 페이지가 로드될 때 함수 실행하기
- **$(...)** : 각 페이지가 로드되자마자 JavaScript 코드를 실행. jQuery JavaScript 라이브러리는 Bootstrap의 dependency로 로드되어있음
- 이 예제에서는 페이지 안의 사용자 이름 링크를 찾고, 이것을 Bootstrap의 popover 컴포넌트로 설정하고자 함
- app/templates/base.html 의 \<script> 부분에 ready function 추가

## Selector로 DOM element 찾기
- 페이지 안에 여러 요소들에게 부여된 class 속성으로도 요소를 식별할 수 있음. 예를 들어 모든 사용자 링크를 class="user_popup" 으로 둔다면, 이 링크들의 리스트를 $('.user_popup') 으로 얻을 수 있음

## Popover 와 DOM
- DOM 안의 사용자 이름 링크의 형제로 Bootstrap이 popover 컴포넌트를 만들도록 함
- hover 이벤트를 popover 전체로 확장시키기 위해서, popover를 타겟 요소(\<span class="user_popup">)의 자식으로 만들어 hover 이벤트가 상속되도록 함 > container 옵션에서 부모 요소를 전달해주면 됨
- popover를 타겟 요소의 자식으로 만들어주면 되는데, 문제는 popover를 \<a>의 자식으로 만들어주면 링크 behavior까지 popover가 얻게 됨  
따라서 popover가 \<a> 안에 있는 것을 막기 위해서, 아래와 같이 바꿈

```html
        <span class="user_popup">
            <a href="...">
                username
            </a>
            <div> ... popover elements here ... </div>
        </span>
```

- \<div> 와 \<span> 요소는 보이지 않기 때문에, DOM 을 조직화, 구조화하는 데에 도움이 됨
1) \<div> : block element=HTML 문서에서 단락처럼 표현
2) \<span> : inline element=단어처럼 한 라인으로 보임  
여기서는 \<a> 가 inline element 이기 때문에, \<span> 으로 감싼 것임

- app/templates/_post.html 을 아래와 같이 변경 : 나중에 span 요소에서 popover() 초기화 함수를 부르면, Bootstrap framework 가 동적으로 팝업 컴포넌트를 삽입하도록 할 것임
```html
    {% set user_link %}
        <span class="user_popup">
            <a href="{{ url_for('main.user', username=post.author.username) }}">
                {{ post.author.username }}
            </a>
        </span>
    {% endset %}
```

## hover 이벤트
- "manual" 모드로 hover 이벤트를 등록 : JavaScript 콜을 만들어서 수동으로 popover가 표시되고 제거되게 함
- **element.hover(handlerIn, handlerOut)**
- **timer = setTimeout(함수, 밀리세컨드)** 도입 : 마우스가 요소에 1초 정도는 머물러야 popover가 뜨도록 함. 요소에서 벗어나면 타이머 다시 리셋함

## Ajax 요청
- ' /user/\<username>/popup' 으로 ajax를 보내야하는데, username을 어떻게 알 것인가?  
elem.first().text().trim() : event.currentTarget 인 user_popup 클래스 span 을 'elem' 으로 받아왔고, 그것의 첫번째 자식인 \<a> 태그를 가져오고, 그것의 text를 뽑아낸 게 username. 주변의 공백을 없애기 위해서 trim()
- javascript에서는 Flask 의 url_for을 못 쓰기 때문에, Ajax 보내는 url은 이어붙여서 만들어줄 수 밖에 없음

## Popover 생성 및 없애기
- 받아온 data로 팝업 생성
```javascript
    function(data) {
        xhr = null;
        elem.popover({
            trigger: 'manual',
            html: true,
            animation: false,  //fade animation
            container: elem,  //<span class="user_popup">을 부모로 하여 hover 이벤트를 상속받음
            content: data
        }).popover('show');
        flask_moment_render_all();
        // last_seen 이 popover에 표시되면서, 새로운 Flask-Moment 요소가 Ajax에 의해 추가되었기 때문에, 이 함수를 불러줌
    }
```


## 이 챕터에서 추가/수정된 파일
- app/templates/user_popup.html 추가
- app/templates/_post.html 수정
- app/templates/base.html ready function 추가
- app/main/routes.py '/user/\<username>/popup' url 매핑 추가
# 11장 : Facelift

## CSS Frameworks
- raw 레벨의 HTML,CSS를 사용하기 힘들면, CSS 프레임워크를 사용하면 됨. 이 프레임워크들은 HTML이나 CSS로는 하기 힘든 것도 JavaScript를 이용해서 할 수 있도록 함

## Bootstrap 소개
- 가장 유명한 CSS 프레임워크가 트위터에서 만든 Bootstrap임.
- 데스크탑, 태플릿, 폰 화면 사이즈에 맞춰서 핸들링 가능, 레이아웃 커스터마이즈 가능, 네비게이션 바, 버튼 등 잘 디자인된 요소 사용 가능.
- bootstrap.min.css 를 base 템플릿에 import하면 됨. 파일을 다운로드 받아서 프로젝트에 추가하거나, CDN에서 직접 import 할 수 있음.
- flask-bootstrap extension : Bootstrap version 3
```shell
pip install flask-bootstrap
```

## Bootstrap 사용하기
- Flask-Bootstrap도 다른 extension들과 마찬가지로 \_\_init\_\_.py 에서 초기화되어야 함. 인스턴스를 만들고나면, {% extends 'bootstrap/base.html' %} 로 앱 템플릿에서 참조가 가능함.
- 세 레벨로 템플릿을 구성함.
1) bootstrap/base.html : Bootstrap 프레임워크 파일들을 포함한 기본 구조
2) base.html
    1. title
    2. navbar
    3. content : flash 메시지를 표시하는 부분과, app_content block
3) base.html을 extends한 다른 템플릿들. (content block에서 app_content block으로 모두 변경함)

## Bootstrap Forms 렌더링하기
```python
{% import 'bootstrap/wtf.html' as wtf %}
...
{{ wtf.quick_form(form) }}
```
완성된 폼이 들어가고, validation error 보여주고, 스타일도 달라짐.
- app/templates 밑의 form이 포함된 edit_profile.html, index.html, login.html, register.html, reset_password_request.html, reset_password.html 에 적용

## 블로그 post 렌더링하기
- app/templates/_post.html 수정  
table 태그에 클래스 입히고, 이미지 클릭해도 해당 사용자 프로필로 이동할 수 있도록 함

## Pagination 링크 렌더링하기
- 이전 페이지나 다음 페이지가 없을 때 링크 자체를 없애는 것이 아니라, disabled 시킴. 
- app/templates/index.html, user.html 에 적용

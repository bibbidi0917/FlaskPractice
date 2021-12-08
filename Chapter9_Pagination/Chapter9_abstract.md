# 9장 : Pagination
- 사용자들로부터 post를 입력받기
- 홈과 프로필 페이지에서 페이징된 리스트로 포스트 보여주기

## 블로그 post 올리기
- app/forms.py 에 PostForm 클래스 생성
- app/templates/index.html 에 PostForm 보여주기
- app/routes.py 의 index 함수에서 리턴할 때 form 넘겨주고, form 데이터 처리하는  로직 삽입. method에 post 추가.
```python
post = Post(body=form.post.data, author=current_user)
```
User 클래스에 posts의 backref로 지정되어있던 'author' 속성을 이용해서, user 객체 자체를 지정할 수 있음
- Q. 왜 routes.py의 index()함수에서 폼데이터를 처리하고 그대로 밑으로 흘려보내지 않고 redirect(url_for('index')) 하는가?  
A. **Post/Redirect/Get 패턴** : web form 제출에 의해 생성된 POST 요청은 redirect로 응답하는 것이 스탠다드임.  
웹 브라우저에서 화면을 리프레시하면, 바로 이전의 요청을 다시 보냄. 그런데 사용자가 폼을 제출하고 나서 화면을 리프레시하면, 이전의 POST 요청이 동일하게 들어가고, db에 다시 post를 저장하는 문제 등이 발생함.  
따라서 POST로 온 요청을 처리한 후에 redirect해서 get 요청으로 바꿔주면, 폼 제출 후에 사용자가 화면 리프레시 해도 get 요청만 계속 들어와서 문제 발생 안 함.

## 블로그 post 보여주기
- app/routes.py 의 index 함수에서 posts를 fake 객체가 아닌 실제 db의 post들로 바꿔줌. .all()이 쿼리 실행을 트리거하고, 결과를 리스트 형태로 바꿔줌. 
```python
posts = current_user.followed_posts().all()
```

## Follow할 사용자 찾는 것을 쉽게 만들기
- 모든 사용자의 post들을 볼 수 있는 explore 페이지를 만듦.
- app/routes.py 에 '/explore' 매핑 추가
- app/templates/index.html 에 /explore로 넘어왔을 경우, 포스트 입력 폼은 보여주지 않고 포스트 목록만 보여주도록 변경
- app/templates/base.html 에 explore 메뉴 추가
- app/templates/_post.html 에 user이름 누르면 그 사람 프로필 화면으로 가도록 변경
- app/templates/index.html 에서도 _post.html을 사용하도록 변경

## 블로그 post의 페이지네이션
- **paginate(페이지 번호, 페이지 당 아이템 수, 에러플래그)** : 리턴값이 Pagination object이기 때문에, 해당 object의 items 속성에 담겨있는 리스트를 꺼내주어야 함.  

범위 밖의 페이지가 요청되었을 때  
1) 에러플래그=True 이면, 404 에러가 클라이언트에게 자동으로 리턴됨. 
2) 에러플래그=False 이면, 빈 리스트가 리턴됨

```python
user.followed_posts().paginate(1, 20, False).items
```

- config.py 에 POSTS_PER_PAGE 추가 : 페이지 당 아이템 수를 어플리케이션 공통 설정값으로 추가해줌
- app/routes.py의 index(), explore()에 page 로직 추가. 페이지 번호를 URL에 'page'로 붙임. 없으면 자동으로 1페이지.  
**request.args.get('page', 디폴트 값, type=)** : query string에 있는 argument를 가져옴

## Page Navigation
- Flask-SQLAlchemy의 Pagination 클래스의 다른 속성들  
1) has_next
2) has_prev
3) next_num
4) prev_num
- app/routes.py의 index(), explore() 함수에서 다음 페이지 url, 이전 페이지 url 반환
```python
next_url = url_for('explore', page=posts.next_num) \  # argument 추가 가능
        if posts.has_next else None
```
**url_for('url', \*\*arguments)** : 뒤의 argument들이 url에 직접 명시되어있으면 그 자리에 넣어주고, 없으면 뒤에 쿼리 argument로 넣어줌)  
ex) url_for('user', username=user.username, page=posts.next_num) >> /user/jihyun?page=2
- app/templates/index.html 에 Newer posts, Older posts 링크 추가 (/index, /explore가 동일 화면 사용)

## 사용자 프로필 페이지의 페이지네이션
- 사용자 프로필 페이지에는 자신이 작성한 글만 나옴
- app/routes.py의 user() 변경
- app/templates/user.html 에 Newer posts, Older posts 링크 추가
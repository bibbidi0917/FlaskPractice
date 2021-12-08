# 8장 : Follwers

## Database Relationships
- followed와 follower 관계를 어떻게 표현할 것인가?
1) One-to-Many : Many 쪽에서 Foreign Key를 가지고 있음  
ex) user는 posts를 가지고 있고, 포스트는 하나의 user를 가지고 있음. post.user_id 필드가 해당 post의 author에 대한 직접 접근을 제공함. 반대로는 한 user가 쓴 모든 post를 가져오는 데에 용이함.

2) Many-to-Many : 두 엔티티가 association table로 연결되고, 해당 table이 두 엔티티의 Foreign Key를 가지고 있음  
ex) 학생과 선생님. 한 명의 학생은 여러 선생님을 가지고 있고, 한 명의 선생님은 여러 학생을 가지고 있음. 1대 다 관계가 양방향으로 중첩된 느낌. 

3) Many-to-One : 1대 다 관계와 비슷하고, 다 관점에서 본다는 것만 다름
4) One-to-One : 1대 다 관계 중 특별한 케이스. many 쪽에서 1개 초과의 링크를 가지지 않도록 db에 제약조건을 둠. 흔하지 않은 경우임.

## Follower들 표현하기
- 자기참조 다 대 다 관계가 적절함.  
한 명의 사용자가 여러 follower들을 가지고 있고, 한 명이 여러 사람을 follow함. 다만, 학생과 선생님처럼 2개 엔티티가 아니라, 사용자와 다른 사용자이므로 1개 엔티티임=자기 참조 관계(self-referential)
- association table로 'followers' 테이블을 생성하고, 이 테이블의 foreign key 2개는 모두 user 엔티티를 참조함. 

## Database Model 표현
- app/models.py 에 'followers' association table 추가  
외래키말고 다른 데이터가 없는 보조 테이블이므로, model로 선언하지 않고 직접 선언함.
- app/models.py 의 User 클래스에 followers 테이블와의 관계 명시
```python
    # db.relationship : 왼쪽 엔티티에서는 이 관계를 followed 로 부름.
    followed = db.relationship(
        'User',  # 오른쪽 엔티티
        secondary=followers,  # secondary : association 테이블
        
        # primaryjoin : 왼쪽 엔티티를 asso 테이블과 링크하는 조건
        primaryjoin=(followers.c.follwer_id == id),
        
        # secondaryjoin : 오른쪽 엔티티를 asso 테이블과 링크하는 조건
        secondaryjoin=(followers.c.follwed_id == id),
        
        # backref : 오른쪽 엔티티에서 이 속성조회할 때,followers로 부름.
        # lazy : 쿼리의 실행모드. dynamic = 요청 전까지 쿼리 돌지 않음. 
        backref=db.backref('followers', lazy='dynamic'),
        # 오른쪽 엔티티에 적용
        
        lazy='dynamic') # 왼쪽 엔티티에 적용
```
※ 왼쪽 유저를 follower user, 오른쪽을 followed user라고 생각함.

## "follows" 추가하고 삭제하기
- 추가 : user1.followed.append(user2) : user1이 user2를 followed.
- 삭제 : user1.followed.remove(user2)
- app/models.py의 user 클래스에 follow, unfollow, is_following 함수 추가

## Followed User들의 posts 얻기
- 로그인한 유저가 followed한 유저들의 모든 post들을 index.html에 띄우고 싶음.
1) user.followed.all() 한 뒤에, 그 유저들의 모든 post들을 조회하는 방식  
    1. 사용자가 수천명을 팔로잉했다면?  
    수천번 조회해서 post 목록 가져오고, 그것 합쳐서 메모리에서 sorting해야 함.
    2. 페이징이 되어있다하더라도, 위 방식말고는 없음


2) 관계형 db에서는 쿼리 한 줄로 해결 가능함.
```python
 Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())
```
- app/models.py 의 User 클래스에 followed_posts 함수 추가  
쿼리가 Post 클래스에서 나가고 있기 때문에, 결과는 임시 테이블에 있는 포스트들임. 조인 과정에서 추가된 컬럼들은 나오지 않음.

### Joins
- **join(테이블, (조건))** : 조인 후 임시테이블을 만듦. 
```python
Post.query.join(followers, (followers.c.followed_id == Post.user_id))
```
post를 followers랑 조인하는데, 조건이 위와 같음. 팔로워가 있는 사람들의 포스트 목록이 결과로 나옴.

### Filters
```python
filter(followers.c.follower_id == self.id)
```
내가 팔로워인 사람 것만 필터링.

### Sorting
```python
order_by(Post.timestamp.desc())
```

## 내 포스트와 Followed 포스트 합치기
1) 모든 유저들이 자기 자신을 followed하게 함.  
위의 쿼리를 그대로 사용할 수 있으나, 팔로워 수 보여줄 때 매번 조정해야함

2) 두번째 쿼리로 자신의 post를 모두 조회한 뒤, 첫번째 쿼리 결과와 union함. 이걸 선택함.
```python
followed.union(own).order_by(Post.timestamp.desc())
```

## User 모델의 단위 테스트
- tests.py 파일 추가. 기능 변경 시 아래와 같이 돌려보면서 기존 기능에 이상없는지 확인 가능.
```python
python tests.py
```
1) assertTrue()
2) assertFalse()
3) assertEqual(a,b)
- setUp과 tearDown은 각 테스트 전과 후에 매번 실행됨.
- db.session.add_all([u1, u2]) : 리스트로 세션에 추가 가능

## 어플리케이션에 Followers 기능 통합하기
- CSRF 공격을 막기 위해 follow, unfollow 요청을 POST로 보내는 것이 바람직함. form에 CSRF 토큰을 같이 보냄.
- 사용자가 별도의 데이터를 submit하지 않고, "Follow"나 "Unfollow" 버튼을 클릭할 때 CSRF 토큰(Flask-WTF 에서 자동으로 추가된 히든 태그. form.hidden_tag())과 함께 요청이 가야 함. 사용자가 입력하는 데이터는 없기 때문에, EmptyForm을 만듦.
- app/forms.py에 EmptyForm 클래스 추가
- app/routes.py에 '/follow/\<username\>', '/unfollow/\<username\>' 매핑 추가
- app/routes.py의 user()에 form 추가. follow, unfollow 버튼을 프로필 화면에 보이게 하기 위함. 두 액션이 exclusive하기 때문에 form을 하나만 보냄. 
- app/templates/user.html에 Emptyform 나타냄. 동일 폼을 버튼 이름만 다르게 함.
```python
{{ form.submit(value='Follow') }}
```
버튼 라벨 지정
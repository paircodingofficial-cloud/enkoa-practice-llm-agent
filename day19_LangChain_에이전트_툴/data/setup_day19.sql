-- day19 Text-to-SQL 실습 테이블 리셋+생성+적재 (교안·과제의 준비 셀이 실행)
-- 17일차에서 배운 sqlite 를 그대로 씁니다 — 접속 정보가 필요 없어 바로 시작할 수 있습니다.
-- 17일차 테이블(book·customer·orders 등)과 겹치지 않게 접두(hd_·bs_)를 붙였습니다.
-- 출처: 전부 수업용 가상 데이터.

-- 이 단원이 만드는 테이블만 정리합니다.
drop table if exists hd_order;
drop table if exists hd_item;
drop table if exists bs_order;
drop table if exists bs_book;
drop table if exists bs_customer;

-- ── 교안: 사내 비품 주문 ─────────────────────────────────────────────
create table hd_item (
    item_id    text primary key,
    item_name  text not null,
    category   text not null,
    unit_price int  not null,
    stock      int  not null
) strict;
create table hd_order (
    order_id   int  primary key,
    item_id    text not null references hd_item(item_id),
    quantity   int  not null,
    dept       text not null,
    order_date text not null
) strict;

insert into hd_item (item_id, item_name, category, unit_price, stock) values
 ('i1', '무선 마우스',   '주변기기', 18000, 40),
 ('i2', '기계식 키보드', '주변기기', 65000, 15),
 ('i3', 'A4 복사용지',   '사무용품',  4500, 200),
 ('i4', '모니터 받침대', '가구',     23000, 25),
 ('i5', '보안 USB',      '저장장치', 32000, 10),
 ('i6', '노트북 거치대', '가구',     19000, 30),
 ('i7', '헤드셋',        '주변기기', 47000, 12);

insert into hd_order (order_id, item_id, quantity, dept, order_date) values
 (1, 'i1', 5,  '개발팀',   '2025-05-02'),
 (2, 'i3', 20, '총무팀',   '2025-05-03'),
 (3, 'i2', 2,  '개발팀',   '2025-05-05'),
 (4, 'i5', 3,  '보안팀',   '2025-05-06'),
 (5, 'i1', 4,  '디자인팀', '2025-05-08'),
 (6, 'i4', 6,  '개발팀',   '2025-05-10'),
 (7, 'i7', 2,  '고객지원팀','2025-05-11'),
 (8, 'i3', 15, '총무팀',   '2025-05-12'),
 (9, 'i6', 8,  '개발팀',   '2025-05-14'),
 (10,'i2', 1,  '디자인팀', '2025-05-15');

-- ── 과제: 온라인 서점 주문 ───────────────────────────────────────────
create table bs_customer (
    customer_id text primary key,
    name        text not null,
    grade       text not null,
    city        text not null
) strict;
create table bs_book (
    book_id text primary key,
    title   text not null,
    author  text not null,
    genre   text not null,
    price   int  not null,
    stock   int  not null
) strict;
create table bs_order (
    order_id    int  primary key,
    customer_id text not null references bs_customer(customer_id),
    book_id     text not null references bs_book(book_id),
    quantity    int  not null,
    order_date  text not null
) strict;

insert into bs_customer (customer_id, name, grade, city) values
 ('c1', '김서연', '최우수', '서울'),
 ('c2', '이준호', '우수',   '부산'),
 ('c3', '박지민', '일반',   '서울'),
 ('c4', '정하늘', '우수',   '대구'),
 ('c5', '최민재', '일반',   '인천');

insert into bs_book (book_id, title, author, genre, price, stock) values
 ('k1', '파이썬 입문',       '한지원', '프로그래밍', 22000, 50),
 ('k2', '데이터 분석 기초',  '오세훈', '데이터',     28000, 30),
 ('k3', '깊은 밤의 서점',    '문가영', '소설',       15000, 80),
 ('k4', '통계학 첫걸음',     '오세훈', '데이터',     26000, 20),
 ('k5', '바다의 기억',       '문가영', '소설',       14000, 60),
 ('k6', '머신러닝 실전',     '한지원', '프로그래밍', 33000, 25);

insert into bs_order (order_id, customer_id, book_id, quantity, order_date) values
 (1, 'c1', 'k1', 1, '2025-06-01'),
 (2, 'c1', 'k2', 2, '2025-06-02'),
 (3, 'c2', 'k3', 3, '2025-06-03'),
 (4, 'c3', 'k1', 1, '2025-06-05'),
 (5, 'c4', 'k4', 2, '2025-06-06'),
 (6, 'c2', 'k6', 1, '2025-06-08'),
 (7, 'c5', 'k5', 4, '2025-06-09'),
 (8, 'c1', 'k6', 1, '2025-06-10'),
 (9, 'c4', 'k2', 1, '2025-06-11'),
 (10,'c3', 'k3', 2, '2025-06-12');

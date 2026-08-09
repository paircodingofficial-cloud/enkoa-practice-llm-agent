-- 교안_02 쇼핑몰 실습 DB 리셋 스크립트 (sqlite)
-- 교안_01 에서 손으로 만든 것과 같은 구조를, 데이터까지 채운 상태로 한 번에 준비합니다.
-- 표기 관례: SQL 키워드는 대문자, 표와 열 이름, 타입, 값은 소문자 (교안_01 2절).
-- 출처: 수업용 가상 데이터

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id         integer PRIMARY KEY AUTOINCREMENT,
    name       text NOT NULL,
    email      text NOT NULL UNIQUE,
    city       text,
    created_at text NOT NULL DEFAULT (date('now'))
) STRICT;

CREATE TABLE products (
    id         integer PRIMARY KEY AUTOINCREMENT,
    name       text NOT NULL UNIQUE,
    list_price int  NOT NULL CHECK (list_price >= 0),
    category   text NOT NULL
) STRICT;

CREATE TABLE orders (
    id          integer PRIMARY KEY AUTOINCREMENT,
    customer_id int  NOT NULL REFERENCES customers(id),
    product     text NOT NULL,
    amount      int  NOT NULL CHECK (amount >= 0),
    ordered_at  text NOT NULL
) STRICT;

CREATE TABLE reviews (
    id          integer PRIMARY KEY AUTOINCREMENT,
    customer_id int  NOT NULL REFERENCES customers(id),
    product     text NOT NULL,
    rating      int  NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     text
) STRICT;

INSERT INTO customers (id, name, email, city, created_at) VALUES
    (1, '김민수', 'minsu@shop.com',  '서울', '2026-01-12'),
    (2, '이지은', 'jieun@shop.com',  '부산', '2026-01-20'),
    (3, '박하늘', 'haneul@shop.com', '대구', '2026-02-03'),
    (4, '최유진', 'yujin@shop.com',  NULL,   '2026-02-14'),
    (5, '정하윤', 'hayoon@shop.com', '서울', '2026-02-27');

INSERT INTO products (id, name, list_price, category) VALUES
    (1, '노트북', 1490000, '컴퓨터'),
    (2, '마우스',   35000, '주변기기'),
    (3, '키보드',   99000, '주변기기'),
    (4, '모니터',  350000, '컴퓨터'),
    (5, '웹캠',     79000, '주변기기'),
    (6, '헤드셋',  129000, '주변기기');

INSERT INTO orders (id, customer_id, product, amount, ordered_at) VALUES
    (1, 1, '노트북', 1290000, '2026-03-02'),
    (2, 1, '마우스',   29000, '2026-03-05'),
    (3, 2, '키보드',   89000, '2026-03-07'),
    (4, 2, '모니터',  320000, '2026-03-11'),
    (5, 3, '마우스',   29000, '2026-03-15'),
    (6, 1, '키보드',   89000, '2026-03-18'),
    (7, 3, '웹캠',     65000, '2026-04-02'),
    (8, 2, '노트북', 1290000, '2026-04-09');

INSERT INTO reviews (id, customer_id, product, rating, comment) VALUES
    (1, 1, '노트북', 5, '화면이 밝고 가벼워요'),
    (2, 1, '마우스', 4, '손에 잘 맞습니다'),
    (3, 2, '키보드', 5, '타건감이 좋아요'),
    (4, 2, '모니터', 3, '받침대가 흔들려요'),
    (5, 3, '마우스', 4, '무난합니다'),
    (6, 1, '키보드', 2, '소리가 너무 큽니다'),
    (7, 3, '웹캠',   4, NULL),
    (8, 2, '노트북', 5, '배송이 빨랐어요');

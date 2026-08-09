-- day17 실습 준비 SQL — Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run 하세요.
-- 언제 몇 번을 다시 실행해도 안전합니다(표를 지우고 다시 만듭니다).
-- 출처: 연구비 FAQ 는 한국산업기술기획평가원 '연구비 집행 자주묻는질문'
--       (공공데이터포털, 공공누리 제1유형) 정제본.

-- 1) 확장 켜기 — vector 타입과 거리 연산자(<=>)가 생깁니다.
CREATE EXTENSION IF NOT EXISTS vector;

-- 2) 실습 표 정리 (자식 -> 부모 순서)
DROP TABLE IF EXISTS faq_docs CASCADE;
DROP TABLE IF EXISTS faq_category CASCADE;

-- 3) 분류·담당팀 표 (JOIN 대상)
CREATE TABLE faq_category (
    category  varchar(20) PRIMARY KEY,
    team_name varchar(20) NOT NULL,
    phone     varchar(20)
);

INSERT INTO faq_category (category, team_name, phone) VALUES
    ('RCMS일반',   '고객지원팀', '042-712-9000'),
    ('환경설정',   '고객지원팀', '042-712-9000'),
    ('협약정보',   '협약관리팀', '042-712-9100'),
    ('사용등록',   '집행지원팀', '042-712-9200'),
    ('연구비집행', '집행지원팀', '042-712-9200'),
    ('연구비취소', '집행지원팀', '042-712-9200'),
    ('연구비정산', '정산관리팀', '042-712-9300');

-- 4) FAQ 본문 + 임베딩 표 (768차원 = jhgan/ko-sroberta-multitask)
CREATE TABLE faq_docs (
    faq_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category  varchar(20) NOT NULL REFERENCES faq_category(category),
    question  text NOT NULL,
    answer    text NOT NULL,
    embedding vector(768)
);

-- 5) 벡터 인덱스 — 코사인 거리(<=>)용 HNSW
CREATE INDEX faq_docs_embedding_idx
    ON faq_docs USING hnsw (embedding vector_cosine_ops);

-- 6) 의미 검색 함수 — 노트북에서 supabase.rpc("match_faq", {...}) 로 부릅니다.
--    filter_category 가 NULL 이면 전체에서, 값이 있으면 그 분류 안에서만 찾습니다.
CREATE OR REPLACE FUNCTION match_faq (
    query_embedding vector(768),
    match_count     int  DEFAULT 3,
    filter_category text DEFAULT NULL
)
RETURNS TABLE (
    faq_id     bigint,
    category   varchar(20),
    question   text,
    answer     text,
    team_name  varchar(20),
    phone      varchar(20),
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT d.faq_id,
           d.category,
           d.question,
           d.answer,
           c.team_name,
           c.phone,
           1 - (d.embedding <=> query_embedding) AS similarity
    FROM faq_docs d
    JOIN faq_category c ON c.category = d.category
    WHERE filter_category IS NULL OR d.category = filter_category
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
$$;

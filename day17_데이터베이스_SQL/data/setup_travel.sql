-- day17 과제 LV3 준비 SQL — Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run 하세요.
-- 언제 몇 번을 다시 실행해도 안전합니다(표를 지우고 다시 만듭니다).
-- 데이터: 여행지 100곳은 수업용 가상 데이터입니다(15일차 실습자료에서 가져왔습니다).

-- 1) 확장 켜기 — vector 타입과 거리 연산자(<=>)가 생깁니다.
CREATE EXTENSION IF NOT EXISTS vector;

-- 2) 실습 표 정리 (자식 -> 부모 순서)
DROP TABLE IF EXISTS travel_docs CASCADE;
DROP TABLE IF EXISTS travel_region CASCADE;

-- 3) 지역과 권역 표 (JOIN 대상) — 지역 15종이 어느 행정 권역에 속하는지
CREATE TABLE travel_region (
    region varchar(10) PRIMARY KEY,
    area   varchar(10) NOT NULL
);

INSERT INTO travel_region (region, area) VALUES
    ('강원', '관동'),
    ('경기', '수도권'),
    ('경남', '영남'),
    ('경북', '영남'),
    ('광주', '호남'),
    ('대구', '영남'),
    ('대전', '충청'),
    ('부산', '영남'),
    ('서울', '수도권'),
    ('울산', '영남'),
    ('인천', '수도권'),
    ('전남', '호남'),
    ('전북', '호남'),
    ('제주', '제주'),
    ('충남', '충청');

-- 4) 여행지 본문 + 임베딩 표 (768차원 = jhgan/ko-sroberta-multitask)
--    CSV 의 type 열은 이 표에서 spot_type 이라는 이름으로 들어갑니다.
CREATE TABLE travel_docs (
    spot_id      varchar(10) PRIMARY KEY,
    name         varchar(40) NOT NULL,
    region       varchar(10) NOT NULL REFERENCES travel_region(region),
    spot_type    varchar(10) NOT NULL,
    entrance_fee int NOT NULL,
    description  text NOT NULL,
    embedding    vector(768)
);

-- 5) 벡터 인덱스 — 코사인 거리(<=>)용 HNSW
CREATE INDEX travel_docs_embedding_idx
    ON travel_docs USING hnsw (embedding vector_cosine_ops);

-- 6) 의미 검색 함수 — 노트북에서 supabase.rpc("match_spot", {...}) 로 부릅니다.
--    filter_region 과 filter_type 은 NULL 이면 그 조건을 걸지 않습니다.
--    min_similarity 는 그 값보다 가까운 것만 남깁니다(기본 0 이면 전부 통과).
--    travel_region 을 JOIN 해서 권역(area)까지 함께 돌려줍니다.
CREATE OR REPLACE FUNCTION match_spot (
    query_embedding vector(768),
    match_count     int   DEFAULT 3,
    filter_region   text  DEFAULT NULL,
    filter_type     text  DEFAULT NULL,
    min_similarity  float DEFAULT 0
)
RETURNS TABLE (
    spot_id      varchar(10),
    name         varchar(40),
    region       varchar(10),
    area         varchar(10),
    spot_type    varchar(10),
    entrance_fee int,
    description  text,
    similarity   float
)
LANGUAGE sql STABLE
AS $$
    SELECT d.spot_id,
           d.name,
           d.region,
           g.area,
           d.spot_type,
           d.entrance_fee,
           d.description,
           1 - (d.embedding <=> query_embedding) AS similarity
    FROM travel_docs d
    JOIN travel_region g ON g.region = d.region
    WHERE (filter_region IS NULL OR d.region = filter_region)
      AND (filter_type IS NULL OR d.spot_type = filter_type)
      AND 1 - (d.embedding <=> query_embedding) >= min_similarity
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- day20 종합 에이전트 교안 — 사내 AI 서비스 도입 대장 리셋+생성+적재
-- 17일차에서 배운 sqlite 를 그대로 씁니다 (접속 정보가 필요 없습니다).
-- 다른 단원 표와 겹치지 않게 ai_ 접두를 붙였습니다.
-- 출처: 전부 수업용 가상 데이터입니다 (실제 회사의 도입 현황이 아닙니다).

drop table if exists ai_request;
drop table if exists ai_service;

-- 회사가 도입했거나 검토 중인 AI 서비스 목록
create table ai_service (
    service_id        text primary key,
    service_name      text not null,
    vendor            text not null,
    category          text not null,   -- 문서요약/번역/코딩보조/고객상담/이미지생성
    personal_data     text not null,   -- 예/아니오 : 개인정보를 입력하게 되는가
    overseas_transfer text not null,   -- 예/아니오 : 데이터가 국외 서버로 나가는가
    monthly_cost      int  not null,   -- 1인당 월 이용료(원)
    review_status     text not null,   -- 승인/검토중/보류
    check (personal_data in ('예', '아니오')),
    check (overseas_transfer in ('예', '아니오'))
) strict;

-- 부서가 올린 사용 신청 내역
create table ai_request (
    request_id   int  primary key,
    service_id   text not null references ai_service(service_id),
    dept         text not null,
    seats        int  not null,   -- 신청 좌석 수
    request_date text not null,   -- 접수일 YYYY-MM-DD
    status       text not null,   -- 접수/검토중/승인/반려/보류
    check (seats > 0)
) strict;

insert into ai_service
 (service_id, service_name, vendor, category, personal_data, overseas_transfer,
  monthly_cost, review_status) values
 ('s1', '문서요약 코파일럿', '해외 A사',   '문서요약',   '예',   '예',   28000, '검토중'),
 ('s2', '사내 번역기',       '국내 B사',   '번역',       '아니오', '아니오', 9000,  '승인'),
 ('s3', '코딩 보조 도구',    '해외 C사',   '코딩보조',   '아니오', '예',   19000, '승인'),
 ('s4', '고객상담 챗봇',     '국내 D사',   '고객상담',   '예',   '아니오', 42000, '검토중'),
 ('s5', '회의록 자동정리',   '국내 B사',   '문서요약',   '예',   '아니오', 15000, '승인'),
 ('s6', '이미지 생성 도구',  '해외 E사',   '이미지생성', '아니오', '예',   23000, '보류'),
 ('s7', '채용서류 분류기',   '국내 F사',   '문서요약',   '예',   '아니오', 31000, '보류');

insert into ai_request
 (request_id, service_id, dept, seats, request_date, status) values
 (1,  's1', '개발팀',     12, '2026-05-08', '검토중'),
 (2,  's2', '해외영업팀', 20, '2026-05-11', '승인'),
 (3,  's3', '개발팀',     18, '2026-05-12', '승인'),
 (4,  's4', '고객지원팀', 25, '2026-05-14', '검토중'),
 (5,  's5', '경영지원팀',  8, '2026-05-15', '승인'),
 (6,  's1', '마케팅팀',    6, '2026-05-18', '반려'),
 (7,  's6', '마케팅팀',    4, '2026-05-19', '보류'),
 (8,  's7', '인사팀',      5, '2026-05-20', '검토중'),
 (9,  's2', '개발팀',      9, '2026-05-21', '승인'),
 (10, 's5', '고객지원팀',  7, '2026-05-22', '접수'),
 (11, 's3', '데이터팀',   11, '2026-05-26', '승인'),
 (12, 's4', '고객지원팀',  3, '2026-05-28', '접수');

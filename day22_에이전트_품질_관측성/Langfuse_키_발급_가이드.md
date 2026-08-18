# Langfuse API 키 발급 가이드

22일차 교안_03(관측성)은 **실제로 대시보드에 기록이 쌓이는 것을 보면서** 진행합니다. 그래서 본인 Langfuse 키가 필요합니다. 가입부터 `.env` 채우기까지 **5분** 정도 걸리고 **신용카드는 필요 없습니다**.

받아야 할 값은 세 개입니다.

| .env 항목 | 무엇인가 | 생김새 |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY` | 어느 프로젝트로 보낼지 가리키는 공개 키 | `pk-lf-` 로 시작 |
| `LANGFUSE_SECRET_KEY` | 그 프로젝트에 쓸 권한을 증명하는 비밀 키 | `sk-lf-` 로 시작 |
| `LANGFUSE_BASE_URL` | 기록을 보낼 서버 주소 | `https://cloud.langfuse.com` |

## 1. 가입하기

**[https://cloud.langfuse.com](https://cloud.langfuse.com)** 에서 가입합니다. 이 사이트에서 프로젝트를 만들고, 키를 발급받고, 나중에 기록도 여기서 봅니다. `langfuse.com` 은 제품 소개 페이지라 로그인이 안 되니 **cloud.** 가 붙은 주소로 들어가세요.

1) [https://cloud.langfuse.com](https://cloud.langfuse.com) 에 접속해 **Sign Up** 을 누릅니다.
2) 구글 또는 깃허브 계정으로 바로 가입하거나, 이메일과 비밀번호로 가입합니다.
3) 기본이 무료 **Hobby** 플랜입니다. 결제 수단을 넣는 단계가 없습니다. 무료 한도는 **월 5만 건**이라 이 수업 분량에는 충분합니다.

Langfuse 클라우드는 지역이 나뉘어 있고, **가입한 지역의 주소가 곧 `LANGFUSE_BASE_URL`** 입니다. 수업은 기본값인 EU 를 씁니다.

| 지역 | 가입·대시보드 주소 = `LANGFUSE_BASE_URL` |
|---|---|
| EU (수업 기본) | `https://cloud.langfuse.com` |
| US | `https://us.cloud.langfuse.com` |
| 일본 | `https://jp.cloud.langfuse.com` |

Langfuse 는 오픈소스라 회사 서버에 직접 설치해 쓸 수도 있습니다. 그 경우 `LANGFUSE_BASE_URL` 은 사내 주소(예: `http://localhost:3000`)가 됩니다. 수업에서는 설치 없이 클라우드 무료 플랜을 씁니다.

## 2. 조직과 프로젝트 만들기

가입 직후 안내에 따라 만들면 됩니다. 이미 지나갔다면 화면 왼쪽 위 조직 이름을 눌러 다시 만들 수 있습니다.

1) **New Organization**: 이름은 아무거나 괜찮습니다(예: `my-org`).
2) **New Project**: 이름을 정합니다(예: `day22-observability`). 키는 **프로젝트마다** 따로 발급됩니다.

> 수업에서는 **각자 본인 프로젝트를 만드는 것**을 권합니다. 남이 만든 프로젝트에 초대받아 들어가면 권한이 **Viewer** 일 수 있는데, 그러면 교안_03 의 4절(프롬프트를 서버에 올리기)이 권한 오류로 막힙니다. 초대받아 쓰려면 **Member 이상**이어야 합니다.

## 3. API 키 발급받기

1) 키를 쓸 프로젝트에 들어간 상태에서 왼쪽 메뉴의 **Settings** 를 누릅니다(프로젝트 설정 화면입니다).
2) **API Keys** 항목에서 **Create new API keys** 를 누릅니다.
3) 화면에 **Secret Key**, **Public Key**, **Host** 가 함께 표시됩니다. 세 값을 모두 복사해 둡니다.

> **Secret Key 는 이 화면을 벗어나면 다시 볼 수 없습니다.** 못 받아 적었다면 그 키는 버리고(**Delete**) 새로 발급받으면 됩니다. 키를 여러 벌 만들어도 상관없습니다.

## 4. `.env` 에 채우기

22일차 폴더에서 예시 파일을 복사합니다.

```bash
cp .env.example .env
```

`.env` 를 열어 복사해 둔 값을 채웁니다. 따옴표는 붙이지 않고, 앞뒤 공백이 들어가지 않게 합니다.

```
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

`.env` 는 **공유하거나 깃에 올리지 않습니다**(`.gitignore` 에 이미 들어 있습니다). 값을 채운 뒤에는 **커널을 재시작**해야 노트북이 새 값을 읽습니다.

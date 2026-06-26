# StoryCore Web

웹소설 작가용 설정 관리 **클라우드 웹앱**입니다.

기존 `localStorage` MVP(`d:\first`)를 확장한 새 프로젝트로, 다음 기능을 포함합니다.

- **Google 로그인 / 로그아웃**
- **Supabase PostgreSQL** 데이터 저장
- **캐릭터 이미지** 업로드 (Supabase Storage)
- **PWA** — 홈 화면에 추가 가능

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React, TypeScript, Tailwind CSS, Vite |
| Auth | Supabase Auth (Google OAuth) |
| Database | Supabase PostgreSQL |
| Storage | Supabase Storage (`character-images`) |
| PWA | vite-plugin-pwa |

## 1. Supabase 프로젝트 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. **SQL Editor**에서 `supabase/migrations/001_initial.sql` 내용 실행
3. **Authentication → Providers → Google** 활성화
   - [Google Cloud Console](https://console.cloud.google.com)에서 OAuth 클라이언트 ID 생성
   - 승인된 리디렉션 URI: `https://<project-ref>.supabase.co/auth/v1/callback`
4. **Authentication → URL Configuration**
   - Site URL: `http://localhost:5173` (개발) / 배포 URL (프로덕션)
   - Redirect URLs: `http://localhost:5173/**`

## 2. 환경 변수

```bash
cd storycore-web
copy .env.example .env
```

`.env` 파일:

```
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

## 3. 실행

```bash
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 → Google 로그인

## 4. PWA 설치

- **Chrome/Edge**: 주소창 우측 "앱 설치" 또는 메뉴 → "StoryCore 설치"
- **모바일**: "홈 화면에 추가"

## 5. 프로덕션 빌드

```bash
npm run build
npm run preview
```

배포 시 Vercel, Netlify 등에 `dist` 폴더를 배포하고, Supabase Redirect URLs에 배포 URL을 추가하세요.

## 프로젝트 구조

```
storycore-web/
├── supabase/migrations/   # DB 스키마 + RLS + Storage 정책
├── src/
│   ├── app/App.tsx
│   ├── components/
│   │   ├── auth/          # 로그인 화면
│   │   └── common/        # ImageUpload, CharacterAvatar 등
│   ├── contexts/          # AuthContext, DataContext
│   ├── lib/               # Supabase, API, 이미지 업로드
│   └── types/
└── public/favicon.svg
```

## 캐릭터 이미지

- 캐릭터 생성/수정 Modal에서 이미지 업로드
- JPEG, PNG, WebP, GIF · 최대 5MB
- Supabase Storage `character-images/{userId}/{characterId}.ext` 경로에 저장

## 기존 MVP와의 차이

| | MVP (`d:\first`) | Web (`storycore-web`) |
|---|---|---|
| 저장 | localStorage | Supabase DB |
| 로그인 | 없음 | Google OAuth |
| 이미지 | 없음 | 캐릭터 1장 |
| PWA | 없음 | 지원 |

## 문제 해결

- **로그인 후 빈 화면**: Supabase SQL 마이그레이션 실행 여부 확인
- **Google 로그인 실패**: Redirect URL / Google OAuth 클라이언트 설정 확인
- **이미지 업로드 실패**: Storage bucket `character-images` 및 RLS 정책 확인

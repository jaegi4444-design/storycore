# StoryCore

웹소설 작가용 설정 관리 앱

## 프로젝트

| 폴더 | 설명 |
|------|------|
| `storycore-web/` | **메인** — Supabase + Google 로그인 + PWA (Vercel 배포용) |
| `src/` 등 (루트) | localStorage MVP (로컬 전용) |

## storycore-web 실행

```bash
cd storycore-web
npm install
cp .env.example .env   # Supabase 키 입력
npm run dev
```

## Vercel 배포

- Root Directory: **`storycore-web`**
- Environment Variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

자세한 내용: [storycore-web/VERCEL.md](storycore-web/VERCEL.md)

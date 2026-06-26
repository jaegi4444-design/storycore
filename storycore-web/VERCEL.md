# Vercel 배포 가이드

## 방법 A: Vercel 대시보드 (추천)

1. [vercel.com](https://vercel.com) 로그인 (GitHub 연동)
2. **Add New → Project**
3. 저장소 import (또는 `storycore-web` 폴더만 업로드)
4. **Root Directory**: `storycore-web` (저장소 루트가 `d:\first`인 경우)
5. **Environment Variables** 추가:

| Name | Value |
|------|--------|
| `VITE_SUPABASE_URL` | Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |

6. **Deploy** 클릭

배포 URL 예: `https://storycore-web.vercel.app`

---

## 방법 B: Vercel CLI

```powershell
cd d:\first\storycore-web
npx vercel login
npx vercel link
npx vercel env add VITE_SUPABASE_URL
npx vercel env add VITE_SUPABASE_ANON_KEY
npx vercel --prod
```

---

## 배포 후 필수 설정

### Supabase (Authentication → URL Configuration)

| 항목 | 값 |
|------|-----|
| Site URL | `https://your-app.vercel.app` |
| Redirect URLs | `https://your-app.vercel.app/**` |

로컬 개발도 유지하려면 Redirect URLs에 아래도 함께 추가:

```
http://localhost:5173/**
https://your-app.vercel.app/**
```

### Google Cloud (OAuth Redirect URI)

Google OAuth는 Supabase 콜백만 필요합니다 (변경 없음):

```
https://cembpfqfvkaoasvdnqmn.supabase.co/auth/v1/callback
```

---

## 확인

- Vercel URL 접속 → Google 로그인
- 헤더에 **「클라우드 저장」** 표시
- 캐릭터/작품 데이터 저장 확인

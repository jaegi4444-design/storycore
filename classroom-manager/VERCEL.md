# Vercel 배포 가이드 — Classroom Manager (콩콩 클래스)

storycore-web과 **동일 GitHub 저장소·동일 Supabase 프로젝트**를 사용합니다.

| 항목 | 값 |
|------|-----|
| GitHub | [jaegi4444-design/storycore](https://github.com/jaegi4444-design/storycore) |
| Vercel Root Directory | `classroom-manager` |
| Supabase Project | `cembpfqfvkaoasvdnqmn` |

---

## 0. Supabase DB 준비 (최초 1회)

[Supabase SQL Editor](https://supabase.com/dashboard/project/cembpfqfvkaoasvdnqmn/sql)에서 순서대로 실행:

1. `storycore-web/supabase/migrations/003_classroom_manager.sql`
2. `storycore-web/supabase/migrations/004_classroom_disable_rls.sql`
3. `storycore-web/supabase/migrations/005_children_company_name.sql`
4. `storycore-web/supabase/migrations/006_point_wallets.sql`

> Database password는 **필요 없습니다.** storycore-web처럼 URL + anon key로 PostgREST API를 사용합니다.

---

## 1. 환경 변수 (Vercel Dashboard)

**Settings → Environment Variables** 에 아래 3개를 추가합니다 (Production·Preview·Development 모두):

| Name | Value |
|------|--------|
| `VITE_SUPABASE_URL` | `https://cembpfqfvkaoasvdnqmn.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | storycore-web과 동일 anon key |
| `SESSION_SECRET_KEY` | 임의의 긴 랜덤 문자열 |

`SUPABASE_URL` / `SUPABASE_ANON_KEY` 이름으로 넣어도 됩니다 (둘 다 인식).

---

## 2. Vercel 대시보드 배포 (추천)

1. [vercel.com/new](https://vercel.com/new) → GitHub `jaegi4444-design/storycore` Import
2. **Root Directory** → `classroom-manager` 선택
3. Framework Preset: **Other** (자동 감지되면 그대로)
4. 위 환경 변수 3개 입력
5. **Deploy**

배포 후 `https://xxx.vercel.app/health` → `{"database":"supabase",...}` 확인

---

## 3. Vercel CLI

```powershell
cd d:\first\classroom-manager
npx vercel login
npx vercel link
npx vercel env add VITE_SUPABASE_URL
npx vercel env add VITE_SUPABASE_ANON_KEY
npx vercel env add SESSION_SECRET_KEY
npx vercel --prod
```

---

## storycore-web과 함께 쓰기

| 앱 | Vercel Root Directory | 로컬 포트 |
|----|----------------------|-----------|
| StoryCore | `storycore-web` | 5173 |
| 콩콩 클래스 | `classroom-manager` | 8080 |

같은 Supabase 프로젝트를 쓰지만 **테이블은 분리**되어 있습니다.

---

## 확인

- 배포 URL → 로그인 → 반 만들기 → 아이 추가 → 콩 지급
- `/health` 에서 `database: supabase` 확인
- 사진 업로드는 Supabase Storage `child-photos` 버킷 사용 (공개 버킷 필요)

---

## 주의

- Vercel 서버리스에서는 **SQLite를 쓸 수 없습니다.** 반드시 Supabase 환경 변수를 설정하세요.
- 로컬 `uploads/` 폴더는 Vercel에 올라가지 않습니다. 사진은 Supabase Storage에 저장됩니다.

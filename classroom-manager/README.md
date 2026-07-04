# Classroom Manager (콩콩 클래스)

storycore-web과 **동일한 방식**으로 Supabase를 사용합니다.

## Supabase 설정 (URL + anon key)

`classroom-manager/.env` 또는 `storycore-web/.env`:

```env
VITE_SUPABASE_URL=https://cembpfqfvkaoasvdnqmn.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
SESSION_SECRET_KEY=임의의-긴-문자열
```

> Database password는 **필요 없습니다.** storycore-web처럼 URL + anon key로 PostgREST API를 사용합니다.

### 최초 1회 — SQL 실행

Supabase SQL Editor에서 순서대로 실행:

1. `storycore-web/supabase/migrations/003_classroom_manager.sql`
2. `storycore-web/supabase/migrations/004_classroom_disable_rls.sql`
3. `storycore-web/supabase/migrations/005_children_company_name.sql` (이미 003 실행한 경우)
4. `storycore-web/supabase/migrations/006_point_wallets.sql` (포인트·지갑·거래내역)

## 실행

```powershell
cd classroom-manager
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location)
python run_web.py
```

http://127.0.0.1:8080

## Vercel

[VERCEL.md](VERCEL.md) — Root Directory: `classroom-manager`

환경변수: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `SESSION_SECRET_KEY`

## GitHub

저장소: [jaegi4444-design/storycore](https://github.com/jaegi4444-design/storycore)

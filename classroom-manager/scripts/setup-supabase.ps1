# Classroom Manager — Supabase 설정 (storycore-web 프로젝트 공유)

Write-Host "=== 콩콩 클래스 Supabase 설정 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "storycore-web과 동일한 Supabase 프로젝트를 사용합니다."
Write-Host "  Project: cembpfqfvkaoasvdnqmn"
Write-Host "  URL:     https://cembpfqfvkaoasvdnqmn.supabase.co"
Write-Host ""

$storycoreEnv = Join-Path $PSScriptRoot ".." ".." "storycore-web" ".env"
$classroomEnv = Join-Path $PSScriptRoot ".." ".env"
$exampleFile = Join-Path $PSScriptRoot ".." ".env.example"

if (-not (Test-Path $classroomEnv)) {
  Copy-Item $exampleFile $classroomEnv
  Write-Host ".env 파일 생성: $classroomEnv" -ForegroundColor Green
}

if (Test-Path $storycoreEnv) {
  Write-Host "storycore-web/.env 를 찾았습니다." -ForegroundColor Green
  Write-Host "  → SUPABASE_URL / SUPABASE_ANON_KEY 는 자동으로 읽힙니다."
  Write-Host "  → classroom-manager/.env 에 SUPABASE_DB_PASSWORD 만 추가하면 됩니다."
} else {
  Write-Host "storycore-web/.env 가 없습니다." -ForegroundColor Yellow
  Write-Host "  → classroom-manager/.env 에 SUPABASE_URL, SUPABASE_ANON_KEY 를 입력하세요."
}

Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. Supabase SQL Editor에서 실행:"
Write-Host "   storycore-web/supabase/migrations/003_classroom_manager.sql"
Write-Host "2. Supabase → Project Settings → Database → password 확인"
Write-Host "3. classroom-manager/.env 에 SUPABASE_DB_PASSWORD 입력"
Write-Host "4. python run_web.py 로 실행"
Write-Host ""
Write-Host "Vercel 배포: classroom-manager/VERCEL.md 참고"

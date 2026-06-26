# StoryCore Web - Supabase 클라우드 설정 가이드
# 로컬 모드(.env 없음)로도 앱은 바로 실행됩니다.
# Google 로그인 + 클라우드 DB를 쓰려면 아래 단계를 진행하세요.

Write-Host "=== StoryCore Supabase 설정 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. https://supabase.com 에서 프로젝트 생성"
Write-Host "2. SQL Editor에서 supabase/migrations/001_initial.sql 실행"
Write-Host "3. Settings > API 에서 URL과 anon key 복사"
Write-Host "4. Authentication > Google 활성화 (Google Cloud OAuth 필요)"
Write-Host "5. Authentication > URL Configuration"
Write-Host "   - Site URL: http://localhost:5173"
Write-Host "   - Redirect URLs: http://localhost:5173/**"
Write-Host ""

$envFile = Join-Path $PSScriptRoot ".." ".env"
$exampleFile = Join-Path $PSScriptRoot ".." ".env.example"

if (-not (Test-Path $envFile)) {
  Copy-Item $exampleFile $envFile
  Write-Host ".env 파일을 생성했습니다: $envFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "아래 값을 .env 파일에 입력하세요:" -ForegroundColor Yellow
Write-Host "  VITE_SUPABASE_URL=..."
Write-Host "  VITE_SUPABASE_ANON_KEY=..."
Write-Host ""
Write-Host "입력 후 개발 서버를 재시작하면 Google 로그인 + 클라우드 DB가 활성화됩니다."

# Supabase CLI 로그인 (선택)
if (Get-Command supabase -ErrorAction SilentlyContinue) {
  Write-Host ""
  Write-Host "Supabase CLI가 설치되어 있습니다." -ForegroundColor Green
  Write-Host "클라우드 연동: supabase login 후 supabase link --project-ref <ref>"
}

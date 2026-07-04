-- classroom-manager: anon key(PostgREST)로 서버 접근 — MVP용 RLS 비활성화
-- storycore-web auth.users 와 별개 public 테이블

ALTER TABLE IF EXISTS public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.code_table DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.classes DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.children DISABLE ROW LEVEL SECURITY;

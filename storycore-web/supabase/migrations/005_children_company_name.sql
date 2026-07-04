-- 아이별 회사(company_name) 컬럼 추가
ALTER TABLE public.children
  ADD COLUMN IF NOT EXISTS company_name VARCHAR(100);

-- 반별 화폐 단위 직접 입력 (currency_name)

ALTER TABLE public.classes
  ADD COLUMN IF NOT EXISTS currency_name VARCHAR(100);

UPDATE public.classes c
SET currency_name = ct.code_name
FROM public.code_table ct
WHERE ct.group_code = 'CURRENCY'
  AND ct.code = c.currency_code
  AND c.currency_name IS NULL;

UPDATE public.classes
SET currency_name = '콩'
WHERE currency_name IS NULL;

ALTER TABLE public.classes
  ALTER COLUMN currency_name SET DEFAULT '콩';

UPDATE public.classes
SET currency_name = '콩'
WHERE currency_name IS NULL;

ALTER TABLE public.classes
  ALTER COLUMN currency_name SET NOT NULL;

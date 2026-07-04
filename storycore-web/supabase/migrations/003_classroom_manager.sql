# Classroom Manager — classroom-manager 테이블 (storycore-web과 동일 Supabase 프로젝트)
# SQL Editor에서 실행하거나 Supabase CLI로 적용

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.code_table (
    id SERIAL PRIMARY KEY,
    group_code VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    code_name VARCHAR(100) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    use_yn VARCHAR(1) NOT NULL DEFAULT 'Y',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_code_table_group_code UNIQUE (group_code, code)
);

CREATE INDEX IF NOT EXISTS ix_code_table_group_code ON public.code_table (group_code);

CREATE TABLE IF NOT EXISTS public.classes (
    id SERIAL PRIMARY KEY,
    teacher_user_id INTEGER NOT NULL UNIQUE REFERENCES public.users (id),
    class_name VARCHAR(100) NOT NULL,
    currency_code VARCHAR(50) NOT NULL DEFAULT 'BEAN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.children (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES public.classes (id) ON DELETE CASCADE,
    child_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100),
    photo_path VARCHAR(500),
    photo_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_children_class_id ON public.children (class_id);

INSERT INTO public.code_table (group_code, code, code_name, sort_order, use_yn)
VALUES ('CURRENCY', 'BEAN', '콩', 1, 'Y')
ON CONFLICT (group_code, code) DO NOTHING;

-- 아이 프로필 사진 Storage (storycore character-images와 별도 버킷)
INSERT INTO storage.buckets (id, name, public)
VALUES ('child-photos', 'child-photos', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "child_photos_select" ON storage.objects;
DROP POLICY IF EXISTS "child_photos_insert" ON storage.objects;
DROP POLICY IF EXISTS "child_photos_update" ON storage.objects;
DROP POLICY IF EXISTS "child_photos_delete" ON storage.objects;

CREATE POLICY "child_photos_select"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'child-photos');

CREATE POLICY "child_photos_insert"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'child-photos');

CREATE POLICY "child_photos_update"
  ON storage.objects FOR UPDATE
  USING (bucket_id = 'child-photos');

CREATE POLICY "child_photos_delete"
  ON storage.objects FOR DELETE
  USING (bucket_id = 'child-photos');

-- 포인트 지갑 및 거래내역 + soft delete + 원자적 지급/차감 RPC

-- children soft delete
ALTER TABLE public.children
  ADD COLUMN IF NOT EXISTS deleted_yn VARCHAR(1) NOT NULL DEFAULT 'N';

-- 아이별 지갑
CREATE TABLE IF NOT EXISTS public.student_wallets (
    id SERIAL PRIMARY KEY,
    child_id INTEGER NOT NULL REFERENCES public.children (id),
    currency_code VARCHAR(50) NOT NULL DEFAULT 'BEAN',
    balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_student_wallets_child_currency UNIQUE (child_id, currency_code)
);

CREATE INDEX IF NOT EXISTS ix_student_wallets_child_id ON public.student_wallets (child_id);

-- 거래내역
CREATE TABLE IF NOT EXISTS public.point_transactions (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES public.classes (id),
    child_id INTEGER NOT NULL REFERENCES public.children (id),
    wallet_id INTEGER NOT NULL REFERENCES public.student_wallets (id),
    transaction_type VARCHAR(20) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    memo TEXT,
    created_by_user_id INTEGER NOT NULL REFERENCES public.users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_point_transactions_child_id ON public.point_transactions (child_id);
CREATE INDEX IF NOT EXISTS ix_point_transactions_class_id ON public.point_transactions (class_id);
CREATE INDEX IF NOT EXISTS ix_point_transactions_created_at ON public.point_transactions (created_at DESC);

-- 기존 아이 지갑 생성
INSERT INTO public.student_wallets (child_id, currency_code, balance)
SELECT c.id, cl.currency_code, 0
FROM public.children c
JOIN public.classes cl ON cl.id = c.class_id
WHERE COALESCE(c.deleted_yn, 'N') = 'N'
ON CONFLICT (child_id, currency_code) DO NOTHING;

-- 콩 지급 (단일 트랜잭션 + row lock)
CREATE OR REPLACE FUNCTION public.cm_deposit_points(
    p_child_id INTEGER,
    p_amount INTEGER,
    p_memo TEXT,
    p_user_id INTEGER
) RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_child RECORD;
    v_class RECORD;
    v_wallet RECORD;
    v_balance_before INTEGER;
    v_balance_after INTEGER;
    v_tx_id INTEGER;
BEGIN
    IF p_amount IS NULL OR p_amount < 1 THEN
        RAISE EXCEPTION 'INVALID_AMOUNT';
    END IF;

    SELECT * INTO v_child FROM public.children
    WHERE id = p_child_id AND COALESCE(deleted_yn, 'N') = 'N';
    IF NOT FOUND THEN RAISE EXCEPTION 'CHILD_NOT_FOUND'; END IF;

    SELECT * INTO v_class FROM public.classes WHERE id = v_child.class_id;
    IF NOT FOUND OR v_class.teacher_user_id != p_user_id THEN
        RAISE EXCEPTION 'ACCESS_DENIED';
    END IF;

    SELECT * INTO v_wallet FROM public.student_wallets
    WHERE child_id = p_child_id AND currency_code = v_class.currency_code
    FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'WALLET_NOT_FOUND'; END IF;

    v_balance_before := v_wallet.balance;
    v_balance_after := v_balance_before + p_amount;

    UPDATE public.student_wallets
    SET balance = v_balance_after, updated_at = NOW()
    WHERE id = v_wallet.id;

    INSERT INTO public.point_transactions (
        class_id, child_id, wallet_id, transaction_type, amount,
        balance_before, balance_after, currency_code, memo, created_by_user_id
    ) VALUES (
        v_class.id, p_child_id, v_wallet.id, 'DEPOSIT', p_amount,
        v_balance_before, v_balance_after, v_class.currency_code, p_memo, p_user_id
    ) RETURNING id INTO v_tx_id;

    RETURN jsonb_build_object(
        'transaction_id', v_tx_id,
        'balance_before', v_balance_before,
        'balance_after', v_balance_after
    );
END;
$$;

-- 콩 차감
CREATE OR REPLACE FUNCTION public.cm_withdraw_points(
    p_child_id INTEGER,
    p_amount INTEGER,
    p_memo TEXT,
    p_user_id INTEGER
) RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_child RECORD;
    v_class RECORD;
    v_wallet RECORD;
    v_balance_before INTEGER;
    v_balance_after INTEGER;
    v_tx_id INTEGER;
BEGIN
    IF p_amount IS NULL OR p_amount < 1 THEN
        RAISE EXCEPTION 'INVALID_AMOUNT';
    END IF;

    SELECT * INTO v_child FROM public.children
    WHERE id = p_child_id AND COALESCE(deleted_yn, 'N') = 'N';
    IF NOT FOUND THEN RAISE EXCEPTION 'CHILD_NOT_FOUND'; END IF;

    SELECT * INTO v_class FROM public.classes WHERE id = v_child.class_id;
    IF NOT FOUND OR v_class.teacher_user_id != p_user_id THEN
        RAISE EXCEPTION 'ACCESS_DENIED';
    END IF;

    SELECT * INTO v_wallet FROM public.student_wallets
    WHERE child_id = p_child_id AND currency_code = v_class.currency_code
    FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'WALLET_NOT_FOUND'; END IF;

    v_balance_before := v_wallet.balance;
    IF v_balance_before < p_amount THEN
        RAISE EXCEPTION 'INSUFFICIENT_BALANCE';
    END IF;
    v_balance_after := v_balance_before - p_amount;

    UPDATE public.student_wallets
    SET balance = v_balance_after, updated_at = NOW()
    WHERE id = v_wallet.id;

    INSERT INTO public.point_transactions (
        class_id, child_id, wallet_id, transaction_type, amount,
        balance_before, balance_after, currency_code, memo, created_by_user_id
    ) VALUES (
        v_class.id, p_child_id, v_wallet.id, 'WITHDRAW', p_amount,
        v_balance_before, v_balance_after, v_class.currency_code, p_memo, p_user_id
    ) RETURNING id INTO v_tx_id;

    RETURN jsonb_build_object(
        'transaction_id', v_tx_id,
        'balance_before', v_balance_before,
        'balance_after', v_balance_after
    );
END;
$$;

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { isSupabaseConfigured, supabase } from '../lib/supabase';

export const isLocalMode = !isSupabaseConfigured;

const LOCAL_USER = {
  id: 'local-user',
  email: 'local@storycore.dev',
  aud: 'authenticated',
  role: 'authenticated',
  app_metadata: { provider: 'local' },
  user_metadata: { full_name: '로컬 사용자', avatar_url: null },
  created_at: new Date().toISOString(),
} as User;

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  configured: boolean;
  isLocalMode: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isLocalMode) {
      setLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin,
      },
    });
    if (error) throw error;
  }, []);

  const signOut = useCallback(async () => {
    if (isLocalMode) return;
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  }, []);

  const user = isLocalMode ? LOCAL_USER : (session?.user ?? null);

  const value = useMemo(
    () => ({
      user,
      session: isLocalMode ? null : session,
      loading,
      configured: isSupabaseConfigured,
      isLocalMode,
      signInWithGoogle,
      signOut,
    }),
    [user, session, loading, signInWithGoogle, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

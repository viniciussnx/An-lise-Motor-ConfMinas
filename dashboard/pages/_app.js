import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import '../styles/globals.css';
import { isAuthenticated } from '../lib/api';

const PUBLIC_PATHS = new Set(['/login']);

export default function App({ Component, pageProps }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const path = router.pathname;
    if (PUBLIC_PATHS.has(path)) {
      setReady(true);
      return;
    }
    if (!isAuthenticated()) {
      const next = encodeURIComponent(router.asPath || '/');
      router.replace(`/login?next=${next}`);
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#64748b',
          fontFamily: 'Inter, sans-serif',
          fontSize: 13,
          background:
            'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(59,108,244,0.08), transparent), #e9edf3',
        }}
      >
        Carregando…
      </div>
    );
  }

  return <Component {...pageProps} />;
}

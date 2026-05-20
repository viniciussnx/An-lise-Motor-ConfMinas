import { memo } from 'react';
import Link from 'next/link';

/** Logo horizontal ConfiMinas Engenharia (1024×355) */
const ASPECT = 1024 / 355;

function ConfiMinasLogo({ href = '/', height = 42, maxWidth = 220, className = '' }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center shrink-0 ${className}`.trim()}
      style={{ lineHeight: 0 }}
      aria-label="ConfiMinas Engenharia — início"
    >
      <img
        src="/logo-confiminas.png"
        alt="ConfiMinas Engenharia"
        width={Math.round(height * ASPECT)}
        height={height}
        style={{
          height,
          width: 'auto',
          maxWidth,
          objectFit: 'contain',
          objectPosition: 'left center',
          display: 'block',
        }}
        draggable={false}
      />
    </Link>
  );
}

export default memo(ConfiMinasLogo);

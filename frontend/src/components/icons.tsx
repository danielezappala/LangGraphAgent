import type { SVGProps } from 'react';

export function RediLogo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 12c-2-2.67-4-4-4-4a4 4 0 1 1 8 0s-2 1.33-4 4z" />
      <path d="M12 12v6" />
      <path d="M12 21a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" />
      <path d="M4.22 13.78a2.5 2.5 0 0 1-1.1-4.06" />
      <path d="M19.78 9.72a2.5 2.5 0 0 1-1.1 4.06" />
    </svg>
  );
}

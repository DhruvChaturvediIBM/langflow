import React from "react";

const SvgDB2 = React.forwardRef<SVGSVGElement, React.SVGProps<SVGSVGElement>>(
  (props, ref) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      ref={ref}
      {...props}
    >
      <defs>
        <linearGradient id="db2-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: "#0f62fe", stopOpacity: 1 }} />
          <stop
            offset="100%"
            style={{ stopColor: "#0043ce", stopOpacity: 1 }}
          />
        </linearGradient>
      </defs>
      <rect width="32" height="32" fill="url(#db2-gradient)" rx="2" />
      <text
        x="16"
        y="20"
        fontFamily="IBM Plex Sans, sans-serif"
        fontSize="12"
        fontWeight="600"
        fill="white"
        textAnchor="middle"
      >
        Db2
      </text>
      <path
        d="M8 10 L24 10 L24 12 L8 12 Z M8 14 L20 14 L20 16 L8 16 Z M8 18 L22 18 L22 20 L8 20 Z"
        fill="white"
        opacity="0.3"
      />
    </svg>
  ),
);

SvgDB2.displayName = "SvgDB2";

export default SvgDB2;

// Made with Bob

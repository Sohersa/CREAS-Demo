/* global React */
// OBRA YA logo — modern geometric mark
// Concept: two rising bars forming an abstract "OY" / crane / upward motion
// Colors: violet → orange gradient representing "de obra a ya" (speed)

function OYLogo({ size = 32, color, showText = true, textSize = 20 }) {
  const gradId = `oyGrad${Math.floor(Math.random() * 100000)}`;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10, letterSpacing: '-0.035em', fontWeight: 700, fontSize: textSize }}>
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" style={{ flexShrink: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#FF7A45"/>
            <stop offset="50%" stopColor="#FF80B5"/>
            <stop offset="100%" stopColor="#635BFF"/>
          </linearGradient>
        </defs>
        {color ? (
          <>
            {/* Solid color variant */}
            <rect x="2" y="16" width="8" height="14" rx="2" fill={color}/>
            <rect x="12" y="10" width="8" height="20" rx="2" fill={color}/>
            <rect x="22" y="2" width="8" height="28" rx="2" fill={color}/>
            <circle cx="26" cy="6" r="3" fill={color === 'white' ? '#FF7A45' : 'white'}/>
          </>
        ) : (
          <>
            {/* Gradient: three rising bars + a beacon dot */}
            <rect x="2" y="16" width="8" height="14" rx="2" fill="#FF7A45"/>
            <rect x="12" y="10" width="8" height="20" rx="2" fill="#FF80B5"/>
            <rect x="22" y="2" width="8" height="28" rx="2" fill={`url(#${gradId})`}/>
            <circle cx="26" cy="6" r="3" fill="#FFFFFF"/>
            <circle cx="26" cy="6" r="1.5" fill="#635BFF"/>
          </>
        )}
      </svg>
      {showText && <span>OBRA·YA</span>}
    </span>
  );
}

window.OYLogo = OYLogo;

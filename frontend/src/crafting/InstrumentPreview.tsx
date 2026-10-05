import React from 'react';
type Appearance={instrument_type:'guitar'|'bass';shape_key:string;primary_colour:string;accent_colour?:string;hardware_colour?:string;surface_sheen?:string};
const InstrumentPreview:React.FC<{appearance:Appearance;label?:string}>=({appearance,label})=>{
 const bass=appearance.instrument_type==='bass',primary=appearance.primary_colour||'#202020',accent=appearance.accent_colour||'#d0d0d0',metal=appearance.hardware_colour||'#c0c0c0';
 return <svg viewBox="0 0 220 520" role="img" aria-label={label||'Crafted instrument preview'} className="w-full max-w-[220px] mx-auto">
  <g><rect x="101" y="70" width="18" height={bass?290:260} rx="7" fill={accent}/><rect x="105" y="76" width="10" height={bass?280:250} rx="4" fill="#33261d"/>
   <path d={bass?"M64 330 C20 350 18 430 55 470 C80 500 105 476 110 450 C115 476 145 500 169 468 C204 420 198 350 155 330 C138 322 126 330 110 342 C94 330 82 322 64 330Z":"M58 310 C20 330 22 405 56 448 C78 476 100 456 110 432 C120 456 144 476 166 448 C198 405 200 330 162 310 C142 300 126 310 110 326 C94 310 78 300 58 310Z"} fill={primary} stroke={accent} strokeWidth="6"/>
   <rect x="92" y="345" width="36" height="12" rx="3" fill={metal}/><rect x="90" y="374" width="40" height="9" rx="3" fill={metal}/>
   <rect x="102" y="30" width="16" height="50" rx="5" fill={accent}/>{[0,1,2,3,4,5].slice(0,bass?4:6).map(n=><line key={n} x1={105+n*2} y1="55" x2={105+n*2} y2="430" stroke="#ddd" strokeWidth=".8"/>)}
  </g>
 </svg>
};
export default InstrumentPreview;

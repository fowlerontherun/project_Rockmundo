import React,{useId} from 'react';
type Appearance={instrument_type:'guitar'|'bass';shape_key:string;primary_colour:string;accent_colour?:string;hardware_colour?:string;surface_sheen?:string};
const bodyPath=(shape:string,bass:boolean)=>{
 const k=shape.split('.').pop()||'';
 const paths:Record<string,string>={
  v_style:'M110 332 L38 488 L92 426 L110 462 L128 426 L182 488 L110 332Z',
  extreme_v:'M110 326 L24 505 L94 432 L110 478 L126 432 L196 505 L110 326Z',
  explorer:'M64 318 L22 384 L72 398 L42 480 L112 442 L174 474 L158 400 L198 350 L142 344 L110 326Z',
  coffin:'M76 314 L144 314 L174 350 L160 478 L110 506 L60 478 L46 350Z',
  star:'M110 304 L132 366 L198 366 L145 405 L164 470 L110 432 L56 470 L75 405 L22 366 L88 366Z',
  offset:'M70 308 C28 324 22 394 52 452 C72 490 104 458 116 430 C136 474 170 470 184 426 C198 378 174 330 148 316 C128 306 116 320 104 336 C92 318 84 304 70 308Z',
  single_cut:'M72 308 C34 326 32 404 62 454 C82 484 108 456 112 432 C126 450 156 452 176 420 C196 388 180 326 148 314 C130 308 118 320 110 336 C100 320 90 302 72 308Z',
  t_style:'M62 316 C30 340 36 424 70 456 C90 474 108 448 112 426 L136 456 C166 468 188 426 178 374 C170 330 146 316 122 328 L110 344 C96 326 78 306 62 316Z',
  modern_metal:'M64 312 L30 372 L70 388 L42 478 L104 438 L126 484 L154 400 L194 374 L150 342 L128 326 L110 350 L90 326Z',
  extreme_asymmetric:'M54 318 L20 410 L78 398 L52 492 L112 438 L150 486 L164 402 L200 344 L142 350 L116 324 L98 350Z',
  extreme_horns:'M48 308 L76 378 L44 484 L104 438 L110 486 L120 438 L180 484 L146 376 L174 306 L128 346 L110 326 L92 346Z',
  signature_razor:'M58 318 L22 390 L78 400 L46 488 L110 442 L154 492 L144 408 L194 354 L140 350 L114 330 L94 350Z'
 };
 if(paths[k])return paths[k];
 return bass?'M64 330 C20 350 18 430 55 470 C80 500 105 476 110 450 C115 476 145 500 169 468 C204 420 198 350 155 330 C138 322 126 330 110 342 C94 330 82 322 64 330Z':'M58 310 C20 330 22 405 56 448 C78 476 100 456 110 432 C120 456 144 476 166 448 C198 405 200 330 162 310 C142 300 126 310 110 326 C94 310 78 300 58 310Z';
};
const InstrumentPreview:React.FC<{appearance:Appearance;label?:string}>=({appearance,label})=>{
 const id=useId().replace(/:/g,''),bass=appearance.instrument_type==='bass',primary=appearance.primary_colour||'#202020',accent=appearance.accent_colour||'#d0d0d0',metal=appearance.hardware_colour||'#c0c0c0',sheen=appearance.surface_sheen||'gloss',headless=appearance.shape_key.includes('headless');
 const opacity=sheen==='matte'?.05:sheen==='satin'?.12:.22;
 return <svg viewBox="0 0 220 520" role="img" aria-label={label||'Crafted instrument preview'} className="w-full max-w-[220px] mx-auto">
  <defs><linearGradient id={'body-'+id} x1="0" y1="0" x2="1" y2="1"><stop stopColor={primary}/><stop offset=".72" stopColor={primary}/><stop offset="1" stopColor={accent}/></linearGradient><linearGradient id={'shine-'+id}><stop stopColor="#fff" stopOpacity={opacity}/><stop offset=".5" stopColor="#fff" stopOpacity="0"/></linearGradient></defs>
  <g><rect x="101" y="70" width="18" height={bass?290:260} rx="7" fill={accent}/><rect x="105" y="76" width="10" height={bass?280:250} rx="4" fill="#33261d"/>
   <path d={bodyPath(appearance.shape_key,bass)} fill={'url(#body-'+id+')'} stroke={accent} strokeWidth="6"/><path d={bodyPath(appearance.shape_key,bass)} fill={'url(#shine-'+id+')'}/>
   <rect x="92" y="345" width="36" height="12" rx="3" fill={metal}/><rect x="90" y="374" width="40" height="9" rx="3" fill={metal}/>
   {!headless&&<rect x="102" y="30" width="16" height="50" rx="5" fill={accent}/>}
   {[0,1,2,3,4,5].slice(0,bass?4:6).map(n=><line key={n} x1={105+n*2} y1={headless?76:55} x2={105+n*2} y2="430" stroke="#ddd" strokeWidth=".8"/>)}
  </g>
 </svg>
};
export default InstrumentPreview;

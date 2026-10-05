import React,{useEffect,useMemo,useState} from 'react';
import {apiFetch} from '../../utils/api.js';

type Shape={key:string;name:string;instrument_type:'guitar'|'bass';required_level:number;locked:boolean;visual?:any};
type Material={key:string;name:string;rarity:string;cost_cents:number;required_level:number;locked:boolean;stat_affinities_json?:string};
type Component={key:string;name:string;part_type:string;required_level:number;locked:boolean};
type Owned={key:string;quantity:number};
const PARTS=['body','neck','fretboard','electronics','hardware'] as const;
type Part=typeof PARTS[number];

const LuthieryWorkshop:React.FC=()=>{
 const [cat,setCat]=useState<{shapes:Shape[];materials:Material[];components:Component[]}>({shapes:[],materials:[],components:[]});
 const [owned,setOwned]=useState<Owned[]>([]),[type,setType]=useState<'guitar'|'bass'>('guitar'),[shape,setShape]=useState('');
 const [step,setStep]=useState<Part|'finish'>('body'),[parts,setParts]=useState<Record<string,{material_key:string;component_key?:string}>>({});
 const [name,setName]=useState(''),[primary,setPrimary]=useState('#202020'),[accent,setAccent]=useState('#d0d0d0'),[finish,setFinish]=useState('luthier.finish.solid');
 const [message,setMessage]=useState(''),[result,setResult]=useState<any>(null),[busy,setBusy]=useState(false);
 useEffect(()=>{Promise.all([apiFetch('/luthiery/catalogue'),apiFetch('/luthiery/materials/inventory')]).then(async([a,b])=>{
   if(!a.ok||!b.ok)throw new Error('Unable to load Luthier workshop');setCat(await a.json());setOwned((await b.json()).items);
 }).catch(e=>setMessage(e.message));},[]);
 const shapes=cat.shapes.filter(s=>s.instrument_type===type); const selectedShape=shapes.find(s=>s.key===shape);
 useEffect(()=>{if(!selectedShape&&shapes.length)setShape(shapes.find(s=>!s.locked)?.key||shapes[0].key)},[type,cat.shapes]);
 const qty=(k:string)=>owned.find(x=>x.key===k)?.quantity||0;
 const ready=!!shape&&PARTS.every(p=>parts[p]?.material_key)&&!!name.trim()&&!selectedShape?.locked;
 const estimated=useMemo(()=>{const chosen=PARTS.map(p=>cat.materials.find(m=>m.key===parts[p]?.material_key)).filter(Boolean) as Material[];
   if(!chosen.length)return null; const rarity={common:1,uncommon:2,rare:3,epic:4,legendary:5};return Math.round(chosen.reduce((n,m)=>n+(rarity[m.rarity as keyof typeof rarity]||1),0)/chosen.length*20);
 },[parts,cat.materials]);
 const chooseMaterial=(p:Part,key:string)=>setParts(v=>({...v,[p]:{...v[p],material_key:key}}));
 const chooseComponent=(p:Part,key:string)=>setParts(v=>({...v,[p]:{...v[p],component_key:key||undefined}}));
 const craft=async()=>{if(!ready)return;setBusy(true);setMessage('');setResult(null);
   const token=globalThis.crypto?.randomUUID?.()||`craft-${Date.now()}`;
   const r=await apiFetch('/luthiery/craft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    request_token:token,name,instrument_type:type,shape_key:shape,selections:parts,finish_key:finish,primary_colour:primary,accent_colour:accent})});
   const d=await r.json();setBusy(false);if(!r.ok){setMessage(d.detail||'Crafting failed');return;}setResult(d);setMessage('Instrument crafted successfully.');
 };
 const anchor=selectedShape?.visual?.anchors||{};
 return <section aria-labelledby="luthier-workshop-title" className="space-y-4">
  <header><h2 id="luthier-workshop-title">Luthier Workshop</h2><p>Build a unique instrument one part at a time.</p></header>
  {message&&<p role="status">{message}</p>}
  <div className="grid gap-4 lg:grid-cols-[minmax(280px,1fr)_minmax(320px,1fr)]">
   <div className="sticky top-2 self-start rounded border p-4 min-h-[420px]" aria-label="Live instrument preview">
    <div className="flex gap-2"><button onClick={()=>setType('guitar')} aria-pressed={type==='guitar'}>Guitar</button><button onClick={()=>setType('bass')} aria-pressed={type==='bass'}>Bass</button></div>
    <select value={shape} onChange={e=>setShape(e.target.value)} className="w-full mt-2">{shapes.map(s=><option key={s.key} value={s.key} disabled={s.locked}>{s.name}{s.locked?` — level ${s.required_level}`:''}</option>)}</select>
    <div className="relative mx-auto mt-4 aspect-[3/4] max-w-sm overflow-hidden rounded border" style={{background:`linear-gradient(145deg,${primary},${accent})`}}>
      <div className="absolute inset-0 flex items-center justify-center text-center p-8"><strong>{selectedShape?.name||'Select a shape'}</strong></div>
      {PARTS.filter(p=>parts[p]).map(p=><span key={p} className="absolute text-xs border rounded px-1" style={{left:`${(anchor[p]?.x||.5)*100}%`,top:`${(anchor[p]?.y||.5)*100}%`,transform:'translate(-50%,-50%)'}}>{p}</span>)}
    </div>
    <p className="text-sm">Estimated material potential: {estimated??'—'}/100</p>
   </div>
   <div>
    <nav className="flex flex-wrap gap-2" aria-label="Build steps">{[...PARTS,'finish'].map(p=><button key={p} onClick={()=>setStep(p as any)} aria-current={step===p?'step':undefined}>{p[0].toUpperCase()+p.slice(1)} {p!=='finish'&&parts[p]?.material_key?'✓':''}</button>)}</nav>
    {step!=='finish'?<div className="mt-4 space-y-3"><h3>{step[0].toUpperCase()+step.slice(1)}</h3>
      <label>Material<select className="w-full" value={parts[step]?.material_key||''} onChange={e=>chooseMaterial(step,e.target.value)}><option value="">Choose material</option>{cat.materials.map(m=><option key={m.key} value={m.key} disabled={m.locked||qty(m.key)<1}>{m.name} · owned {qty(m.key)}{m.locked?` · level ${m.required_level}`:''}</option>)}</select></label>
      <label>Component<select className="w-full" value={parts[step]?.component_key||''} onChange={e=>chooseComponent(step,e.target.value)}><option value="">Standard / none</option>{cat.components.filter(c=>c.part_type===step).map(c=><option key={c.key} value={c.key} disabled={c.locked}>{c.name}{c.locked?` · level ${c.required_level}`:''}</option>)}</select></label>
    </div>:<div className="mt-4 space-y-3"><label>Instrument name<input value={name} maxLength={80} onChange={e=>setName(e.target.value)} /></label>
      <label>Finish<select value={finish} onChange={e=>setFinish(e.target.value)}><option value="luthier.finish.solid">Solid</option><option value="luthier.finish.natural">Natural</option><option value="luthier.finish.transparent">Transparent</option><option value="luthier.finish.metallic">Metallic</option></select></label>
      <label>Primary colour<input type="color" value={primary} onChange={e=>setPrimary(e.target.value)} /></label><label>Accent colour<input type="color" value={accent} onChange={e=>setAccent(e.target.value)} /></label>
      <div className="rounded border p-3"><strong>Final build review</strong><p>{selectedShape?.name} · {PARTS.filter(p=>parts[p]?.material_key).length}/5 parts selected</p><p>Crafting consumes one owned material for each part.</p></div>
      <button disabled={!ready||busy} onClick={craft}>{busy?'Crafting…':'Craft instrument'}</button>
    </div>}
    {result&&<div className="mt-4 rounded border p-3"><h3>{result.name}</h3><p>{result.quality_tier} · quality {result.quality_score}</p><p>Maker serial: {result.serial_number}</p></div>}
   </div>
  </div>
 </section>
};
export default LuthieryWorkshop;

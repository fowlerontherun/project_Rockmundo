import React,{useEffect,useMemo,useRef,useState} from 'react';
import {apiFetch} from '../../utils/api.js';\nimport InstrumentPreview from './InstrumentPreview';

type Shape={key:string;name:string;instrument_type:'guitar'|'bass';required_level:number;locked:boolean;visual?:any};
type Material={key:string;name:string;rarity:string;cost_cents:number;required_level:number;locked:boolean;material_type:string;stat_affinities_json?:string};
type Component={key:string;name:string;part_type:string;required_level:number;locked:boolean};
type Owned={key:string;quantity:number};
type Workshop={character_id:number;quality_score:number;upgrade_level:number;next_upgrade_cost_cents:number|null};
const PARTS=['body','neck','fretboard','electronics','hardware'] as const;\nconst MATERIAL_TYPES:Record<string,string[]>={body:['body_wood','wood','decorative_wood'],neck:['wood'],fretboard:['fretboard_wood','wood'],electronics:['wood','body_wood','decorative_wood'],hardware:['wood','body_wood','decorative_wood']};
type Part=typeof PARTS[number];

const materialSwatch=(m:Material)=>{const n=m.name.toLowerCase();if(n.includes('maple'))return 'repeating-linear-gradient(100deg,#d9bd82 0 8px,#cba96d 9px 11px)';if(n.includes('rosewood'))return 'repeating-linear-gradient(100deg,#4b281c 0 7px,#6b3b27 8px 10px)';if(n.includes('mahogany'))return 'repeating-linear-gradient(100deg,#713c2c 0 8px,#8a4b36 9px 11px)';if(n.includes('ebony'))return 'repeating-linear-gradient(100deg,#171513 0 8px,#302b27 9px 10px)';return 'repeating-linear-gradient(100deg,#9b744b 0 8px,#c29a68 9px 11px)'};\nconst LuthieryWorkshop:React.FC=()=>{
 const [cat,setCat]=useState<{shapes:Shape[];materials:Material[];components:Component[]}>({shapes:[],materials:[],components:[]});
 const [finishingLevel,setFinishingLevel]=useState(0);
 const [workshop,setWorkshop]=useState<Workshop|null>(null),[upgradingWorkshop,setUpgradingWorkshop]=useState(false);
 const [owned,setOwned]=useState<Owned[]>([]),[type,setType]=useState<'guitar'|'bass'>('guitar'),[shape,setShape]=useState('');
 const [step,setStep]=useState<Part|'finish'>('body'),[parts,setParts]=useState<Record<string,{material_key:string;component_key?:string}>>({});
 const [name,setName]=useState(''),[primary,setPrimary]=useState('#202020'),[accent,setAccent]=useState('#d0d0d0'),[hardwareColour,setHardwareColour]=useState('#c0c0c0'),[finish,setFinish]=useState('luthier.finish.solid');
 const [sheen,setSheen]=useState<'matte'|'satin'|'gloss'>('gloss'),[zoom,setZoom]=useState(1),[rotation,setRotation]=useState(0),[rareConfirmed,setRareConfirmed]=useState(false);
 const [message,setMessage]=useState(''),[result,setResult]=useState<any>(null),[busy,setBusy]=useState(false);\n const craftToken=useRef<string>('');
 useEffect(()=>{Promise.all([apiFetch('/luthiery/catalogue'),apiFetch('/luthiery/materials/inventory'),apiFetch('/luthiery/workshop')]).then(async([a,b,w])=>{
   if(!a.ok||!b.ok||!w.ok)throw new Error('Unable to load Luthier workshop');const catalogue=await a.json();setCat(catalogue);setFinishingLevel(Number(catalogue.skill_levels?.instrument_finishing||0));setOwned((await b.json()).items);setWorkshop(await w.json());
 }).catch(e=>setMessage(e.message));},[]);
 const shapes=cat.shapes.filter(s=>s.instrument_type===type); const selectedShape=shapes.find(s=>s.key===shape);
 useEffect(()=>{if(!selectedShape&&shapes.length)setShape(shapes.find(s=>!s.locked)?.key||shapes[0].key)},[type,cat.shapes]);
 const qty=(k:string)=>owned.find(x=>x.key===k)?.quantity||0;\n const materialsFor=(p:Part)=>cat.materials.filter(m=>MATERIAL_TYPES[p].includes(m.material_type));\n const refreshOwned=async()=>{const r=await apiFetch('/luthiery/materials/inventory');if(r.ok)setOwned((await r.json()).items)};
 const upgradeWorkshop=async()=>{if(!workshop?.next_upgrade_cost_cents||upgradingWorkshop)return;setUpgradingWorkshop(true);setMessage('');const r=await apiFetch('/luthiery/workshop/upgrade',{method:'POST'});const d=await r.json();setUpgradingWorkshop(false);if(!r.ok){setMessage(d.detail||'Workshop upgrade failed');return;}setWorkshop(d);setMessage('Luthier workshop upgraded successfully.');};
 const ready=!!shape&&PARTS.every(p=>parts[p]?.material_key)&&!!name.trim()&&!selectedShape?.locked;
 const estimated=useMemo(()=>{const chosen=PARTS.map(p=>cat.materials.find(m=>m.key===parts[p]?.material_key)).filter(Boolean) as Material[];
   if(!chosen.length)return null; const rarity={common:1,uncommon:2,rare:3,epic:4,legendary:5};return Math.round(chosen.reduce((n,m)=>n+(rarity[m.rarity as keyof typeof rarity]||1),0)/chosen.length*20);
 },[parts,cat.materials]);
 const statPreview=useMemo(()=>{const out:Record<string,number>={};PARTS.forEach(p=>{const m=cat.materials.find(x=>x.key===parts[p]?.material_key);if(!m?.stat_affinities_json)return;try{Object.entries(JSON.parse(m.stat_affinities_json)).forEach(([k,v])=>out[k]=(out[k]||0)+Number(v)*3)}catch{}});return out},[parts,cat.materials]);
 const rareSelected=PARTS.some(p=>{const m=cat.materials.find(x=>x.key===parts[p]?.material_key);return m?.rarity==='epic'||m?.rarity==='legendary'});
 const chooseMaterial=(p:Part,key:string)=>{setRareConfirmed(false);setParts(v=>({...v,[p]:{...v[p],material_key:key}}));};
 const chooseComponent=(p:Part,key:string)=>setParts(v=>({...v,[p]:{...v[p],component_key:key||undefined}}));
 const craft=async()=>{if(!ready)return;if(rareSelected&&!rareConfirmed){setMessage('Confirm use of rare materials before crafting.');return;}setBusy(true);setMessage('');setResult(null);
   const token=craftToken.current||(craftToken.current=globalThis.crypto?.randomUUID?.()||`craft-${Date.now()}`);
   const r=await apiFetch('/luthiery/craft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    request_token:token,name,instrument_type:type,shape_key:shape,selections:parts,finish_key:finish,primary_colour:primary,accent_colour:accent,hardware_colour:hardwareColour,surface_sheen:sheen})});
   const d=await r.json();setBusy(false);if(!r.ok){setMessage(d.detail||'Crafting failed');return;}setResult(d);setMessage('Instrument crafted successfully.');craftToken.current='';await refreshOwned();
 };
 const anchor=selectedShape?.visual?.anchors||{};
 return <section aria-labelledby="luthier-workshop-title" className="space-y-4">
  <header><h2 id="luthier-workshop-title">Luthier Workshop</h2><p>Build a unique instrument one part at a time.</p></header>
  {message&&<p role="status">{message}</p>}
  {workshop&&<div className="rounded border p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3" aria-label="Workshop quality">
    <div><h3 className="font-semibold">Workshop quality {workshop.quality_score}/100</h3><p className="text-sm">Upgrade level {workshop.upgrade_level}/5. Workshop quality contributes 10% of the instrument quality calculation.</p></div>
    {workshop.next_upgrade_cost_cents!=null?<button type="button" disabled={upgradingWorkshop} onClick={upgradeWorkshop} className="min-h-11">{upgradingWorkshop?'Upgrading…':`Upgrade workshop · ${(workshop.next_upgrade_cost_cents/100).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`}</button>:<span className="text-sm font-semibold">Maximum workshop quality</span>}
   </div>}
  <div className="grid gap-4 lg:grid-cols-[minmax(280px,1fr)_minmax(320px,1fr)]">
   <div className="rounded border p-3 sm:p-4 min-h-[360px] lg:min-h-[420px] lg:sticky lg:top-2 lg:self-start" aria-label="Live instrument preview">
    <div className="flex flex-wrap gap-2"><button onClick={()=>setType('guitar')} aria-pressed={type==='guitar'}>Guitar</button><button onClick={()=>setType('bass')} aria-pressed={type==='bass'}>Bass</button></div>
    <select value={shape} onChange={e=>setShape(e.target.value)} className="w-full mt-2 min-h-11">{shapes.map(s=><option key={s.key} value={s.key} disabled={s.locked}>{s.name}{s.locked?` — level ${s.required_level}`:''}</option>)}</select>
    <div className="relative mx-auto mt-4 aspect-[3/4] max-w-sm overflow-hidden rounded border bg-black/5">
      <div className="absolute inset-0 transition-transform flex items-center justify-center" style={{transform:`scale(${zoom}) rotate(${rotation}deg)`}}>
       <InstrumentPreview appearance={{instrument_type:type,shape_key:shape,primary_colour:primary,accent_colour:accent,hardware_colour:hardwareColour,surface_sheen:sheen}} label={selectedShape?.name||'Instrument preview'} />
       {PARTS.map(p=><button type="button" key={p} onClick={()=>setStep(p)} aria-label={`Edit ${p}`} className="absolute text-xs border rounded px-1 bg-white/80" style={{left:`${(anchor[p]?.x||.5)*100}%`,top:`${(anchor[p]?.y||.5)*100}%`,transform:'translate(-50%,-50%)',borderColor:p==='hardware'?hardwareColour:undefined}}>{p}{parts[p]?' ✓':''}</button>)}
      </div>
    </div>
    <div className="flex flex-wrap gap-2 mt-2"><button onClick={()=>setRotation(r=>r-15)} aria-label="Rotate left">↺</button><button onClick={()=>setRotation(r=>r+15)} aria-label="Rotate right">↻</button><button onClick={()=>setZoom(z=>Math.max(.75,z-.1))} aria-label="Zoom out">−</button><button onClick={()=>setZoom(z=>Math.min(1.6,z+.1))} aria-label="Zoom in">+</button><button onClick={()=>{setZoom(1);setRotation(0)}}>Reset view</button></div>
    <p className="text-sm">Estimated material potential: {estimated??'—'}/100</p>
    {!!Object.keys(statPreview).length&&<div className="text-sm" aria-label="Predicted characteristic changes">{Object.entries(statPreview).map(([k,v])=><span key={k} className="inline-block mr-2">{k.replaceAll('_',' ')} +{v}</span>)}</div>
   </div>
   <div>
    <nav className="flex flex-wrap gap-2" aria-label="Build steps">{[...PARTS,'finish'].map(p=><button key={p} onClick={()=>setStep(p as any)} aria-current={step===p?'step':undefined}>{p[0].toUpperCase()+p.slice(1)} {p!=='finish'&&parts[p]?.material_key?'✓':''}</button>)}</nav>
    {step!=='finish'?<div className="mt-4 space-y-3"><h3>{step[0].toUpperCase()+step.slice(1)}</h3>
      <label>Material<select className="w-full" value={parts[step]?.material_key||''} onChange={e=>chooseMaterial(step,e.target.value)}><option value="">Choose material</option>{materialsFor(step).map(m=><option key={m.key} value={m.key} disabled={m.locked||qty(m.key)<1}>{m.name} · {m.rarity} · owned {qty(m.key)} · ${(m.cost_cents/100).toFixed(2)}{m.locked?` · level ${m.required_level}`:''}</option>)}</select></label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" aria-label="Material thumbnails">{materialsFor(step).slice(0,9).map(m=><button key={m.key} disabled={m.locked||qty(m.key)<1} onClick={()=>chooseMaterial(step,m.key)} className="border rounded p-2 text-xs" aria-pressed={parts[step]?.material_key===m.key}><span className="block aspect-square rounded border mb-1" aria-hidden="true" style={{background:materialSwatch(m)}} />{m.name}</button>)}</div>
      <label>Component<select className="w-full" value={parts[step]?.component_key||''} onChange={e=>chooseComponent(step,e.target.value)}><option value="">Standard / none</option>{cat.components.filter(c=>c.part_type===step).map(c=><option key={c.key} value={c.key} disabled={c.locked}>{c.name}{c.locked?` · level ${c.required_level}`:''}</option>)}</select></label>
    </div>:<div className="mt-4 space-y-3"><label>Instrument name<input value={name} maxLength={80} onChange={e=>setName(e.target.value)} /></label>
      <label>Finish<select value={finish} onChange={e=>setFinish(e.target.value)}><option value="luthier.finish.solid">Solid</option><option value="luthier.finish.natural">Natural</option><option value="luthier.finish.transparent" disabled={finishingLevel<20}>Transparent{finishingLevel<20?' — Instrument Finishing 20':''}</option><option value="luthier.finish.metallic" disabled={finishingLevel<40}>Metallic{finishingLevel<40?' — Instrument Finishing 40':''}</option></select></label>
      <label>Primary colour<input type="color" value={primary} onChange={e=>setPrimary(e.target.value)} /></label><label>Accent colour<input type="color" value={accent} onChange={e=>setAccent(e.target.value)} /></label>
      <label>Hardware colour<input type="color" value={hardwareColour} onChange={e=>setHardwareColour(e.target.value)} /></label>
      <fieldset><legend>Surface sheen</legend>{(['matte','satin','gloss'] as const).map(x=><label key={x} className="mr-3"><input type="radio" checked={sheen===x} onChange={()=>setSheen(x)} /> {x}</label>)}</fieldset>
      {rareSelected&&<label className="block border rounded p-2"><input type="checkbox" checked={rareConfirmed} onChange={e=>setRareConfirmed(e.target.checked)} /> I understand this build will consume epic/legendary material.</label>
      <div className="rounded border p-3"><strong>Final build review</strong><p>{selectedShape?.name} · {PARTS.filter(p=>parts[p]?.material_key).length}/5 parts selected</p><p>Crafting consumes one owned material for each part.</p></div>
      <button className="w-full sm:w-auto min-h-11" disabled={!ready||busy} onClick={craft}>{busy?'Crafting…':'Craft instrument'}</button>
    </div>}
    {result&&<div className="mt-4 rounded border p-3"><h3>{result.name}</h3><p>{result.quality_tier} · quality {result.quality_score}</p><p>Maker serial: {result.serial_number}</p></div>}
   </div>
  </div>
 </section>
};
export default LuthieryWorkshop;

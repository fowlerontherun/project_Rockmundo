import React,{useEffect,useState} from 'react';
import {apiFetch} from '../../utils/api.js';
import InstrumentPreview from './InstrumentPreview';
type Item={id:number;name:string;serial_number:string;quality_tier:string;quality_score:number;condition_percent:number;locked:number;instrument_type:string;traits_json:string;workshop_snapshot_json:string};
const LuthieryInventory:React.FC=()=>{
 const [items,setItems]=useState<Item[]>([]),[detail,setDetail]=useState<any>(null),[equipped,setEquipped]=useState<number|null>(null),[message,setMessage]=useState(''),[salePrices,setSalePrices]=useState<Record<number,string>>({});
 const load=async()=>{const [a,b]=await Promise.all([apiFetch('/luthiery/crafted/inventory'),apiFetch('/luthiery/crafted/equipped')]);if(!a.ok||!b.ok)throw new Error('Unable to load crafted instruments');setItems((await a.json()).items);setEquipped((await b.json()).item?.id??null)};
 useEffect(()=>{load().catch(e=>setMessage(e.message))},[]);
 const open=async(id:number)=>{const r=await apiFetch('/luthiery/crafted/'+id);const d=await r.json();if(!r.ok){setMessage(d.detail||'Unable to load instrument');return}setDetail(d)};
 const equip=async(id:number)=>{const r=await apiFetch('/luthiery/crafted/'+id+'/equip',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(r.ok){setEquipped(id);setMessage('Instrument equipped.')}else setMessage((await r.json()).detail||'Unable to equip')};
 const lock=async(id:number,value:boolean)=>{const r=await apiFetch('/luthiery/crafted/'+id+'/lock',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({locked:value})});if(r.ok){await load();if(detail?.id===id)await open(id)}};
 const listForSale=async(id:number)=>{const cents=Math.round(Number(salePrices[id]||'')*100);if(!Number.isFinite(cents)||cents<=0){setMessage('Enter a valid sale price.');return}const r=await apiFetch('/luthiery/shops/mine/listings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item_id:id,price_cents:cents})});const d=await r.json();setMessage(r.ok?'Instrument listed for sale.':d.detail||'Unable to list instrument')};
 const maintain=async(id:number)=>{const r=await apiFetch('/luthiery/crafted/'+id+'/maintain',{method:'POST'});const d=await r.json();if(!r.ok){setMessage(d.detail||'Maintenance failed');return}setMessage('Maintenance complete.');await load();await open(id)};
 const parsed=(raw:string,fallback:any)=>{try{return JSON.parse(raw||'')}catch{return fallback}};
 return <section className="space-y-3" aria-labelledby="crafted-instruments-heading"><h2 id="crafted-instruments-heading">My Crafted Instruments</h2>{message&&<p role="status">{message}</p>}
  <div className="grid gap-2 md:grid-cols-2">{items.map(i=><article key={i.id} className="border rounded p-3"><h3>{i.name}</h3><p>{i.instrument_type} · {i.quality_tier} {i.quality_score} · condition {i.condition_percent}%</p><p className="text-sm">{i.serial_number}{i.locked?' · Locked':''}{equipped===i.id?' · Equipped':''}</p><div className="flex gap-2"><button onClick={()=>open(i.id)}>Details</button><button disabled={equipped===i.id} onClick={()=>equip(i.id)}>Equip</button><button onClick={()=>lock(i.id,!i.locked)}>{i.locked?'Unlock':'Favourite / lock'}</button>{i.condition_percent<100&&<button onClick={()=>maintain(i.id)}>Maintain</button>}<input aria-label="Sale price" type="number" min="0.01" step="0.01" placeholder="Sale price" value={salePrices[i.id]||''} onChange={e=>setSalePrices(v=>({...v,[i.id]:e.target.value}))}/><button disabled={!!i.locked||equipped===i.id} onClick={()=>listForSale(i.id)}>List for sale</button></div></article>)}</div>
  {detail&&<article className="border rounded p-4"><InstrumentPreview appearance={detail.appearance} label={`${detail.name} crafted instrument`} /><h3>{detail.name}</h3><p><strong>Maker serial:</strong> {detail.serial_number}</p><p><strong>Quality:</strong> {detail.quality_tier} · {detail.quality_score}</p><p><strong>Condition:</strong> {detail.condition_percent}%</p>
   <p><strong>Finish:</strong> {detail.finish_key.replace('luthier.finish.',' ')} · {parsed(detail.workshop_snapshot_json,{}).surface_sheen||'gloss'} · hardware {parsed(detail.workshop_snapshot_json,{}).hardware_colour||'#c0c0c0'}</p>
   <h4>Five-part specification</h4><ul>{detail.parts?.map((p:any)=><li key={p.part_type}><strong>{p.part_type}:</strong> {p.material_name||p.material_key}{p.component_name?' · '+p.component_name:''}</li>)}</ul>
   <h4>Traits</h4><p>{parsed(detail.traits_json,[]).join(', ')||'None'}</p>
   <h4>Provenance</h4><ul>{detail.events?.map((e:any,n:number)=><li key={n}>{e.created_at} · {e.event_type.replaceAll('_',' ')}</li>)}</ul>
  </article>}
 </section>
};
export default LuthieryInventory;

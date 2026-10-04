import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../utils/api.js';
type Material={key:string;name:string;material_type:string;rarity:string;cost_cents:number;required_level:number;locked:boolean};
type Owned={key:string;name:string;quantity:number};
const LuthieryMaterials:React.FC=()=>{
 const [materials,setMaterials]=useState<Material[]>([]); const [owned,setOwned]=useState<Owned[]>([]); const [message,setMessage]=useState('');
 const load=async()=>{const [a,b]=await Promise.all([apiFetch('/luthiery/catalogue'),apiFetch('/luthiery/materials/inventory')]);if(!a.ok||!b.ok)throw new Error('Unable to load Luthiery materials');setMaterials((await a.json()).materials);setOwned((await b.json()).items);};
 useEffect(()=>{load().catch(e=>setMessage(e.message));},[]);
 const buy=async(key:string)=>{setMessage('');const r=await apiFetch('/luthiery/supplier/purchase',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({material_key:key,quantity:1})});const d=await r.json();if(!r.ok){setMessage(d.detail||'Purchase failed');return;}setMessage('Material purchased successfully');await load();};
 const qty=(key:string)=>owned.find(i=>i.key===key)?.quantity??0;
 return <section aria-labelledby="luthiery-materials-heading"><h2 id="luthiery-materials-heading">Luthier Materials</h2>{message&&<p role="status">{message}</p>}<div className="space-y-2">{materials.map(m=><article key={m.key} className="border rounded p-3"><strong>{m.name}</strong><div>{m.rarity} · {m.material_type.replaceAll('_',' ')}</div><div>Owned: {qty(m.key)} · USD {(m.cost_cents/100).toFixed(2)}</div>{m.locked?<div>Unlocks at Luthiery level {m.required_level}</div>:<button onClick={()=>buy(m.key)}>Buy 1</button>}</article>)}</div></section>;
};
export default LuthieryMaterials;

import {useEffect,useState} from 'react';
import {ShieldCheck,Trash2} from 'lucide-react';
type Person={id:number;full_name:string;university_id:string};
type Gate={id:number;name:string};
type Permission={id:number;person_id:number;gate_id:number;enabled:boolean};
type Check={allowed:boolean;eligible:boolean;reason:string;identity_verification_required:boolean;gate_action:string};
async function api<T>(path:string,method='GET',body?:object):Promise<T>{
  const res=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
  if(res.status===204)return undefined as T;
  const result=await res.json();
  if(!res.ok)throw new Error(result.error||'Request failed');
  return result as T;
}
export default function Permissions({people,gates}:{people:Person[];gates:Gate[]}){
  const [items,setItems]=useState<Permission[]>([]);
  const [personId,setPersonId]=useState('');
  const [gateId,setGateId]=useState('');
  const [notice,setNotice]=useState('');
  const [result,setResult]=useState<Check|null>(null);
  const refresh=async()=>{try{setItems(await api<Permission[]>('/permissions'));}catch(e){setNotice(String(e));}};
  useEffect(()=>{void refresh();},[]);
  async function add(){
    try{
      await api('/permissions','POST',{person_id:Number(personId),gate_id:Number(gateId)});
      setNotice('Gate permission assigned');await refresh();
    }catch(e){setNotice(String(e));}
  }
  async function remove(id:number){
    try{await api('/permissions/'+id,'DELETE');setNotice('Permission revoked');setResult(null);await refresh();}
    catch(e){setNotice(String(e));}
  }
  async function check(){
    try{setResult(await api<Check>('/access/check','POST',{person_id:Number(personId),gate_id:Number(gateId)}));}
    catch(e){setNotice(String(e));}
  }
  return <><section className="panel"><h2>Gate access permissions</h2>
    <p className="empty">Permissions determine eligibility only. Identity must still be verified by an authorized operator; this page cannot open a gate.</p>
    <div className="form">
      <select aria-label="Person" value={personId} onChange={e=>{setPersonId(e.target.value);setResult(null);}}>
        <option value="">Select person</option>{people.map(p=><option key={p.id} value={p.id}>{p.full_name} ({p.university_id})</option>)}
      </select>
      <select aria-label="Gate" value={gateId} onChange={e=>{setGateId(e.target.value);setResult(null);}}>
        <option value="">Select gate</option>{gates.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}
      </select>
      <button disabled={!personId||!gateId} onClick={()=>void add()}>Assign permission</button>
      <button disabled={!personId||!gateId} onClick={()=>void check()}>Check eligibility</button>
    </div>
    {notice&&<p role="status">{notice}</p>}
    {result&&<p role="status" className="empty"><ShieldCheck size={16}/> {result.eligible?'Eligible under gate policy':'Not eligible under gate policy'} — Identity verification required. Gate action: none.</p>}
  </section>
  <section className="panel"><h2>Assigned permissions</h2>
    <div className="table-wrap"><table><thead><tr><th>Person</th><th>Gate</th><th>Status</th><th>Action</th></tr></thead><tbody>
      {items.map(p=><tr key={p.id}><td>{people.find(x=>x.id===p.person_id)?.full_name||p.person_id}</td>
        <td>{gates.find(x=>x.id===p.gate_id)?.name||p.gate_id}</td><td>{p.enabled?'Enabled':'Disabled'}</td>
        <td><button className="secondary" onClick={()=>void remove(p.id)}><Trash2 size={14}/> Revoke</button></td></tr>)}
    </tbody></table>{items.length===0&&<p className="empty">No permissions assigned.</p>}</div>
  </section></>;
}

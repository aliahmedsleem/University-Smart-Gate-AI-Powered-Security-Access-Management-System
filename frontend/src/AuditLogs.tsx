import {useMemo,useState} from 'react';
import {Download,Filter} from 'lucide-react';
import {apiFetch} from './api';
type Person={id:number;full_name:string};
type Gate={id:number;name:string};
type Event={id:number;person_id:number;gate_id:number;direction:string;decision:string;created_at:string};
export default function AuditLogs({events,people,gates}:{events:Event[];people:Person[];gates:Gate[]}){
  const [person,setPerson]=useState('');
  const [gate,setGate]=useState('');
  const [direction,setDirection]=useState('');
  const filtered=useMemo(()=>events.filter(e=>(!person||e.person_id===Number(person))&&(!gate||e.gate_id===Number(gate))&&(!direction||e.direction===direction)),[events,person,gate,direction]);
  const params=new URLSearchParams();
  if(person)params.set('person_id',person);
  if(gate)params.set('gate_id',gate);
  if(direction)params.set('direction',direction);
  async function exportCsv(){try{const res=await apiFetch('/events/export.csv'+(params.size?'?'+params.toString():''));if(!res.ok)throw new Error('Export failed');const blob=await res.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='access-events.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){setExportError(String(e));}}
  const [exportError,setExportError]=useState('');
  return <><div className="audit-toolbar"><Filter size={18}/>
    <select aria-label="Filter person" value={person} onChange={e=>setPerson(e.target.value)}><option value="">All people</option>{people.map(p=><option key={p.id} value={p.id}>{p.full_name}</option>)}</select>
    <select aria-label="Filter gate" value={gate} onChange={e=>setGate(e.target.value)}><option value="">All gates</option>{gates.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}</select>
    <select aria-label="Filter direction" value={direction} onChange={e=>setDirection(e.target.value)}><option value="">All directions</option><option value="entry">Entry</option><option value="exit">Exit</option></select>
    <button className="audit-download" onClick={()=>void exportCsv()}><Download size={16}/> Export CSV</button>
  </div>
  {exportError&&<p role="alert">{exportError}</p>}
  <p className="empty">Showing {filtered.length} of {events.length} most recent loaded events. CSV export uses server-side filters (up to 5,000 events).</p>
  <div className="table-wrap"><table><thead><tr><th>Time</th><th>Person</th><th>Gate</th><th>Direction</th><th>Decision</th></tr></thead>
    <tbody>{filtered.map(e=><tr key={e.id}><td>{new Date(e.created_at).toLocaleString()}</td><td>{people.find(p=>p.id===e.person_id)?.full_name||'#'+e.person_id}</td><td>{gates.find(g=>g.id===e.gate_id)?.name||'#'+e.gate_id}</td><td>{e.direction}</td><td><span className="tag">{e.decision}</span></td></tr>)}</tbody>
  </table>{!filtered.length&&<p className="empty">No matching events.</p>}</div></>;
}

import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Activity, Camera, DoorOpen, ShieldCheck, Users, ScrollText, Plus, RefreshCw} from 'lucide-react';
import './styles.css';

type Person={id:number;university_id:string;full_name:string;department:string;role:string;status:string};
type Gate={id:number;name:string;location:string;enabled:boolean};
type Event={id:number;person_id:number;gate_id:number;direction:string;decision:string;created_at:string};
const api=async<T,>(path:string,options?:RequestInit):Promise<T>=>{
  const res=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...options?.headers}});
  const data=await res.json();
  if(!res.ok)throw new Error(data.error||'Request failed');
  return data as T;
};
function App(){
  const [people,setPeople]=useState<Person[]>([]);
  const [gates,setGates]=useState<Gate[]>([]);
  const [events,setEvents]=useState<Event[]>([]);
  const [page,setPage]=useState('Overview');
  const [notice,setNotice]=useState('');
  const [form,setForm]=useState({university_id:'',full_name:'',department:'',role:'student'});
  const [gateName,setGateName]=useState('');
  const [entry,setEntry]=useState({person_id:'',gate_id:'',direction:'entry'});
  const [status,setStatus]=useState('Connecting');
  const refresh=async()=>{
    try{
      const [p,g,e]=await Promise.all([api<Person[]>('/people'),api<Gate[]>('/gates'),api<Event[]>('/events')]);
      setPeople(p);setGates(g);setEvents(e);setStatus('Online');
    }catch(err){setStatus('Backend offline');setNotice(String(err));}
  };
  useEffect(()=>{void refresh();},[]);
  async function submitPerson(ev:React.FormEvent){ev.preventDefault();try{await api('/people',{method:'POST',body:JSON.stringify(form)});setForm({university_id:'',full_name:'',department:'',role:'student'});setNotice('Person registered (identity metadata only)');await refresh();}catch(e){setNotice(String(e));}}
  async function submitGate(ev:React.FormEvent){ev.preventDefault();try{await api('/gates',{method:'POST',body:JSON.stringify({name:gateName})});setGateName('');await refresh();}catch(e){setNotice(String(e));}}
  async function submitEvent(ev:React.FormEvent){ev.preventDefault();try{await api('/events',{method:'POST',body:JSON.stringify({...entry,person_id:Number(entry.person_id),gate_id:Number(entry.gate_id)})});setNotice('Operator event logged for review');await refresh();}catch(e){setNotice(String(e));}}
  const nav=[['Overview',Activity],['People',Users],['Gates',DoorOpen],['Access Logs',ScrollText],['Cameras',Camera]] as const;
  return <div className="shell">
    <aside className="sidebar"><div className="brand"><ShieldCheck size={30}/><div><b>SMART GATE</b><small>UNIVERSITY SECURITY</small></div></div><div className="menu">{nav.map(([name,Icon])=><button key={name} className={page===name?'active':''} onClick={()=>setPage(name)}><Icon size={18}/>{name}</button>)}</div><div className="side-bottom">Prototype • Operator controlled<br/>No automatic gate opening</div></aside>
    <main><header><div><small>SECURITY OPERATIONS / {page.toUpperCase()}</small><h1>{page}</h1></div><div className="actions"><span className={'status '+(status==='Online'?'ok':'')}>● {status}</span><button className="secondary" onClick={()=>void refresh()}><RefreshCw size={16}/> Refresh</button></div></header>
    {notice&&<div className="notice" role="status">{notice}<button onClick={()=>setNotice('')}>×</button></div>}
    {page==='Overview'&&<><div className="stats"><article><span>Registered People</span><strong>{people.length}</strong><Users/></article><article><span>Configured Gates</span><strong>{gates.length}</strong><DoorOpen/></article><article><span>Recorded Events</span><strong>{events.length}</strong><ScrollText/></article><article><span>Camera Streams</span><strong>0</strong><Camera/></article></div><section className="panel"><h2>Recent access activity</h2><Events events={events} people={people} gates={gates}/></section><section className="panel note"><h2>Development mode</h2><p>Camera preview runs locally through the Python camera service. Facial enrollment, recognition and electronic gate actuation are not enabled. All access events are operator-entered and marked for manual review.</p></section></>}
    {page==='People'&&<><section className="panel"><h2>Register identity metadata</h2><form className="form" onSubmit={submitPerson}><input required placeholder="University ID" value={form.university_id} onChange={e=>setForm({...form,university_id:e.target.value})}/><input required placeholder="Full name" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/><input required placeholder="Department" value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option value="student">Student</option><option value="staff">Staff</option><option value="faculty">Faculty</option><option value="visitor">Visitor</option></select><button><Plus size={16}/> Add person</button></form></section><section className="panel"><h2>People directory</h2><div className="table-wrap"><table><thead><tr><th>Name</th><th>University ID</th><th>Department</th><th>Role</th><th>Status</th></tr></thead><tbody>{people.map(p=><tr key={p.id}><td>{p.full_name}</td><td>{p.university_id}</td><td>{p.department}</td><td>{p.role}</td><td>{p.status}</td></tr>)}</tbody></table>{!people.length&&<p className="empty">No people registered.</p>}</div></section></>}
    {page==='Gates'&&<><section className="panel"><h2>Configure gate</h2><form className="form" onSubmit={submitGate}><input required placeholder="Gate name" value={gateName} onChange={e=>setGateName(e.target.value)}/><button><Plus size={16}/> Add gate</button></form></section><section className="panel"><h2>Registered gates</h2>{gates.length?gates.map(g=><div className="list-row" key={g.id}><DoorOpen/> <b>{g.name}</b><span>{g.enabled?'Configured':'Disabled'}</span></div>):<p className="empty">No gates configured.</p>}</section></>}
    {page==='Access Logs'&&<><section className="panel"><h2>Manual event entry</h2><form className="form" onSubmit={submitEvent}><select required value={entry.person_id} onChange={e=>setEntry({...entry,person_id:e.target.value})}><option value="">Select person</option>{people.map(p=><option key={p.id} value={p.id}>{p.full_name}</option>)}</select><select required value={entry.gate_id} onChange={e=>setEntry({...entry,gate_id:e.target.value})}><option value="">Select gate</option>{gates.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}</select><select value={entry.direction} onChange={e=>setEntry({...entry,direction:e.target.value})}><option value="entry">Entry</option><option value="exit">Exit</option></select><button>Record for review</button></form></section><section className="panel"><h2>Access event log</h2><Events events={events} people={people} gates={gates}/></section></>}
    {page==='Cameras'&&<section className="panel"><h2>Camera preview service</h2><div className="camera-placeholder"><Camera size={42}/><strong>Local preview is available</strong><span>Run camera_service/preview.py from the computer connected to the webcam.</span><code>python camera_service/preview.py --source 0</code></div></section>}
    </main></div>
}
function Events({events,people,gates}:{events:Event[];people:Person[];gates:Gate[]}){return <div className="table-wrap"><table><thead><tr><th>Time</th><th>Person</th><th>Gate</th><th>Direction</th><th>Decision</th></tr></thead><tbody>{events.map(e=><tr key={e.id}><td>{new Date(e.created_at).toLocaleString()}</td><td>{people.find(p=>p.id===e.person_id)?.full_name||'#'+e.person_id}</td><td>{gates.find(g=>g.id===e.gate_id)?.name||'#'+e.gate_id}</td><td>{e.direction}</td><td><span className="tag">{e.decision}</span></td></tr>)}</tbody></table>{!events.length&&<p className="empty">No access events yet.</p>}</div>}
createRoot(document.getElementById('root')!).render(<App/>);

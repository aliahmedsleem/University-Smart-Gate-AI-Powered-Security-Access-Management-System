import {useEffect,useState} from 'react';
import {api} from './api';

type Person={id:number;full_name:string;university_id:string};
export default function ReferencePhoto({people}:{people:Person[]}){
  const [personId,setPersonId]=useState('');
  const [file,setFile]=useState<File|null>(null);
  const [consent,setConsent]=useState(false);
  const [saved,setSaved]=useState<number[]>([]);
  const [message,setMessage]=useState('');
  const [busy,setBusy]=useState(false);
  const [engine,setEngine]=useState('checking');
  const refresh=async()=>{try{const d=await api<{person_ids:number[];engine:string}>('/vision/enrollments');setSaved(d.person_ids);setEngine(d.engine);}catch(e){setMessage(String(e));}};
  useEffect(()=>{void refresh();},[]);
  async function submit(){
    if(!file||!personId||!consent||busy)return;
    setBusy(true);setMessage('');
    try{
      if(file.size>1_500_000)throw new Error('Choose a JPEG under 1.5 MB');
      if(!['image/jpeg','image/jpg'].includes(file.type))throw new Error('JPEG photo required');
      const image=await new Promise<string>((resolve,reject)=>{
        const reader=new FileReader();
        reader.onload=()=>resolve(String(reader.result));
        reader.onerror=()=>reject(new Error('Cannot read photo'));
        reader.readAsDataURL(file);
      });
      await api('/vision/enroll',{method:'POST',body:JSON.stringify({person_id:Number(personId),image,consent_confirmed:true})});
      setMessage('Reference photo processed and template saved. Recognition remains advisory.');
      setFile(null);await refresh();
    }catch(e){setMessage(String(e));}
    finally{setBusy(false);}
  }
  async function remove(){
    if(!personId||!window.confirm('Delete the stored biometric template?'))return;
    setBusy(true);
    try{await api('/vision/enroll/'+personId,{method:'DELETE'});setMessage('Reference template deleted');await refresh();}
    catch(e){setMessage(String(e));}
    finally{setBusy(false);}
  }
  return <section className="panel">
    <h2>Reference photo — one image per person</h2>
    <p role="status">Recognition engine: <b>{engine}</b>. {engine!=='sface'?'Install pretrained models with backend/scripts/download_face_models.py and restart the backend. Legacy LBPH is unreliable across poses.':'Pretrained SFace is active; accuracy must still be validated.'}</p>
    <p className="empty">No multi-angle capture or camera enrollment needed. Upload one authorized JPEG from a university record; the backend extracts one face and stores a local template, not the original photo. A frontal reference photo is recommended.</p>
    <div className="form">
      <select aria-label="Select person for reference photo" value={personId} onChange={e=>{setPersonId(e.target.value);setMessage('');}}>
        <option value="">Select registered person</option>
        {people.map(p=><option key={p.id} value={p.id}>{p.full_name} ({p.university_id}) {saved.includes(p.id)?'· photo registered':''}</option>)}
      </select>
      <input aria-label="Reference JPEG photo" type="file" accept="image/jpeg" onChange={e=>setFile(e.target.files?.[0]||null)}/>
      <button disabled={busy||!personId||!file||!consent||saved.includes(Number(personId))} onClick={()=>void submit()} type="button">{busy?'Processing...':'Process reference photo'}</button>
      <button className="secondary" disabled={busy||!saved.includes(Number(personId))} onClick={()=>void remove()} type="button">Remove reference</button>
    </div>
    <label className="consent-row"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I confirm the university has appropriate authorization and informed consent for biometric processing of this photo.</label>
    {message&&<p role="status">{message}</p>}
    <p className="camera-disclaimer">SFace is used when installed; otherwise legacy LBPH remains. Neither can infer hidden 3D geometry or guarantee recognition from every angle. No automatic gate control or autonomous identity updates.</p>
  </section>;
}

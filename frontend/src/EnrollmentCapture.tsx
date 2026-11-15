import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,RotateCcw,ShieldCheck} from 'lucide-react';
import {api} from './api';
type Quality={width:number;height:number;brightness:number;contrast:number;message:string;ok:boolean};
function inspect(canvas:HTMLCanvasElement):Quality{
  const ctx=canvas.getContext('2d',{willReadFrequently:true});
  if(!ctx)throw new Error('Canvas unavailable');
  const {width,height}=canvas;
  const pixels=ctx.getImageData(0,0,width,height).data;
  let sum=0,sumSq=0,n=0;
  for(let i=0;i<pixels.length;i+=16){
    const v=.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2];
    sum+=v;sumSq+=v*v;n++;
  }
  const brightness=sum/n,contrast=Math.sqrt(Math.max(0,sumSq/n-brightness*brightness));
  const ok=width>=640&&height>=480&&brightness>=55&&brightness<=205&&contrast>=28;
  const message=width<640||height<480?'Resolution too low':brightness<55?'Scene too dark':brightness>205?'Scene too bright':contrast<28?'Low image contrast':'Basic image checks passed';
  return {width,height,brightness:Math.round(brightness),contrast:Math.round(contrast),message,ok};
}
/** Local-only consent-driven capture. Never persists, uploads or recognizes a face. */
export default function EnrollmentCapture({people}:{people:{id:number;full_name:string;university_id:string}[]}){
  const video=useRef<HTMLVideoElement>(null);
  const stream=useRef<MediaStream|null>(null);
  const [personId,setPersonId]=useState('');
  const [enrolled,setEnrolled]=useState<number[]>([]);
  const [notice,setNotice]=useState('');
  const refresh=async()=>{try{const data=await api<{person_ids:number[]}>('/vision/enrollments');setEnrolled(data.person_ids);}catch(e){setError(String(e));}};
  useEffect(()=>{void refresh();},[]);
  const [consent,setConsent]=useState(false);
  const [running,setRunning]=useState(false);
  const [quality,setQuality]=useState<Quality|null>(null);
  const [error,setError]=useState('');
  const [preview,setPreview]=useState('');
  const [captures,setCaptures]=useState<string[]>([]);
  const poses=['Front','Slight left','Slight right','Left profile','Right profile'];
  const stop=()=>{
    stream.current?.getTracks().forEach(t=>t.stop());
    stream.current=null;
    if(video.current)video.current.srcObject=null;
    setRunning(false);
  };
  const clear=()=>{setPreview('');setQuality(null);};
  const reset=()=>{clear();setCaptures([]);};
  const start=async()=>{
    if(!consent)return;
    setError('');clear();stop();
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera requires localhost or HTTPS');
      const media=await navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'}});
      stream.current=media;
      if(video.current){video.current.srcObject=media;await video.current.play();}
      setRunning(true);
    }catch(e){stop();setError(String(e));}
  };
  const capture=()=>{
    if(!video.current||!running)return;
    const v=video.current;
    if(!v.videoWidth||!v.videoHeight){setError('Video frame not ready');return;}
    const canvas=document.createElement('canvas');
    canvas.width=v.videoWidth;canvas.height=v.videoHeight;
    const ctx=canvas.getContext('2d');
    if(!ctx)return;
    ctx.drawImage(v,0,0);
    const check=inspect(canvas);
    setQuality(check);
    const shot=canvas.toDataURL('image/jpeg',.8);
    setPreview(shot);
    if(check.ok&&captures.length<poses.length)setCaptures(old=>[...old,shot]);
    stop();
  };
  async function enroll(){
    if(!consent||captures.length<3||!personId)return;
    try{await api('/vision/enroll',{method:'POST',body:JSON.stringify({person_id:Number(personId),images:captures,consent_confirmed:true})});setNotice('Multi-pose enrollment saved for selected person');reset();await refresh();}
    catch(e){setError(String(e));}
  }
  async function remove(){if(!personId||!window.confirm('Delete face enrollment for this person?'))return;try{await api('/vision/enroll/'+personId,{method:'DELETE'});setNotice('Enrollment deleted');await refresh();}catch(e){setError(String(e));}}
  useEffect(()=>()=>{stream.current?.getTracks().forEach(t=>t.stop());},[]);
  return <section className="panel">
    <h2>Enrollment capture — local quality check</h2>
    <p className="empty">Select a registered person. Exactly one detectable face is required. Duplicate-looking faces are blocked for manual review. This prototype stores a local biometric template and is not suitable for automatic gate decisions.</p>
    <div className="form"><select aria-label="Person to enroll" value={personId} onChange={e=>{setPersonId(e.target.value);reset();}}><option value="">Select registered person</option>{people.map(p=><option key={p.id} value={p.id}>{p.full_name} ({p.university_id}) {enrolled.includes(p.id)?'· enrolled':''}</option>)}</select><button disabled={!personId||!enrolled.includes(Number(personId))} onClick={()=>void remove()} type="button">Delete enrollment</button></div>
    <label className="consent-row"><input type="checkbox" checked={consent} onChange={e=>{setConsent(e.target.checked);if(!e.target.checked){stop();reset();}}}/>
      I have the subject's informed permission to take a temporary camera image for this local demonstration.</label>
    <p role="status">Pose captures: {captures.length}/5. Next: {poses[captures.length]||"Ready to enroll"}. Capture at least front, slightly left and slightly right. Keep one face in frame. These are operator-guided prompts, not automatic pose validation.</p>
    <div className="camera-controls">
      {!running?<button disabled={!consent} onClick={()=>void start()}><Camera size={16}/> Start capture camera</button>:<>
        <button onClick={capture}><ShieldCheck size={16}/> Capture & inspect</button>
        <button className="secondary" onClick={stop}><CameraOff size={16}/> Stop</button>
      </>}
      {preview&&captures.length<5&&<button className="secondary" onClick={()=>{clear();void start();}} disabled={!consent}><RotateCcw size={16}/> Next pose</button>}
      {captures.length>0&&<button className="secondary" onClick={reset}>Reset all captures</button>}
      {captures.length>=3&&<button disabled={!personId||!consent||enrolled.includes(Number(personId))} onClick={()=>void enroll()}>Enroll {captures.length} poses</button>}
    </div>
    <div className="live-camera">
      <video ref={video} autoPlay playsInline muted style={{display:running?'block':'none'}}/>
      {preview&&!running&&<img src={preview} alt="Temporary local capture" style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
      {!running&&!preview&&<div className="camera-overlay"><Camera size={34}/> Camera is off</div>}
    </div>
    {captures.length>0&&<p role="status">Captured: {poses.slice(0,captures.length).join(' · ')}. Each accepted image is held in browser memory until enrollment or reset.</p>}
    {quality&&<p role="status">Image quality: <b>{quality.message}</b> — {quality.width}×{quality.height}; brightness {quality.brightness}; contrast {quality.contrast}. {quality.ok?'Basic checks passed; pose captured for pending enrollment.':'Retake in better lighting.'}</p>}
    {notice&&<p role="status">{notice}</p>}
    {error&&<p role="alert" className="camera-error">{error}</p>}
    <p className="camera-disclaimer">On enrollment, a processed biometric face template is saved locally on the backend. The original photo is not saved. Obtain explicit informed consent and restrict backend access. No liveness verification.</p>
  </section>;
}

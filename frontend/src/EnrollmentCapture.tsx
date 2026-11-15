import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,RotateCcw,ShieldCheck} from 'lucide-react';
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
export default function EnrollmentCapture(){
  const video=useRef<HTMLVideoElement>(null);
  const stream=useRef<MediaStream|null>(null);
  const [consent,setConsent]=useState(false);
  const [running,setRunning]=useState(false);
  const [quality,setQuality]=useState<Quality|null>(null);
  const [error,setError]=useState('');
  const [preview,setPreview]=useState('');
  const stop=()=>{
    stream.current?.getTracks().forEach(t=>t.stop());
    stream.current=null;
    if(video.current)video.current.srcObject=null;
    setRunning(false);
  };
  const clear=()=>{setPreview('');setQuality(null);};
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
    setQuality(inspect(canvas));
    setPreview(canvas.toDataURL('image/jpeg',.8));
    stop();
  };
  useEffect(()=>()=>{stream.current?.getTracks().forEach(t=>t.stop());},[]);
  return <section className="panel">
    <h2>Enrollment capture — local quality check</h2>
    <p className="empty">Select an enrolled person in the People directory first. This is a camera and image-quality prototype only; it does not detect a face, create biometric templates, upload photos or link images to a person.</p>
    <label className="consent-row"><input type="checkbox" checked={consent} onChange={e=>{setConsent(e.target.checked);if(!e.target.checked){stop();clear();}}}/>
      I have the subject's informed permission to take a temporary camera image for this local demonstration.</label>
    <div className="camera-controls">
      {!running?<button disabled={!consent} onClick={()=>void start()}><Camera size={16}/> Start capture camera</button>:<>
        <button onClick={capture}><ShieldCheck size={16}/> Capture & inspect</button>
        <button className="secondary" onClick={stop}><CameraOff size={16}/> Stop</button>
      </>}
      {preview&&<button className="secondary" onClick={()=>{clear();void start();}} disabled={!consent}><RotateCcw size={16}/> Retake</button>}
      {preview&&<button className="secondary" onClick={clear}>Discard image</button>}
    </div>
    <div className="live-camera">
      <video ref={video} autoPlay playsInline muted style={{display:running?'block':'none'}}/>
      {preview&&!running&&<img src={preview} alt="Temporary local capture" style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
      {!running&&!preview&&<div className="camera-overlay"><Camera size={34}/> Camera is off</div>}
    </div>
    {quality&&<p role="status">Image quality: <b>{quality.message}</b> — {quality.width}×{quality.height}; brightness {quality.brightness}; contrast {quality.contrast}. {quality.ok?'Basic checks passed, not a facial enrollment.':'Retake in better lighting.'}</p>}
    {error&&<p role="alert" className="camera-error">{error}</p>}
    <p className="camera-disclaimer">No images are saved or transmitted. Closing this page discards the capture. Quality checks cannot confirm identity, liveness or face presence.</p>
  </section>;
}

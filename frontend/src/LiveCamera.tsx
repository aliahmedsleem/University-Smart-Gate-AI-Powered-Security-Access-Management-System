import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,ShieldAlert} from 'lucide-react';

/** Browser-local camera preview. No image data is uploaded or stored. */
export default function LiveCamera(){
  const video=useRef<HTMLVideoElement>(null);
  const stream=useRef<MediaStream|null>(null);
  const [active,setActive]=useState(false);
  const [error,setError]=useState('');
  const [devices,setDevices]=useState<MediaDeviceInfo[]>([]);
  const [deviceId,setDeviceId]=useState('');
  async function enumerate(){
    if(!navigator.mediaDevices?.enumerateDevices)return;
    try{setDevices((await navigator.mediaDevices.enumerateDevices()).filter(d=>d.kind==='videoinput'));}
    catch{ /* device list is optional */ }
  }
  function stop(){
    stream.current?.getTracks().forEach(t=>t.stop());
    stream.current=null;
    if(video.current)video.current.srcObject=null;
    setActive(false);
  }
  async function start(id=deviceId){
    stop();setError('');
    if(!navigator.mediaDevices?.getUserMedia){
      setError('Camera access requires localhost or HTTPS in a supported browser.');
      return;
    }
    try{
      const media=await navigator.mediaDevices.getUserMedia({
        audio:false,video:id?{deviceId:{exact:id},width:{ideal:1280},height:{ideal:720}}:{width:{ideal:1280},height:{ideal:720}}
      });
      stream.current=media;
      if(video.current){video.current.srcObject=media;await video.current.play();}
      setActive(true);await enumerate();
    }catch(e){stop();setError(e instanceof Error?e.message:String(e));}
  }
  useEffect(()=>()=>stop(),[]);
  return <div>
    <div className="camera-controls">
      <select aria-label="Camera device" value={deviceId} onChange={e=>{setDeviceId(e.target.value);if(active)void start(e.target.value);}}>
        <option value="">Default camera</option>
        {devices.map(d=><option key={d.deviceId} value={d.deviceId}>{d.label||'Camera '+d.deviceId.slice(0,6)}</option>)}
      </select>
      {!active?<button onClick={()=>void start()}><Camera size={16}/> Start camera</button>:<button onClick={stop}><CameraOff size={16}/> Stop camera</button>}
    </div>
    <div className="live-camera">
      <video ref={video} autoPlay playsInline muted aria-label="Local live camera preview"/>
      {!active&&<div className="camera-overlay"><Camera size={34}/><span>Camera is off</span></div>}
      {active&&<span className="camera-live-label">● LIVE · LOCAL ONLY</span>}
    </div>
    {error&&<p className="camera-error" role="alert">{error}</p>}
    <p className="camera-disclaimer"><ShieldAlert size={16}/> Preview only. Frames remain in your browser; no facial identification, recording or gate activation.</p>
  </div>;
}

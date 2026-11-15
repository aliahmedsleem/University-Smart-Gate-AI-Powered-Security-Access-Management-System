import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,ShieldAlert} from 'lucide-react';
import {api} from './api';
type Detection={box:number[];recognized:boolean;person_id:number|null;name:string};
type Activity={name:string;person_id:number|null;recognized:boolean;timestamp:string;status:string};
export default function GateMonitor(){
  const video=useRef<HTMLVideoElement>(null);
  const overlay=useRef<HTMLCanvasElement>(null);
  const stream=useRef<MediaStream|null>(null);
  const busy=useRef(false);
  const [running,setRunning]=useState(false);
  const [error,setError]=useState('');
  const [detections,setDetections]=useState<Detection[]>([]);
  const [activity,setActivity]=useState<Activity[]>([]);
  const [count,setCount]=useState(0);
  function stop(){
    stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;
    if(video.current)video.current.srcObject=null;
    setRunning(false);setDetections([]);setCount(0);
    const ctx=overlay.current?.getContext('2d');
    if(ctx&&overlay.current)ctx.clearRect(0,0,overlay.current.width,overlay.current.height);
  }
  async function start(){
    setError('');stop();
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera requires localhost or HTTPS');
      const media=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:960},height:{ideal:540}},audio:false});
      stream.current=media;
      if(video.current){video.current.srcObject=media;await video.current.play();}
      setRunning(true);
    }catch(e){setError(String(e));stop();}
  }
  useEffect(()=>{if(!running)return;let cancelled=false;
    const timer=setInterval(async()=>{
      const v=video.current;if(!v||!v.videoWidth||busy.current||cancelled)return;
      busy.current=true;
      try{
        const c=document.createElement('canvas');
        const scale=Math.min(1,720/v.videoWidth);
        c.width=Math.round(v.videoWidth*scale);c.height=Math.round(v.videoHeight*scale);
        c.getContext('2d')?.drawImage(v,0,0,c.width,c.height);
        const image=c.toDataURL('image/jpeg',.7);
        const data=await api<{detections:Detection[];face_count:number}>('/vision/recognize',{method:'POST',body:JSON.stringify({image})});
        if(cancelled)return;
        setDetections(data.detections);setCount(data.face_count);
        const canvas=overlay.current;
        if(canvas){
          canvas.width=c.width;canvas.height=c.height;
          const ctx=canvas.getContext('2d');
          if(ctx){
            ctx.clearRect(0,0,c.width,c.height);ctx.lineWidth=3;ctx.font='bold 16px sans-serif';
            for(const d of data.detections){
              const [x,y,w,h]=d.box;const color=d.recognized?'#65e7b2':'#ff9e81';
              ctx.strokeStyle=color;ctx.strokeRect(x,y,w,h);
              const label=d.name;const tw=ctx.measureText(label).width+12;
              ctx.fillStyle='#101d31dd';ctx.fillRect(x,Math.max(0,y-25),tw,25);
              ctx.fillStyle=color;ctx.fillText(label,x+6,Math.max(17,y-7));
            }
          }
        }
        setActivity(await api<Activity[]>('/vision/activity'));
      }catch(e){if(!cancelled)setError(String(e));}
      finally{busy.current=false;}
    },1500);
    return()=>{cancelled=true;clearInterval(timer);};
  },[running]);
  useEffect(()=>()=>{stream.current?.getTracks().forEach(t=>t.stop());},[]);
  const unknown=detections.filter(d=>!d.recognized).length;
  return <div className="monitor-layout">
    <section className="panel monitor-primary">
      <div className="monitor-head"><div><h2>Live entrance monitoring</h2><p className="empty">Face recognition candidates · local camera</p></div>
        <div className="camera-controls">{running?<button onClick={stop}><CameraOff size={16}/> Stop</button>:<button onClick={()=>void start()}><Camera size={16}/> Start monitoring</button>}</div>
      </div>
      <div className="monitor-video">
        <video ref={video} autoPlay playsInline muted style={{display:running?'block':'none'}}/>
        <canvas ref={overlay} style={{display:running?'block':'none'}}/>
        {!running&&<div className="camera-overlay"><Camera size={42}/> Start camera to monitor passing people</div>}
      </div>
      <div className="monitor-metrics"><span>Faces visible: <b>{count}</b></span><span>Recognized candidates: <b>{detections.filter(d=>d.recognized).length}</b></span><span>Unknown: <b>{unknown}</b></span></div>
      {unknown>0&&<div className="monitor-alert" role="alert"><ShieldAlert size={20}/> Unknown face detected — operator review required. Do not infer threat or deny access solely from recognition.</div>}
      {error&&<p className="camera-error" role="alert">{error}</p>}
      <p className="camera-disclaimer">Advisory identification only. No liveness check, physical passage verification or automatic gate action. Recognition may be inaccurate.</p>
    </section>
    <aside className="panel monitor-activity"><h2>Live recognition activity</h2><p className="empty">Updates while the camera is running</p>
      {activity.map((a,i)=><div className="monitor-activity-row" key={a.timestamp+'-'+i}><span className={a.recognized?'monitor-dot ok':'monitor-dot warn'}/><div><b>{a.name}</b><small>{a.recognized?'Possible match':'Unknown · review'} · {new Date(a.timestamp).toLocaleTimeString()}</small></div></div>)}
      {!activity.length&&<p className="empty">No detections yet.</p>}
    </aside>
  </div>;
}

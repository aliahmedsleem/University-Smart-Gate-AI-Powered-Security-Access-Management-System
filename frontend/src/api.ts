/** In-memory bearer token: never persisted in localStorage or cookies. */
let apiToken='';
export function setApiToken(token:string){apiToken=token.trim();}
export function hasApiToken(){return apiToken.length>0;}
export function clearApiToken(){apiToken='';}
export async function apiFetch(path:string,options:RequestInit={}):Promise<Response>{
  const headers=new Headers(options.headers);
  if(apiToken)headers.set('Authorization','Bearer '+apiToken);
  if(options.body&&!headers.has('Content-Type'))headers.set('Content-Type','application/json');
  return fetch('/api'+path,{...options,headers,cache:'no-store'});
}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
  const res=await apiFetch(path,options);
  if(res.status===204)return undefined as T;
  const data=await res.json();
  if(!res.ok)throw new Error(data.error||'Request failed');
  return data as T;
}

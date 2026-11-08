// A dedicated worker keeps model loading/inference off the reading interface.
let extractor,queue=Promise.resolve(),latest=0;
self.onmessage=({data})=>{
 latest=data.id;
 queue=queue.catch(()=>{}).then(async()=>{
  if(data.id!==latest)return;
  try{
   if(!extractor){
    self.postMessage({id:data.id,kind:'progress',stage:'Loading the meaning-search model…'});
    const {pipeline,env}=await import('./vendor/transformers.min.js');
    env.allowRemoteModels=false;env.allowLocalModels=true;
    env.localModelPath=new URL('./models/',import.meta.url).href;
    env.useBrowserCache=false;env.useFSCache=false;
    env.backends.onnx.wasm.wasmPaths=new URL('./vendor/',import.meta.url).href;
    env.backends.onnx.wasm.numThreads=1;env.backends.onnx.wasm.proxy=false;
    extractor=await pipeline('feature-extraction','minilm',{dtype:'q8',device:'wasm',progress_callback:p=>{
     if(p.status==='progress'&&p.file?.endsWith('.onnx'))self.postMessage({id:latest,kind:'progress',stage:'Downloading the model…'+(Number.isFinite(p.progress)?' '+Math.round(p.progress)+'%':'')});
    }});
   }
   if(data.id!==latest)return;
   self.postMessage({id:data.id,kind:'progress',stage:'Finding related passages…'});
   const result=await extractor(data.text,{pooling:'mean',normalize:true,truncation:true,max_length:256});
   if(data.id===latest)self.postMessage({id:data.id,kind:'result',embedding:Array.from(result.data)});
  }catch(error){extractor=null;self.postMessage({id:data.id,kind:'error',message:'Meaning search could not load. Keyword results are still available.'});}
 });
};

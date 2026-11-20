const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const palette = ["#aa95ff", "#ff9aab", "#76e2c8", "#f9c978", "#83bcff", "#e6a6f7"];
let initialized = false;
let activeLab = "regression";
const reg = {points:[],weights:[0,0,0,0,0],step:0,running:true,drag:-1,raf:0,last:0};
const boundary = {points:[],classIndex:0,algorithm:"knn",param:5,model:null};
const clusters = {points:[],centroids:[],k:3,iteration:0,auto:null,dataset:"blobs"};
const attention = {selected:0};

function canvasPoint(canvas,event) {
  const rect = canvas.getBoundingClientRect();
  return {x:(event.clientX-rect.left)/rect.width*canvas.width,y:(event.clientY-rect.top)/rect.height*canvas.height};
}
function plotGrid(ctx,w,h) {
  ctx.fillStyle="#101523";ctx.fillRect(0,0,w,h);
  ctx.strokeStyle="#293248";ctx.lineWidth=1;
  for(let x=0;x<=w;x+=60){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
  for(let y=0;y<=h;y+=54){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
}
function dot(ctx,x,y,color,r=7) {ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.lineWidth=2;ctx.strokeStyle="#101523";ctx.stroke();}
function rand(min,max){return min+Math.random()*(max-min);}
function normal(){return (Math.random()+Math.random()+Math.random()+Math.random()-2)/2;}

function regCoordinates(p){return {x:p.x/360-1,y:1-p.y/215};}
function regPrediction(x){const degree=Number($("#degree").value);let sum=0;for(let j=0;j<=degree;j++)sum+=reg.weights[j]*Math.pow(x,j);return sum;}
function regLoss(){
  if(!reg.points.length)return 0;
  let sum=0;
  for(const p of reg.points){const c=regCoordinates(p);const d=regPrediction(c.x)-c.y;sum+=d*d;}
  return sum/reg.points.length;
}
function regStep(){
  if(!reg.points.length)return;
  const degree=Number($("#degree").value),grad=Array(degree+1).fill(0),rate=Number($("#learningRate").value);
  for(const p of reg.points){const c=regCoordinates(p),error=regPrediction(c.x)-c.y;for(let j=0;j<=degree;j++)grad[j]+=2*error*Math.pow(c.x,j)/reg.points.length;}
  for(let j=0;j<=degree;j++)reg.weights[j]-=rate*grad[j];
  reg.step++;
  if(!Number.isFinite(regLoss())||Math.abs(regLoss())>1e9){reg.running=false;$("#regRun").textContent="Resume training";}
}
function drawRegression(){
  const c=$("#regressionCanvas"),ctx=c.getContext("2d");plotGrid(ctx,c.width,c.height);
  ctx.strokeStyle="#4d5066";ctx.lineWidth=2;ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(0,c.height/2);ctx.lineTo(c.width,c.height/2);ctx.stroke();ctx.setLineDash([]);
  ctx.strokeStyle="#b6a4ff";ctx.lineWidth=4;ctx.beginPath();
  for(let px=0;px<c.width;px+=3){const x=px/360-1,y=regPrediction(x),py=(1-y)*215;if(px===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);}ctx.stroke();
  reg.points.forEach((p,i)=>dot(ctx,p.x,p.y,i===reg.drag?"#fff":palette[0],8));
  const loss=regLoss();
  $("#regLoss").textContent=loss>1e6?"Exploding":loss.toFixed(4);
  $("#regSteps").textContent=String(reg.step);
  $("#regInsight").textContent=loss>10?"Learning rate too high: the updates overshoot and loss explodes. Lower the rate or reset.":reg.step>120?"The curve is settling. Try moving a point to see the optimizer adapt.":"Each step nudges the weights in the direction that reduces loss.";
}
function animateRegression(time){
  if(reg.running && time-reg.last>45){for(let i=0;i<3;i++)regStep();drawRegression();reg.last=time;}
  reg.raf=requestAnimationFrame(animateRegression);
}
function setRegressionPreset(type){
  reg.weights=[0,0,0,0,0];reg.step=0;reg.running=true;$("#regRun").textContent="Pause training";
  if(type==="linear"){reg.points=Array.from({length:15},(_,i)=>({x:55+i*43,y:330-i*14+normal()*24}));$("#degree").value="1";$("#learningRate").value="0.08";}
  else {reg.points=Array.from({length:17},(_,i)=>{const x=-.85+i*.106;return {x:(x+1)*360,y:(1-(.6*x*x-.38+normal()*.13))*215};});$("#degree").value="2";$("#learningRate").value=type==="explode"?"1.5":"0.08";}
  $("#degreeValue").textContent=$("#degree").value;$("#lrValue").textContent=Number($("#learningRate").value).toFixed(3);
  drawRegression();
}
function setupRegression(){
  const c=$("#regressionCanvas");
  c.addEventListener("pointerdown",(e)=>{const p=canvasPoint(c,e);const i=reg.points.findIndex((q)=>Math.hypot(q.x-p.x,q.y-p.y)<18);if(i>=0)reg.drag=i;else{reg.points.push(p);reg.drag=reg.points.length-1;}c.setPointerCapture(e.pointerId);drawRegression();});
  c.addEventListener("pointermove",(e)=>{if(reg.drag<0)return;const p=canvasPoint(c,e);reg.points[reg.drag]={x:Math.max(0,Math.min(c.width,p.x)),y:Math.max(0,Math.min(c.height,p.y))};drawRegression();});
  const release=()=>{reg.drag=-1;};c.addEventListener("pointerup",release);c.addEventListener("pointercancel",release);
  $("#learningRate").addEventListener("input",()=>{$("#lrValue").textContent=Number($("#learningRate").value).toFixed(3);});
  $("#degree").addEventListener("input",()=>{reg.weights=[0,0,0,0,0];reg.step=0;$("#degreeValue").textContent=$("#degree").value;drawRegression();});
  $("#regRun").addEventListener("click",()=>{reg.running=!reg.running;$("#regRun").textContent=reg.running?"Pause training":"Resume training";});
  $("#regReset").addEventListener("click",()=>setRegressionPreset("curve"));
  $$("[data-reg-preset]").forEach((b)=>b.addEventListener("click",()=>setRegressionPreset(b.dataset.regPreset)));
  setRegressionPreset("curve");reg.raf=requestAnimationFrame(animateRegression);
}

function sigmoid(z){return 1/(1+Math.exp(-Math.max(-30,Math.min(30,z))));}
function normXY(p){return [(p.x/360-1),(1-p.y/215)];}
function trainLogistic(points){
  const w=[0,0,0],lambda=(Number($("#boundaryParam").value)-1)/100;
  for(let epoch=0;epoch<250;epoch++){
    const g=[0,0,0];for(const p of points){const [x,y]=normXY(p),diff=sigmoid(w[0]+w[1]*x+w[2]*y)-p.classIndex;g[0]+=diff;g[1]+=diff*x;g[2]+=diff*y;}
    for(let j=0;j<3;j++)w[j]-=.7*(g[j]/points.length+(j?lambda*w[j]:0));
  }
  return w;
}
function neuralPredict(model,x,y){
  let z=model.b;
  for(let i=0;i<model.hidden;i++){const h=Math.tanh(model.w1[i][0]*x+model.w1[i][1]*y+model.b1[i]);z+=h*model.w2[i];}
  return sigmoid(z);
}
function trainNeural(points,hidden){
  const model={hidden,w1:[],b1:[],w2:[],b:0};
  for(let i=0;i<hidden;i++){model.w1.push([rand(-1,1),rand(-1,1)]);model.b1.push(rand(-.3,.3));model.w2.push(rand(-1,1));}
  for(let epoch=0;epoch<320;epoch++){
    for(const p of points){
      const [x,y]=normXY(p),hs=model.w1.map((w,i)=>Math.tanh(w[0]*x+w[1]*y+model.b1[i]));
      const output=sigmoid(model.b+hs.reduce((s,h,i)=>s+h*model.w2[i],0)),dz=output-p.classIndex,oldW2=model.w2.slice();
      model.b-=.14*dz;
      for(let i=0;i<hidden;i++){model.w2[i]-=.14*dz*hs[i];const dh=dz*oldW2[i]*(1-hs[i]*hs[i]);model.w1[i][0]-=.14*dh*x;model.w1[i][1]-=.14*dh*y;model.b1[i]-=.14*dh;}
    }
  }
  return model;
}
function predictClass(x,y){
  if(!boundary.points.length)return .5;
  if(boundary.algorithm==="knn"){
    const k=Math.min(boundary.param,boundary.points.length);
    const nearest=boundary.points.map((p)=>{const q=normXY(p);return {d:(q[0]-x)**2+(q[1]-y)**2,c:p.classIndex};}).sort((a,b)=>a.d-b.d).slice(0,k);
    return nearest.reduce((s,p)=>s+p.c,0)/k;
  }
  if(boundary.algorithm==="logistic"){const w=boundary.model;return sigmoid(w[0]+w[1]*x+w[2]*y);}
  return neuralPredict(boundary.model,x,y);
}
function rebuildBoundary(){
  boundary.algorithm=$("#boundaryAlgorithm").value;boundary.param=Number($("#boundaryParam").value);
  if(boundary.points.length){boundary.model=boundary.algorithm==="logistic"?trainLogistic(boundary.points):boundary.algorithm==="neural"?trainNeural(boundary.points,boundary.param):null;}
  drawBoundary();
}
function drawBoundary(){
  const c=$("#boundaryCanvas"),ctx=c.getContext("2d");plotGrid(ctx,c.width,c.height);
  if(boundary.points.length){const cell=12;for(let y=0;y<c.height;y+=cell)for(let x=0;x<c.width;x+=cell){const p=predictClass((x+cell/2)/360-1,1-(y+cell/2)/215);ctx.fillStyle=p>=.5?"rgba(255,154,171,.20)":"rgba(170,149,255,.22)";ctx.fillRect(x,y,cell,cell);}}
  boundary.points.forEach((p)=>dot(ctx,p.x,p.y,palette[p.classIndex],8));
  $("#boundaryPoints").textContent=String(boundary.points.length);
  const accurate=boundary.points.filter((p)=>{const q=normXY(p);return Number(predictClass(q[0],q[1])>=.5)===p.classIndex;}).length;
  $("#boundaryAccuracy").textContent=boundary.points.length?Math.round(accurate/boundary.points.length*100)+"%":"—";
  $("#boundaryInsight").textContent=boundary.algorithm==="knn"?"KNN votes with nearby examples. Raise K to smooth the boundary.":boundary.algorithm==="logistic"?"Logistic regression learns one straight dividing line. It cannot solve XOR.":"A small neural network combines nonlinear hidden units to bend the boundary.";
}
function boundaryPreset(type){
  boundary.points=[];
  if(type==="diagonal")for(let i=0;i<30;i++){const classIndex=i%2;boundary.points.push({x:classIndex?rand(390,640):rand(75,320),y:classIndex?rand(80,340):rand(90,360),classIndex});}
  if(type==="xor")for(let i=0;i<40;i++){const corner=i%4,x=(corner%2?500:200)+normal()*75,y=(corner<2?115:315)+normal()*55;boundary.points.push({x,y,classIndex:(corner===1||corner===2)?1:0});}
  rebuildBoundary();
}
function setupBoundary(){
  const c=$("#boundaryCanvas");
  c.addEventListener("pointerdown",(e)=>{const p=canvasPoint(c,e);boundary.points.push({...p,classIndex:boundary.classIndex});rebuildBoundary();});
  $("#boundaryAlgorithm").addEventListener("change",()=>{const alg=$("#boundaryAlgorithm").value;const slider=$("#boundaryParam");slider.max=alg==="knn"?"15":alg==="logistic"?"10":"12";slider.min=alg==="knn"?"1":alg==="logistic"?"1":"2";slider.step=alg==="knn"?"2":"1";slider.value=alg==="knn"?"5":alg==="logistic"?"3":"6";$("#boundaryParamLabel").firstChild.textContent=alg==="knn"?"Neighbors (K) ":alg==="logistic"?"Regularization ":"Hidden units ";$("#boundaryParamValue").textContent=slider.value;rebuildBoundary();});
  $("#boundaryParam").addEventListener("input",()=>{$("#boundaryParamValue").textContent=$("#boundaryParam").value;rebuildBoundary();});
  $$("[data-class]").forEach((b)=>b.addEventListener("click",()=>{boundary.classIndex=Number(b.dataset.class);$$("[data-class]").forEach((x)=>x.classList.toggle("active",x===b));}));
  $$("[data-boundary-preset]").forEach((b)=>b.addEventListener("click",()=>boundaryPreset(b.dataset.boundaryPreset)));
  boundaryPreset("diagonal");
}

function datasetPoints(type){
  const pts=[];
  for(let i=0;i<90;i++){
    let x,y;
    if(type==="blobs"){const centers=[[175,130],[520,125],[350,320]],center=centers[i%3];x=center[0]+normal()*115;y=center[1]+normal()*90;}
    else if(type==="rings"){const ring=i%2,r=ring?155:70,a=rand(0,Math.PI*2);x=360+Math.cos(a)*(r+normal()*24);y=215+Math.sin(a)*(r+normal()*24);}
    else{x=rand(35,685);y=rand(35,395);}
    pts.push({x:Math.max(15,Math.min(705,x)),y:Math.max(15,Math.min(415,y)),cluster:-1});
  }
  return pts;
}
function nearestCentroid(p){let best=0,bestDist=Infinity;clusters.centroids.forEach((c,i)=>{const d=(p.x-c.x)**2+(p.y-c.y)**2;if(d<bestDist){bestDist=d;best=i;}});return best;}
function clusterInertia(){return clusters.points.reduce((sum,p)=>{const c=clusters.centroids[p.cluster<0?nearestCentroid(p):p.cluster];return sum+(p.x-c.x)**2+(p.y-c.y)**2;},0)/clusters.points.length;}
function clusterStep(){
  clusters.points.forEach((p)=>p.cluster=nearestCentroid(p));
  clusters.centroids.forEach((c,i)=>{const group=clusters.points.filter((p)=>p.cluster===i);if(group.length){c.x=group.reduce((s,p)=>s+p.x,0)/group.length;c.y=group.reduce((s,p)=>s+p.y,0)/group.length;}});
  clusters.iteration++;drawClusters();
}
function drawClusters(){
  const c=$("#clusterCanvas"),ctx=c.getContext("2d");plotGrid(ctx,c.width,c.height);
  if(clusters.centroids.length)for(let y=0;y<c.height;y+=18)for(let x=0;x<c.width;x+=18){const i=nearestCentroid({x:x+9,y:y+9});ctx.fillStyle=palette[i]+"12";ctx.fillRect(x,y,18,18);}
  clusters.points.forEach((p)=>dot(ctx,p.x,p.y,p.cluster<0?"#9ba3b9":palette[p.cluster],5));
  clusters.centroids.forEach((p,i)=>{ctx.fillStyle=palette[i];ctx.font="bold 30px system-ui";ctx.fillText("✦",p.x-14,p.y+10);});
  $("#clusterIteration").textContent=String(clusters.iteration);
  $("#clusterInertia").textContent=clusterInertia().toFixed(0);
  $("#clusterInsight").textContent=clusters.iteration>5?"Centroids have usually stabilized. Regenerate or change K to try another solution.":"Each step assigns points, then moves each centroid to the center of its group.";
}
function resetClusters(){
  stopClusterAuto();clusters.dataset=$("#clusterDataset").value;clusters.k=Number($("#clusterK").value);clusters.points=datasetPoints(clusters.dataset);clusters.centroids=Array.from({length:clusters.k},()=>({x:rand(80,640),y:rand(70,360)}));clusters.iteration=0;drawClusters();
}
function stopClusterAuto(){if(clusters.auto){clearInterval(clusters.auto);clusters.auto=null;$("#clusterAuto").textContent="Auto-run";}}
function setupClusters(){
  $("#clusterK").addEventListener("input",()=>{$("#clusterKValue").textContent=$("#clusterK").value;resetClusters();});
  $("#clusterDataset").addEventListener("change",resetClusters);
  $("#clusterStep").addEventListener("click",clusterStep);
  $("#clusterAuto").addEventListener("click",()=>{if(clusters.auto)stopClusterAuto();else{clusters.auto=setInterval(clusterStep,650);$("#clusterAuto").textContent="Pause";}});
  $("#clusterReset").addEventListener("click",resetClusters);
  resetClusters();
}

function tokenFeatures(token){
  const t=token.toLowerCase(),v=Array(12).fill(0);
  for(let i=0;i<t.length;i++){const code=t.charCodeAt(i);v[code%12]+=1;v[(code+i*3)%12]+=.45;}
  const norm=Math.hypot(...v)||1;return v.map((x)=>x/norm);
}
function similarity(a,b){return a.reduce((s,x,i)=>s+x*b[i],0);}
function renderAttention(){
  const tokens=$("#attentionText").value.trim().split(/\s+/).filter(Boolean).slice(0,12);
  attention.selected=Math.min(attention.selected,Math.max(0,tokens.length-1));
  const list=$("#tokenList");list.replaceChildren();
  tokens.forEach((token,i)=>{const b=document.createElement("button");b.type="button";b.textContent=token;b.classList.toggle("active",i===attention.selected);b.addEventListener("click",()=>{attention.selected=i;renderAttention();});list.append(b);});
  const bars=$("#attentionBars");bars.replaceChildren();
  const features=tokens.map(tokenFeatures),query=features[attention.selected]||Array(12).fill(0),sharpness=Number($("#attentionSharpness").value);
  const raw=features.map((f)=>Math.exp(sharpness*similarity(query,f))),total=raw.reduce((a,b)=>a+b,0)||1;
  const weights=raw.map((x)=>x/total);
  weights.forEach((weight,i)=>{const row=document.createElement("div");row.className="attention-row";const name=document.createElement("span");name.textContent=tokens[i];const bar=document.createElement("div");bar.className="bar";const fill=document.createElement("span");fill.style.width=(weight*100)+"%";bar.append(fill);const val=document.createElement("strong");val.textContent=Math.round(weight*100)+"%";row.append(name,bar,val);bars.append(row);});
  $("#attentionCount").textContent=String(tokens.length);
  const highest=weights.length?weights.indexOf(Math.max(...weights)):-1;$("#attentionTop").textContent=highest>=0?tokens[highest]:"—";
}
function setupAttention(){
  $("#attentionText").addEventListener("input",renderAttention);
  $("#attentionSharpness").addEventListener("input",()=>{$("#attentionSharpnessValue").textContent=$("#attentionSharpness").value;renderAttention();});
  const phrases={robot:"the curious robot learns from data",animals:"the cat watches the small kitten play",code:"python model learns patterns from python data"};
  $$("[data-attention-preset]").forEach((b)=>b.addEventListener("click",()=>{$("#attentionText").value=phrases[b.dataset.attentionPreset];attention.selected=0;renderAttention();}));
  renderAttention();
}

export function activateLab(name){
  activeLab=name;
  $$("[data-lab]").forEach((b)=>b.setAttribute("aria-selected",String(b.dataset.lab===name)));
  $$(".lab-panel").forEach((p)=>p.hidden=p.id!=="panel-"+name);
  if(name!=="clusters")stopClusterAuto();
  if(name==="regression")drawRegression();
  if(name==="boundary")drawBoundary();
  if(name==="clusters")drawClusters();
}
export function initPlayground(){
  if(initialized){activateLab(activeLab);return;}
  initialized=true;setupRegression();setupBoundary();setupClusters();setupAttention();activateLab("regression");
}

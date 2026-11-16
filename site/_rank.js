var D=__DATA__;
function E(s){return String(s==null?'':s).replace(
 /[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;',
 '>':'&gt;','"':'&quot;'}[c];});}
function n(v,d){if(v==null||v!==v)return '--';
 return Number(v).toFixed(d==null?0:d);}
function edge(x){
 if(x.ar==null)return '<td>--</td>';
 var e=x.ar-x.rk;
 var c=e>8?'up':(e<-8?'dn':'');
 return '<td class="'+c+'">'+(e>0?'+':'')+e.toFixed(0)+'</td>';}
function row(x){
 var z=x.pp>0?'':' class=zero';
 return '<tr'+z+'><td>'+x.rk+'</td>'
 +'<td class=l><span class=nm data-pid="'+E(x.id)+'">'
 +E(x.nm)+'</span> <span class=tm>('+E(x.tm)+')</span>'
 +(x.st?'<span class=tag>'+E(x.st)+'</span>':'')+'</td>'
 +'<td class=l><span class="pos '+E(x.ps)+'">'
 +E(x.ps)+x.pr+'</span></td>'
 +'<td>'+(x.by?x.by:'--')+'</td>'
 +'<td>'+n(x.pp,2)+'</td>'
 +'<td>'+n(x.sz,0)+'</td>'
 +'<td>'+(x.vp>0?'+':'')+n(x.vp,2)+'</td>'
 +'<td>'+n(x.ad,1)+'</td>'
 +'<td>'+n(x.sa,1)+'</td>'
 +'<td>'+n(x.ea,1)+'</td>'
 +edge(x)+'</tr>';}
function draw(){
 var q=document.getElementById('q').value.toLowerCase();
 var p=document.getElementById('p').value;
 var out=[],i;
 for(i=0;i<D.length;i++){
  var x=D[i];
  if(p&&x.ps!==p)continue;
  if(q&&(x.nm+' '+x.tm).toLowerCase().indexOf(q)<0)continue;
  out.push(x);}
 document.getElementById('cnt').textContent=
  out.length+' of '+D.length+' players';
 var h='';
 for(i=0;i<out.length;i++)h+=row(out[i]);
 document.getElementById('tb').innerHTML=h;}
document.getElementById('q').addEventListener('input',draw);
document.getElementById('p').addEventListener('change',draw);
document.addEventListener('click',function(ev){
 var t=ev.target;
 while(t&&t.getAttribute){
  var v=t.getAttribute('data-pid');
  if(v){window.open('player.html#id='+v,'_blank');return;}
  t=t.parentNode;}});
draw();

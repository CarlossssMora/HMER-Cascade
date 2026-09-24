// Verifica las predicciones SAN y separa anotación de rasterización.
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname,'../..');
const resultDir = path.join(__dirname,'resultados');
const years=['2014','2016','2019'];

function csvRows(file) {
  const content=fs.readFileSync(file,'utf8');
  let quoted=false,field='',fields=[],records=[];
  for(let i=0;i<content.length;i++) {
    const char=content[i];
    if(char==='"') {
      if(quoted&&content[i+1]==='"'){field+='"';i++;}
      else quoted=!quoted;
    } else if(char===','&&!quoted){fields.push(field);field='';}
    else if((char==='\r'||char==='\n')&&!quoted){
      if(char==='\r'&&content[i+1]==='\n')i++;
      fields.push(field);field='';
      if(fields.some(value=>value!==''))records.push(fields);
      fields=[];
    } else field+=char;
  }
  if(quoted)throw new Error(`CSV inválido: ${file}`);
  if(field||fields.length){fields.push(field);records.push(fields);}
  const header=records.shift();
  return records.map(values=>Object.fromEntries(header.map((name,index)=>[name,values[index]??''])));
}

function captions(file) {
  return new Map(fs.readFileSync(file,'utf8').trim().split(/\r?\n/).map(line=>{
    const tab=line.indexOf('\t');
    return [line.slice(0,tab),line.slice(tab+1).trim().replace(/\s+/g,' ')];
  }));
}

function normalize(value) {
  return value.trim().split(/\s+/).filter(token=>token&&token!=='\\limits').join(' ');
}

function mean(values) {
  return values.reduce((sum,value)=>sum+value,0)/values.length;
}

function pairedAccuracy(left,right,gt,normalized) {
  const a=normalized?normalize(left)===normalize(gt):left.trim()===gt.trim();
  const b=normalized?normalize(right)===normalize(gt):right.trim()===gt.trim();
  return a?(b?'both':'only_bttr'):(b?'only_posformer':'neither');
}

const summary={years:{},checks:{}};
const allRows={};
for(const year of years) {
  const file=path.join(resultDir,`san_bttr_${year}.csv`);
  const rows=csvRows(file);
  const bttr=captions(path.join(root,'data/BTTR',year,'caption.txt'));
  const pos=captions(path.join(root,'data/Modelo2',year,'caption.txt'));
  if(rows.length!==bttr.size)throw new Error(`Conteo incorrecto: ${year}`);
  const seen=new Set();
  const counts={year,requested:rows.length,valid:0,errors:[],
    bttr_exact:0,bttr_no_limits:0,posformer_exact:0,posformer_no_limits:0,
    mean_time_ms:null};
  const times=[];
  for(const row of rows) {
    const id=row.sample_id;
    if(seen.has(id)||!bttr.has(id)||!pos.has(id))throw new Error(`ID inesperado: ${year}/${id}`);
    seen.add(id);
    if(row.ground_truth_bttr!==bttr.get(id)||row.ground_truth_posformer!==pos.get(id))
      throw new Error(`Etiqueta inesperada: ${year}/${id}`);
    if(row.status!=='ok') {counts.errors.push({id,error:row.error});continue;}
    counts.valid++;
    const expected={
      bttr_exact:Number(row.san_prediction.trim()===bttr.get(id)),
      bttr_no_limits:Number(normalize(row.san_prediction)===normalize(bttr.get(id))),
      posformer_exact:Number(row.san_prediction.trim()===pos.get(id)),
      posformer_no_limits:Number(normalize(row.san_prediction)===normalize(pos.get(id))),
    };
    for(const [key,value] of Object.entries(expected)) {
      if(Number(row[key])!==value)throw new Error(`Resultado incorrecto: ${year}/${id}/${key}`);
      counts[key]+=value;
    }
    times.push(Number(row.time_ms));
  }
  counts.mean_time_ms=mean(times);
  summary.years[year]=counts;
  allRows[year]=new Map(rows.map(row=>[row.sample_id,row]));
}

// 2014 usa exactamente los mismos BMP que el benchmark original de SAN.
const old2014=csvRows(path.join(root,'Cascada/01_seleccion/resultados/benchmark_crohme_2014.csv'));
let same2014=0;
for(const row of old2014) {
  const current=allRows['2014'].get(row.sample_id);
  if(!current||current.status!=='ok')continue;
  if(current.san_prediction===row.san_prediction)same2014++;
}
summary.checks.predictions_equal_to_2014_benchmark=same2014;
summary.checks.previous_2014_rows=old2014.length;

// En 2019 se comparan dos rasterizaciones con los mismos IDs, checkpoint y GT PosFormer.
const old2019=csvRows(path.join(resultDir,'benchmark_crohme_2019_common_images.csv'));
const comparison={samples:old2019.length,predictions_equal:0,
  raw:{both:0,only_bttr:0,only_posformer:0,neither:0},
  no_limits:{both:0,only_bttr:0,only_posformer:0,neither:0}};
for(const row of old2019) {
  const current=allRows['2019'].get(row.sample_id);
  if(!current||current.status!=='ok'||row.status!=='ok')
    throw new Error(`Falta predicción 2019: ${row.sample_id}`);
  if(row.ground_truth!==current.ground_truth_posformer)
    throw new Error(`GT PosFormer 2019 distinto: ${row.sample_id}`);
  if(current.san_prediction===row.san_prediction)comparison.predictions_equal++;
  comparison.raw[pairedAccuracy(current.san_prediction,row.san_prediction,row.ground_truth,false)]++;
  comparison.no_limits[pairedAccuracy(current.san_prediction,row.san_prediction,row.ground_truth,true)]++;
}
summary.checks.image_source_effect_2019=comparison;

const output=path.join(resultDir,'san_bttr_summary.json');
fs.writeFileSync(output,JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));

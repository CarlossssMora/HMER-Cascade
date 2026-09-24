// Resume Exact Match con el mismo ground truth y la misma normalización para ambos modelos.
const fs = require('fs');
const path = require('path');

const input = process.argv[2] || path.join(__dirname,'resultados/benchmark_crohme_2019_common_images.csv');
const outputDir = path.dirname(input);
const stem = path.basename(input,'.csv');
const expectedCaptions = path.resolve(__dirname,'../../data/Modelo2/2019/caption.txt');

function parseCsv(content) {
  const records=[];
  let fields=[],field='',quoted=false;
  for(let i=0;i<content.length;i++) {
    const char=content[i];
    if(char==='"') {
      if(quoted && content[i+1]==='"'){field+='"';i++;}
      else quoted=!quoted;
    } else if(char===',' && !quoted){fields.push(field);field='';}
    else if((char==='\n'||char==='\r') && !quoted){
      if(char==='\r' && content[i+1]==='\n')i++;
      fields.push(field);field='';
      if(fields.some(value=>value!==''))records.push(fields);
      fields=[];
    } else field+=char;
  }
  if(quoted)throw new Error('CSV con comillas sin cerrar');
  if(field || fields.length){fields.push(field);records.push(fields);}
  const header=records.shift();
  return records.map(fields=>Object.fromEntries(header.map((name,index)=>[name,fields[index]??''])));
}

function csv(value) {
  const string=String(value??'');
  return /[",\r\n]/.test(string)?`"${string.replace(/"/g,'""')}"`:string;
}

function normalize(value) {
  return value.trim().split(/\s+/).filter(token=>token && token!=='\\limits').join(' ');
}

function counts(rows,mode) {
  const result={both_correct:0,san_only:0,posformer_only:0,both_wrong:0};
  for(const row of rows)result[row[mode]]++;
  result.san_correct=result.both_correct+result.san_only;
  result.posformer_correct=result.both_correct+result.posformer_only;
  result.oracle_correct=result.both_correct+result.san_only+result.posformer_only;
  return result;
}

const rows=parseCsv(fs.readFileSync(input,'utf8'));
const valid=rows.filter(row=>row.status==='ok');
const errors=rows.filter(row=>row.status!=='ok');
const expectedIds=new Set(fs.readFileSync(expectedCaptions,'utf8').trim().split(/\r?\n/)
  .map(line=>line.slice(0,line.indexOf('\t'))));
if(expectedIds.size!==1199)throw new Error('El archivo de etiquetas 2019 cambió');
const detail=[];
const changes={san_gained:0,san_lost:0,posformer_gained:0,posformer_lost:0};
for(const row of valid) {
  const gt=normalize(row.ground_truth);
  const san=normalize(row.san_prediction);
  const pos=normalize(row.posformer_prediction);
  const sanCorrect=san===gt;
  const posCorrect=pos===gt;
  const rawSan=row.san_prediction.trim()===row.ground_truth.trim();
  const rawPos=row.posformer_prediction.trim()===row.ground_truth.trim();
  if(!expectedIds.has(row.sample_id) || row.image_file!==`${row.sample_id}.bmp`)
    throw new Error(`Imagen o ID inesperado: ${row.sample_id}`);
  if(Number(row.san_correct)!==Number(rawSan) || Number(row.posformer_correct)!==Number(rawPos))
    throw new Error(`Las banderas del benchmark no coinciden: ${row.sample_id}`);
  if(sanCorrect && !rawSan)changes.san_gained++;
  if(!sanCorrect && rawSan)changes.san_lost++;
  if(posCorrect && !rawPos)changes.posformer_gained++;
  if(!posCorrect && rawPos)changes.posformer_lost++;
  const outcome=(a,b)=>a?(b?'both_correct':'san_only'):(b?'posformer_only':'both_wrong');
  detail.push({id:row.sample_id,raw_outcome:outcome(rawSan,rawPos),
    normalized_outcome:outcome(sanCorrect,posCorrect),
    raw_san_correct:rawSan,raw_posformer_correct:rawPos,
    normalized_san_correct:sanCorrect,normalized_posformer_correct:posCorrect,
    ground_truth:row.ground_truth,san_prediction:row.san_prediction,
    posformer_prediction:row.posformer_prediction});
}
const uniqueIds=new Set(valid.map(row=>row.sample_id));
if(uniqueIds.size!==valid.length)throw new Error('ID duplicado en resultados');
if(rows.length!==1199)throw new Error(`Se esperaban 1199 muestras y hay ${rows.length}`);
if(errors.length===0 && [...expectedIds].some(id=>!uniqueIds.has(id)))
  throw new Error('Faltan IDs del test de PosFormer 2019');
const summary={input,requested:rows.length,valid:valid.length,errors:errors.map(row=>({id:row.sample_id,error:row.error})),
  posformer_resized:valid.filter(row=>row.posformer_resized==='1').length,
  raw:counts(detail,'raw_outcome'),normalized:counts(detail,'normalized_outcome'),changes};
const fields=['id','raw_outcome','normalized_outcome','raw_san_correct','raw_posformer_correct',
  'normalized_san_correct','normalized_posformer_correct','ground_truth','san_prediction','posformer_prediction'];
fs.writeFileSync(path.join(outputDir,`${stem}_normalized.csv`),
  fields.join(',')+'\n'+detail.map(row=>fields.map(field=>csv(row[field])).join(',')).join('\n')+'\n');
fs.writeFileSync(path.join(outputDir,`${stem}_summary.json`),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));

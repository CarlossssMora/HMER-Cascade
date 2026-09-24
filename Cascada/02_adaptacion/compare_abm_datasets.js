// Compara ABM con conjuntos locales sin ejecutar constructores de sus pickle.
const fs = require('fs');
const path = require('path');
const {readPickleArrays,bmpPixels,captions,withoutLimits,sha} = require('./compare_tamer_datasets');

const root = path.resolve(__dirname,'../..');
const outDir = path.join(__dirname,'resultados');
const abmDir = path.join(root,'data/ABM');

function abmFiles(year) {
  if (year === 'train') return {
    labels:path.join(abmDir,'train_caption.txt'),
    images:path.join(abmDir,'offline-train.pkl'),
  };
  return {
    labels:path.join(abmDir,`test-caption-${year}.txt`),
    images:path.join(abmDir,`offline-${year}-test.pkl`),
  };
}

function referenceFiles(year,reference) {
  if (reference === 'SAN') return {
    labels:path.join(root,'data/Modelo1/2014/test_caption.txt'),
    image:id=>path.join(root,'data/Modelo1/2014/14_test_images',`${id}_0.bmp`),
  };
  if (reference === 'BTTR') return {
    labels:path.join(root,'data/BTTR',year,'caption.txt'),
    image:id=>path.join(root,'data/BTTR',year,`${id}.bmp`),
  };
  return {
    labels:path.join(root,'data/Modelo2',year,'caption.txt'),
    image:id=>path.join(root,'data/Modelo2',year,'img',`${id}.bmp`),
  };
}

function csv(value) {
  const string=String(value??'');
  return /[",\r\n]/.test(string)?`"${string.replace(/"/g,'""')}"`:string;
}

function compare(year,reference) {
  const a=abmFiles(year), b=referenceFiles(year,reference);
  const labels=captions(a.labels), referenceLabels=captions(b.labels);
  const images=readPickleArrays(a.images);
  const result={year,reference,abm_count:labels.size,reference_count:referenceLabels.size,
    caption_files_identical:sha(a.labels)===sha(b.labels),
    common:0,missing_reference:0,missing_abm_image:0,
    identical_gt:0,only_limits:0,residual_gt:0,
    image_dimensions_equal:0,image_pixels_equal:0};
  const rows=[];
  for(const [id,label] of labels) {
    const referenceLabel=referenceLabels.get(id);
    if(referenceLabel===undefined){result.missing_reference++;continue;}
    result.common++;
    let category;
    if(label===referenceLabel){category='identical';result.identical_gt++;}
    else if(withoutLimits(label)===withoutLimits(referenceLabel)){
      category='only_limits';result.only_limits++;
    } else {category='residual';result.residual_gt++;}
    const entry=images.get(id);
    if(!entry){result.missing_abm_image++;continue;}
    if(entry.fn!=='numpy.core.multiarray._reconstruct'||!Array.isArray(entry.state))
      throw new Error(`Arreglo inesperado: ${year}/${id}`);
    const [,shape,dtype,fortran,pixels]=entry.state;
    if(dtype.fn!=='numpy.dtype'||dtype.args[0]!=='u1'||fortran||!Buffer.isBuffer(pixels))
      throw new Error(`Formato de imagen inesperado: ${year}/${id}`);
    if(shape.length!==2 && !(shape.length===3 && shape[0]===1))
      throw new Error(`Dimensiones no previstas: ${year}/${id}`);
    const [height,width]=shape.length===2?shape:shape.slice(1);
    if(pixels.length!==width*height)throw new Error(`Tamaño inválido: ${year}/${id}`);
    const image=bmpPixels(b.image(id));
    const sameDimensions=height===image.height&&width===image.width;
    const samePixels=sameDimensions&&pixels.equals(image.pixels);
    if(sameDimensions)result.image_dimensions_equal++;
    if(samePixels)result.image_pixels_equal++;
    rows.push([id,category,`${width}x${height}`,`${image.width}x${image.height}`,
      samePixels,label,referenceLabel].map(csv).join(','));
  }
  if(images.size!==labels.size)throw new Error(`Conteos de etiquetas e imágenes distintos: ${year}`);
  fs.writeFileSync(path.join(outDir,`ABM-${reference}-${year}.csv`),
    'id,category,abm_dimensions,reference_dimensions,pixels_equal,abm_gt,reference_gt\n'+rows.join('\n')+'\n');
  return result;
}

fs.mkdirSync(outDir,{recursive:true});
const results=[compare('2014','SAN'),...['2014','2016','2019','train'].flatMap(year=>
  ['BTTR','PosFormer'].map(reference=>compare(year,reference)))];
fs.writeFileSync(path.join(outDir,'abm_datasets_summary.json'),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify(results,null,2));

// Lee únicamente las instrucciones de datos del pickle; no ejecuta constructores Python.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const root = path.resolve(__dirname, '../..');
const output = path.join(__dirname, 'resultados');
const MARK = Symbol('pickle mark');

function readPickleArrays(file) {
  const bytes = fs.readFileSync(file);
  let offset = 0;
  const stack = [];
  const memo = [];
  const popMark = () => {
    const values = [];
    while (stack.length) {
      const value = stack.pop();
      if (value === MARK) return values.reverse();
      values.push(value);
    }
    throw new Error('MARK ausente');
  };
  const take = size => {
    const end = offset + size;
    if (end > bytes.length) throw new Error('Pickle truncado');
    const value = bytes.subarray(offset, end);
    offset = end;
    return value;
  };
  const u8 = () => take(1)[0];
  const u16 = () => take(2).readUInt16LE(0);
  const u32 = () => take(4).readUInt32LE(0);
  const i32 = () => take(4).readInt32LE(0);
  const line = () => {
    const end = bytes.indexOf(10, offset);
    if (end < 0) throw new Error('Línea pickle incompleta');
    const value = bytes.toString('utf8', offset, end);
    offset = end + 1;
    return value;
  };
  while (offset < bytes.length) {
    const opcode = u8();
    switch (opcode) {
      case 0x80: if (u8() !== 3) throw new Error('Se esperaba protocolo 3'); break;
      case 0x7d: stack.push(new Map()); break;               // EMPTY_DICT
      case 0x5d: stack.push([]); break;                      // EMPTY_LIST
      case 0x28: stack.push(MARK); break;                    // MARK
      case 0x58: stack.push(take(u32()).toString('utf8')); break; // BINUNICODE
      case 0x55: stack.push(take(u8()).toString('latin1')); break; // SHORT_BINSTRING
      case 0x43: stack.push(take(u8())); break;             // SHORT_BINBYTES
      case 0x42: stack.push(take(u32())); break;            // BINBYTES
      case 0x63: stack.push(`${line()}.${line()}`); break;  // GLOBAL
      case 0x4b: stack.push(u8()); break;                   // BININT1
      case 0x4d: stack.push(u16()); break;                  // BININT2
      case 0x4a: stack.push(i32()); break;                  // BININT
      case 0x4e: stack.push(null); break;                   // NONE
      case 0x88: stack.push(true); break;                   // NEWTRUE
      case 0x89: stack.push(false); break;                  // NEWFALSE
      case 0x71: memo[u8()] = stack.at(-1); break;          // BINPUT
      case 0x72: memo[u32()] = stack.at(-1); break;         // LONG_BINPUT
      case 0x68: stack.push(memo[u8()]); break;             // BINGET
      case 0x6a: stack.push(memo[u32()]); break;            // LONG_BINGET
      case 0x85: stack.push([stack.pop()]); break;          // TUPLE1
      case 0x86: { const b=stack.pop(), a=stack.pop(); stack.push([a,b]); break; }
      case 0x87: { const c=stack.pop(), b=stack.pop(), a=stack.pop(); stack.push([a,b,c]); break; }
      case 0x74: stack.push(popMark()); break;              // TUPLE
      case 0x52: {                                          // REDUCE (representación, sin ejecutar)
        const args = stack.pop(), fn = stack.pop();
        stack.push({fn, args}); break;
      }
      case 0x62: {                                          // BUILD
        const state = stack.pop();
        stack.at(-1).state = state; break;
      }
      case 0x75: {                                          // SETITEMS
        const entries = popMark(), dict = stack.at(-1);
        if (!(dict instanceof Map) || entries.length % 2) throw new Error('Diccionario inválido');
        for (let i=0; i<entries.length; i+=2) dict.set(entries[i], entries[i+1]);
        break;
      }
      case 0x73: { const value=stack.pop(), key=stack.pop(); stack.at(-1).set(key,value); break; }
      case 0x2e: {
        if (offset !== bytes.length || stack.length !== 1 || !(stack[0] instanceof Map))
          throw new Error('Estructura pickle inesperada');
        return stack[0];
      }
      default: throw new Error(`Opcode pickle no previsto 0x${opcode.toString(16)} en ${offset-1}`);
    }
  }
  throw new Error('STOP ausente');
}

function bmpPixels(file) {
  const bmp = fs.readFileSync(file);
  if (bmp.toString('ascii',0,2) !== 'BM' || bmp.readUInt16LE(28) !== 8 || bmp.readUInt32LE(30) !== 0)
    throw new Error(`Se esperaba BMP de 8 bits sin compresión: ${file}`);
  const width = bmp.readInt32LE(18), signedHeight = bmp.readInt32LE(22);
  const height = Math.abs(signedHeight), stride = (width+3)&~3, start = bmp.readUInt32LE(10);
  for (let value=0; value<256; value++) {
    const palette = 54 + 4*value;
    if (bmp[palette] !== value || bmp[palette+1] !== value || bmp[palette+2] !== value)
      throw new Error(`Paleta no gris o no identidad: ${file}`);
  }
  const pixels = Buffer.alloc(width*height);
  for(let row=0;row<height;row++) {
    const input = start + (signedHeight>0 ? height-1-row : row)*stride;
    bmp.copy(pixels,row*width,input,input+width);
  }
  return {width,height,pixels};
}

function captions(file) {
  const result = new Map();
  for (const line of fs.readFileSync(file,'utf8').trim().split(/\r?\n/)) {
    const tab = line.indexOf('\t');
    if (tab < 0) throw new Error(`Etiqueta sin tabulador: ${file}`);
    const id = line.slice(0,tab);
    if (result.has(id)) throw new Error(`ID repetido: ${id}`);
    result.set(id,line.slice(tab+1).trim().replace(/\s+/g,' '));
  }
  return result;
}

function withoutLimits(value) {
  return value.split(' ').filter(token => token !== '\\limits').join(' ');
}

function sha(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function compare(year, reference) {
  const tamer = path.join(root,'data/TAMER',year);
  const other = path.join(root,'data',reference === 'SAN' ? 'Modelo1/2014' : reference === 'BTTR' ? `BTTR/${year}` : `Modelo2/${year}`);
  const tamerCaptions = path.join(tamer,'caption.txt');
  const otherCaptions = path.join(other, reference === 'SAN' ? 'test_caption.txt' : 'caption.txt');
  const tamerLabels = captions(tamerCaptions);
  const ids = [...tamerLabels.keys()];
  const pkl = readPickleArrays(path.join(tamer,'images.pkl'));
  const referenceLabels = captions(otherCaptions);
  const result = {year,reference,tamer_count:ids.length,reference_count:referenceLabels.size,
    caption_files_identical:sha(tamerCaptions)===sha(otherCaptions),
    common:0,missing_reference:0,missing_tamer_image:0,
    identical_gt:0,only_limits:0,residual_gt:0,
    image_dimensions_equal:0,image_pixels_equal:0};
  const rows=[];
  for (const id of ids) {
    if (!referenceLabels.has(id)) {result.missing_reference++; continue;}
    result.common++;
    const left=tamerLabels.get(id), right=referenceLabels.get(id);
    if (left===right) result.identical_gt++;
    else if (withoutLimits(left)===withoutLimits(right)) result.only_limits++;
    else result.residual_gt++;
    const entry=pkl.get(id);
    if (!entry) {result.missing_tamer_image++; continue;}
    if (entry.fn !== 'numpy.core.multiarray._reconstruct' || !Array.isArray(entry.state))
      throw new Error(`Arreglo inesperado: ${year}/${id}`);
    const [,shape,dtype,fortran,pixels]=entry.state;
    if (dtype.fn !== 'numpy.dtype' || dtype.args[0] !== 'u1' || fortran || !Buffer.isBuffer(pixels))
      throw new Error(`Formato de imagen inesperado: ${year}/${id}`);
    const [height,width]=shape;
    if (pixels.length !== height*width) throw new Error(`Tamaño de imagen inválido: ${year}/${id}`);
    const bmp = reference === 'SAN'
      ? path.join(other,'14_test_images',`${id}_0.bmp`)
      : path.join(other,reference==='PosFormer'?'img':'',`${id}.bmp`);
    if (!fs.existsSync(bmp)) throw new Error(`Falta imagen: ${bmp}`);
    const image=bmpPixels(bmp);
    const sameDimensions=height===image.height && width===image.width;
    const samePixels=sameDimensions && pixels.equals(image.pixels);
    if (sameDimensions) result.image_dimensions_equal++;
    if (samePixels) result.image_pixels_equal++;
    rows.push(`${id},${width}x${height},${image.width}x${image.height},${samePixels}`);
  }
  if (pkl.size !== ids.length) throw new Error(`Conteo de imágenes distinto al de etiquetas: ${year}`);
  fs.writeFileSync(path.join(output,`TAMER-${reference}-${year}-images.csv`),
    'id,tamer_dimensions,reference_dimensions,pixels_equal\n'+rows.join('\n')+'\n');
  return result;
}

if (require.main === module) {
  fs.mkdirSync(output,{recursive:true});
  const results=[compare('2014','SAN'),...['2014','2016','2019','train'].flatMap(year =>
    ['BTTR','PosFormer'].map(reference => compare(year,reference)))];
  fs.writeFileSync(path.join(output,'tamer_datasets_summary.json'),JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results,null,2));
}

module.exports = { readPickleArrays, bmpPixels, captions, withoutLimits, sha };

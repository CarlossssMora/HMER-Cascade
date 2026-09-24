// Compara los datos locales sin modificar los archivos originales.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const root = path.resolve(__dirname, '../..');
const outDir = path.join(__dirname, 'resultados');
const sources = {
  SAN: path.join(root, 'data/Modelo1/2014'),
  PosFormer: path.join(root, 'data/Modelo2'),
  BTTR: path.join(root, 'data/BTTR'),
};

function captions(file) {
  const result = new Map();
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    if (!line.trim()) continue;
    const tab = line.indexOf('\t');
    if (tab < 0) throw new Error(`Sin tabulador: ${file}: ${line}`);
    const id = line.slice(0, tab);
    if (result.has(id)) throw new Error(`ID duplicado: ${file}: ${id}`);
    result.set(id, line.slice(tab + 1).trim().replace(/\s+/g, ' '));
  }
  return result;
}

function imageFile(source, year, id) {
  if (source === 'SAN') {
    const dir = path.join(sources.SAN, '14_test_images');
    for (const name of [`${id}_0.bmp`, `${id}.bmp`]) {
      const file = path.join(dir, name);
      if (fs.existsSync(file)) return file;
    }
    return null;
  }
  const dir = source === 'BTTR'
    ? path.join(sources.BTTR, year)
    : path.join(sources.PosFormer, year, 'img');
  const file = path.join(dir, `${id}.bmp`);
  return fs.existsSync(file) ? file : null;
}

function imageInfo(file) {
  if (!file) return null;
  const data = fs.readFileSync(file);
  if (data.toString('ascii', 0, 2) !== 'BM') throw new Error(`BMP inválido: ${file}`);
  return {
    width: data.readInt32LE(18),
    height: Math.abs(data.readInt32LE(22)),
    sha256: crypto.createHash('sha256').update(data).digest('hex'),
  };
}

function withoutLimits(value) {
  return value.split(' ').filter(token => token !== '\\limits').join(' ');
}

function csv(value) {
  const string = String(value ?? '');
  return /[",\r\n]/.test(string) ? `"${string.replace(/"/g, '""')}"` : string;
}

function compare(left, right, year) {
  const leftFile = left === 'SAN'
    ? path.join(sources.SAN, 'test_caption.txt')
    : path.join(sources[left], year, 'caption.txt');
  const rightFile = path.join(sources[right], year, 'caption.txt');
  const a = captions(leftFile);
  const b = captions(rightFile);
  const ids = [...new Set([...a.keys(), ...b.keys()])].sort();
  const summary = {
    comparison: `${left}-${right}-${year}`,
    left_count: a.size,
    right_count: b.size,
    common: 0, identical_gt: 0, only_limits: 0, residual_gt: 0,
    missing_left: 0, missing_right: 0,
    limits_more_left: 0, limits_more_right: 0,
    missing_image_left: 0, missing_image_right: 0,
    image_bytes_equal: 0, image_dimensions_equal: 0,
  };
  const rows = [];
  for (const id of ids) {
    const leftGt = a.get(id);
    const rightGt = b.get(id);
    let category;
    if (leftGt === undefined) {
      category = 'missing_left'; summary.missing_left++;
    } else if (rightGt === undefined) {
      category = 'missing_right'; summary.missing_right++;
    } else {
      summary.common++;
      if (leftGt === rightGt) {
        category = 'identical'; summary.identical_gt++;
      } else if (withoutLimits(leftGt) === withoutLimits(rightGt)) {
        category = 'only_limits'; summary.only_limits++;
        const lc = leftGt.split(' ').filter(x => x === '\\limits').length;
        const rc = rightGt.split(' ').filter(x => x === '\\limits').length;
        if (lc > rc) summary.limits_more_left++;
        if (rc > lc) summary.limits_more_right++;
      } else {
        category = 'residual'; summary.residual_gt++;
      }
    }
    const ai = imageInfo(imageFile(left, year, id));
    const bi = imageInfo(imageFile(right, year, id));
    if (!ai) summary.missing_image_left++;
    if (!bi) summary.missing_image_right++;
    if (ai && bi) {
      if (ai.sha256 === bi.sha256) summary.image_bytes_equal++;
      if (ai.width === bi.width && ai.height === bi.height) summary.image_dimensions_equal++;
    }
    rows.push({ id, category, left_gt: leftGt, right_gt: rightGt,
      left_dimensions: ai ? `${ai.width}x${ai.height}` : '',
      right_dimensions: bi ? `${bi.width}x${bi.height}` : '',
      image_bytes_equal: ai && bi ? ai.sha256 === bi.sha256 : '' });
  }
  const fields = ['id', 'category', 'left_gt', 'right_gt', 'left_dimensions',
    'right_dimensions', 'image_bytes_equal'];
  const file = path.join(outDir, `${summary.comparison}.csv`);
  fs.writeFileSync(file, [fields.join(','), ...rows.map(row =>
    fields.map(field => csv(row[field])).join(','))].join('\n') + '\n');
  return summary;
}

fs.mkdirSync(outDir, { recursive: true });
const summaries = [
  compare('SAN', 'BTTR', '2014'),
  compare('SAN', 'PosFormer', '2014'),
  ...['2014', '2016', '2019'].map(year => compare('BTTR', 'PosFormer', year)),
];
const result = path.join(outDir, 'bttr_datasets_summary.json');
fs.writeFileSync(result, JSON.stringify(summaries, null, 2) + '\n');
console.log(JSON.stringify(summaries, null, 2));

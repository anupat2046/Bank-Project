// Remove stale content-type declarations without changing slide content.
const fs = require('fs');
const JSZip = require(require.resolve('jszip', { paths: [require.resolve('pptxgenjs')] }));

async function cleanContentTypes(deckPath) {
  const zip = await JSZip.loadAsync(fs.readFileSync(deckPath));
  const name = '[Content_Types].xml';
  const before = await zip.file(name).async('string');
  let removed = 0;
  const after = before.replace(/<Override\b[^>]*\/>/g, (entry) => {
    const part = entry.match(/PartName="([^"]+)"/)?.[1];
    if (part && !zip.file(part.replace(/^\//, ''))) {
      removed += 1;
      return '';
    }
    return entry;
  });
  if (removed) {
    zip.file(name, after);
    const bytes = await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
    const verified = await JSZip.loadAsync(bytes);
    for (const [part, file] of Object.entries(zip.files)) {
      if (file.dir || part === name) continue;
      if (!(await file.async('nodebuffer')).equals(await verified.file(part).async('nodebuffer'))) {
        throw new Error(`Unexpected content change: ${part}`);
      }
    }
    fs.writeFileSync(deckPath, bytes);
  }
  return removed;
}
module.exports = { cleanContentTypes };
if (require.main === module) {
  if (!process.argv[2]) throw new Error('Usage: node clean_content_types.js deck.pptx');
  cleanContentTypes(process.argv[2]).then(n => console.log(`Removed ${n} stale declarations`))
    .catch(error => { console.error(error); process.exitCode = 1; });
}

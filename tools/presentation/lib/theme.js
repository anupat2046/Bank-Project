// Writes the deck's theme into ppt/theme/theme1.xml after pptxgenjs has saved the file.
// pptxgenjs sets the theme fonts but keeps Office's stock palette and leaves the complex-script
// font empty, so Thai text would fall back to Angsana/Cordia New in PowerPoint.
const fs = require("fs");

const SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
const escAttr = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

async function applyTheme(file, theme) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  for (const k of SLOTS) {
    if (!/^[0-9A-F]{6}$/i.test(theme.colors[k] || "")) throw new Error(`theme.colors.${k} must be six hex digits`);
  }
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  let xml = await zip.file(part).async("string");
  for (const k of SLOTS) {
    xml = xml.replace(new RegExp(`<a:${k}>[\\s\\S]*?</a:${k}>`), `<a:${k}><a:srgbClr val="${theme.colors[k].toUpperCase()}"/></a:${k}>`);
  }
  const name = escAttr(theme.name);
  const face = escAttr(theme.bodyFontFace);
  xml = xml
    .replace(/(<a:theme\b[^>]*\bname=")[^"]*"/, `$1${name}"`)
    .replace(/(<a:clrScheme\b[^>]*\bname=")[^"]*"/, `$1${name}"`)
    .replace(/<a:cs typeface="[^"]*"\/>/g, `<a:cs typeface="${face}"/>`)
    .replace(/<a:font script="Thai" typeface="[^"]*"\/>/g, `<a:font script="Thai" typeface="${face}"/>`);
  zip.file(part, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

module.exports = { applyTheme };

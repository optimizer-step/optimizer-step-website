// Minify the published CSS and JavaScript in place: node scripts/minify.mjs docs/assets
// Run by scripts/build_pages.py. Comments are removed and local variable names are shortened,
// so the published files are compact and hard to read; the readable source stays in site/assets.
import { transform } from "esbuild";
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const dir = process.argv[2];
if (!dir) {
  console.error("Usage: node scripts/minify.mjs <assets-dir>");
  process.exit(2);
}

async function* walk(folder) {
  for (const entry of await readdir(folder, { withFileTypes: true })) {
    const full = path.join(folder, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else yield full;
  }
}

let before = 0;
let after = 0;
let count = 0;
for await (const file of walk(dir)) {
  const ext = path.extname(file);
  if (ext !== ".js" && ext !== ".css") continue;
  const source = await readFile(file, "utf8");
  const result = await transform(source, {
    sourcefile: path.relative(dir, file), // errors name the file, not <stdin>
    loader: ext.slice(1),
    minify: true,
    legalComments: "none",
    charset: "utf8",
    ...(ext === ".js" ? { target: "es2017" } : {}),
  });
  await writeFile(file, result.code);
  before += Buffer.byteLength(source);
  after += Buffer.byteLength(result.code);
  count += 1;
}
console.log(`Minified ${count} CSS/JS files: ${(before / 1024).toFixed(1)} KB -> ${(after / 1024).toFixed(1)} KB`);

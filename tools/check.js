// Inkstone CI check: syntax, required assets, size budget, manifest validity
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const root = path.join(__dirname, '..');
let failed = 0;
const fail = msg => { console.error('FAIL:', msg); failed++; };
const ok = msg => console.log('PASS:', msg);

// 1. required files
const required = ['index.html', 'i18n.js', 'manifest.json', 'sw.js', 'icon.svg', 'LICENSE', 'README.md',
  'vendor/marked.min.js', 'vendor/katex.min.js', 'vendor/auto-render.min.js',
  'vendor/mermaid.min.js', 'vendor/dom-to-image-more.min.js', 'vendor/purify.min.js',
  'vendor/katex.min.css'];
for (const f of required) {
  if (fs.existsSync(path.join(root, f))) ok('exists: ' + f);
  else fail('missing: ' + f);
}

// 2. size budget
const budget = [['index.html', 200 * 1024], ['vendor/mermaid.min.js', 5 * 1024 * 1024], ['vendor/katex.min.js', 400 * 1024]];
for (const [f, limit] of budget) {
  const p = path.join(root, f);
  if (!fs.existsSync(p)) continue;
  const size = fs.statSync(p).size;
  if (size <= limit) ok(`size: ${f} ${(size / 1024).toFixed(0)}KB <= ${(limit / 1024).toFixed(0)}KB`);
  else fail(`size: ${f} ${(size / 1024).toFixed(0)}KB exceeds budget ${(limit / 1024).toFixed(0)}KB`);
}

// 3. inline script syntax
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf-8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
scripts.forEach((code, i) => {
  const tmp = path.join(os.tmpdir(), `inkstone-ci-${i}.js`);
  fs.writeFileSync(tmp, code);
  try {
    execFileSync(process.execPath, ['--check', tmp], { stdio: 'pipe' });
    ok(`syntax: inline script #${i}`);
  } catch (e) {
    fail(`syntax: inline script #${i}\n` + e.stderr.toString().slice(0, 400));
  }
});

// 4. manifest validity
try {
  const m = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf-8'));
  if (m.name && m.start_url && m.icons) ok('manifest: valid'); else fail('manifest: missing fields');
} catch (e) { fail('manifest: invalid JSON'); }

// 4.5 render regression (math protection pipeline)
try {
  execFileSync(process.execPath, [path.join(__dirname, 'render-test.js')], { stdio: 'inherit' });
  ok('render regression');
} catch (e) {
  fail('render regression failed');
}

// 5. no upstream promo leakage
const promo = /lengcp2013|沃垠|Woyin AI|冷逸|Leng Yi of/;
for (const f of ['index.html', 'i18n.js']) {
  const content = fs.readFileSync(path.join(root, f), 'utf-8');
  if (promo.test(content)) fail(`promo leakage in ${f}`); else ok(`no promo: ${f}`);
}

process.exit(failed ? 1 : 0);

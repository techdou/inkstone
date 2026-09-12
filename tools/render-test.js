// 渲染回归测试：从 index.html 提取 [render-core] 区间（marked 公式保护扩展 + escMath），
// 在 node 里直接跑断言——不依赖浏览器，CI 可用。
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf-8');

// 1. 提取 render-core 区间（从标记行行尾起，避免把注释文字带进代码）
const m = html.match(/\[render-core:start\][^\n]*\n([\s\S]*?)\s*\/\/ \[render-core:end\]/);
if (!m) { console.error('FAIL: render-core 区间标记未找到'); process.exit(1); }
const core = m[1];

// 2. 在受控作用域里执行（marked 来自本地 vendor，无 DOM 依赖）
const marked = require('../vendor/marked.min.js');
const scope = { marked, result: null };
new Function('marked', 'window', core + '\nthis.__ink = { marked };').call(scope, marked, {});

const escMath = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// 区间里定义了同名函数，重新绑定到本作用域以便断言直接调用
// （new Function 内的函数声明留在作用域内，这里复制其逻辑等价断言即可）

let failed = 0;
const check = (name, cond) => {
  if (cond) console.log('PASS:', name);
  else { console.error('FAIL:', name); failed++; }
};

// 用例 1：多行 array 公式（含 \\ 行分隔）原样透传，不被 markdown 破坏
const multiLine = 'A $$\\begin{array}{r}{\\mathbf{Q}} \\\\{\\mathbf{K}} \\end{array}$$ B';
const h1 = marked.parse(multiLine);
check('多行公式整体包进 math-block（行分隔保留）', /math-block">\$\$[\s\S]*\\\\[\s\S]*\$\$<\/div>/.test(h1));
check('多行公式不被拆成多个段落', !/<\/p>\s*<p>\s*\\/.test(h1));

// 用例 2：公式内裸 < 被转义为 &lt;（不破坏 DOM）
const h2 = marked.parse('$$p < q$$');
check('公式内 < 转义为 &lt;', h2.includes('&lt;'));
check('公式内 < 不以裸标签形式泄漏', !/<q/.test(h2.replace(/&lt;/g, '')));

// 用例 3：价格文本 $5 ... $3 不误配为公式
const h3 = marked.parse('价格 $5，折扣 $3，合计 $2');
check('价格类 $ 文本不误配', !h3.includes('math-inline'));

// 用例 4：正常行内公式照常匹配
const h4 = marked.parse('范围 $W_1$ 与 $a_1+b_2$');
check('正常行内公式匹配 2 处', (h4.match(/math-inline/g) || []).length === 2);

// 用例 5：行内公式内 < 同样转义
const h5 = marked.parse('$a<b$');
check('行内公式 < 转义', h5.includes('&lt;') && !/<b\$/.test(h5));

// 用例 6：$ 转义形态 \$ 不触发公式
const h6 = marked.parse('花费 \\$5 和 \\$6');
check('\\$ 转义不触发公式', !h6.includes('math-inline'));

if (failed) {
  console.error(`\n${failed} 个用例失败`);
  process.exit(1);
}
console.log('\n渲染回归测试全部通过');

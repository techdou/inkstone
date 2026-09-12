#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地代理脚本，配合 markdown-editor.html 的「网页转 Markdown」功能使用。
解决浏览器跨域限制和部分反爬问题。

用法：
    python web-to-md-proxy.py              # 启动本地代理
    python web-to-md-proxy.py --bookmark   # 生成浏览器书签小工具代码
"""

import json
import sys
import re
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

PORT = 8765

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
]


def make_headers(url):
    host = urlparse(url).netloc.lower()
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    # 知乎需要 referer 和一些额外头
    if 'zhihu.com' in host:
        headers['Referer'] = 'https://www.zhihu.com/'
        headers['x-requested-with'] = 'fetch'
    elif 'weixin.qq.com' in host or 'mp.weixin.qq.com' in host:
        headers['Referer'] = 'https://mp.weixin.qq.com/'
    elif 'jianshu.com' in host:
        headers['Referer'] = 'https://www.jianshu.com/'
    return headers


def fetch_with_requests(url, retries=2):
    last_err = None
    for attempt in range(retries + 1):
        try:
            headers = make_headers(url)
            resp = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1 + attempt)
    raise last_err


def fetch_with_urllib(url):
    headers = make_headers(url)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = resp.read()
        charset = 'utf-8'
        ct = resp.headers.get('Content-Type', '')
        m = re.search(r'charset=([\w-]+)', ct)
        if m:
            charset = m.group(1)
        try:
            return data.decode(charset)
        except (UnicodeDecodeError, LookupError):
            return data.decode('utf-8', errors='ignore')


def fetch_url(url):
    if HAS_REQUESTS:
        return fetch_with_requests(url)
    return fetch_with_urllib(url)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if parsed.path != '/fetch':
            body = json.dumps({'error': 'Only /fetch endpoint is supported'}, ensure_ascii=False)
            self.wfile.write(body.encode('utf-8'))
            return

        urls = params.get('url', [])
        if not urls:
            body = json.dumps({'error': 'Missing url parameter'}, ensure_ascii=False)
            self.wfile.write(body.encode('utf-8'))
            return

        url = unquote(urls[0])
        try:
            html_text = fetch_url(url)
            body = json.dumps({
                'success': True,
                'html': html_text,
                'length': len(html_text)
            }, ensure_ascii=False)
        except Exception as e:
            err_msg = str(e)
            hint = ''
            if '403' in err_msg:
                hint = '目标网站拒绝访问，可能需要登录。建议在该网页已登录状态下使用浏览器书签小工具，或手动粘贴 HTML 源码。'
            elif 'zhihu.com' in url:
                hint = '知乎需要登录才能查看全文，请在浏览器中登录知乎后使用书签小工具提取。'
            body = json.dumps({
                'success': False,
                'error': err_msg,
                'hint': hint
            }, ensure_ascii=False)

        self.wfile.write(body.encode('utf-8'))

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


BOOKMARKLET_JS = r"""
javascript:(function(){
  function toMd(n){
    if(n.nodeType===3)return n.textContent.replace(/\s+/g,' ');
    if(n.nodeType!==1)return '';
    var t=n.tagName.toLowerCase(),c=Array.from(n.childNodes).map(toMd).join(''),h;
    switch(t){
      case 'h1':return '# '+c.trim()+'\n\n';
      case 'h2':return '## '+c.trim()+'\n\n';
      case 'h3':return '### '+c.trim()+'\n\n';
      case 'p':return c.trim()+'\n\n';
      case 'br':return '\n';
      case 'a':h=n.getAttribute('href')||'';return '['+c+']('+h+')';
      case 'strong':case 'b':return '**'+c+'**';
      case 'em':case 'i':return '*'+c+'*';
      case 'code':return '`'+c+'`';
      case 'pre':return '\n```\n'+c.trim()+'\n```\n\n';
      case 'ul':return Array.from(n.children).map(function(li){return '- '+toMd(li).trim();}).join('\n')+'\n\n';
      case 'ol':return Array.from(n.children).map(function(li,i){return (i+1)+'. '+toMd(li).trim();}).join('\n')+'\n\n';
      case 'blockquote':return '> '+c.trim().replace(/\n/g,'\n> ')+'\n\n';
      case 'hr':return '---\n\n';
      case 'div':case 'section':case 'article':return c.trim()+'\n\n';
      default:return c;
    }
  }
  var sel='article,[role=main],.post-content,.entry-content,.article-content,#js_content,.rich_media_content,.content,#content,main';
  var el=document.querySelector(sel)||document.body;
  el.querySelectorAll('script,style,nav,aside,header,footer,form,iframe,img,svg,video,audio,canvas,.ad,.ads,.sidebar,.comments').forEach(function(e){e.remove();});
  var md=toMd(el).replace(/\n{3,}/g,'\n\n').trim();
  var title=document.title||'';
  if(title)md='# '+title+'\n\n'+md;
  navigator.clipboard.writeText(md).then(function(){alert('已复制 Markdown，请回到编辑器粘贴');}).catch(function(){prompt('请复制以下内容：',md);});
})();
""".strip()


def print_bookmarklet():
    js = BOOKMARKLET_JS.replace('\n', '')
    print("=" * 60)
    print("浏览器书签小工具（Bookmarklet）")
    print("=" * 60)
    print("\n使用方法：")
    print("1. 复制下面整行代码（以 javascript: 开头）")
    print("2. 在浏览器书签栏右键 → 添加网页")
    print("3. 名称填「提取 Markdown」，网址粘贴复制的代码")
    print("4. 在知乎、微信公众号等已登录页面点击该书签，即可复制 Markdown\n")
    print(js)
    print("\n" + "=" * 60)


def main():
    if '--bookmark' in sys.argv or '-b' in sys.argv:
        print_bookmarklet()
        return

    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f"本地代理已启动: http://127.0.0.1:{PORT}")
    print("在 Markdown 编辑器中勾选「使用本地代理」即可使用")
    print("如需生成浏览器书签小工具，请运行：python web-to-md-proxy.py --bookmark")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        sys.exit(0)


if __name__ == '__main__':
    main()

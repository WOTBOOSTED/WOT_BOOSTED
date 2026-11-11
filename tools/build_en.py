#!/usr/bin/env python3
"""Збирає англійські сторінки /en/… з українських.
Запуск із кореня репозиторію після будь-якої правки сторінок:  python3 tools/build_en.py
Переклади беруться з об'єкта `translations.en` у самій сторінці (потрібен node)."""
import re, json, subprocess, html, os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES={'':'index.html','top-tanks':'top-tanks/index.html','streams':'streams/index.html','group':'group/index.html','modpack':'modpack/index.html'}
META={
 '':('WOT BOOSTED — WoT boosting: Personal Missions, Marks, Ace Tanker',
     'World of Tanks boosting by WOT BOOSTED: Personal Missions 1.0–4.0, Marks of Excellence, Ace Tanker, damage battles for WN8. Every order is streamed on YouTube for the customer.',
     'WOT BOOSTED — professional World of Tanks boosting',
     'Personal Missions, Marks of Excellence, Ace Tanker, damage battles. Fast, safe, honest.'),
 'top-tanks':('Top Tanks — WOT BOOSTED','Personal World of Tanks top list by WOT BOOSTED: the best vehicles of tiers 8, 9, 10 and 11 — five tanks per tier worth grinding and getting.',None,None),
 'streams':('Streams — WOT BOOSTED','WOT BOOSTED streams and broadcast recordings for World of Tanks: tank reviews, order runs and live battles. Watch on the @wot_boosted YouTube channel.',None,None),
 'group':('Group — WOT BOOSTED','WOT BOOSTED Telegram group: World of Tanks boosting news, updates and fresh posts. Join and read the feed right on the site.',None,None),
 'modpack':('Modpack — WOT BOOSTED','WOT BOOSTED modpack for World of Tanks — a personal mod build by the booster. The page is in progress, the modpack is coming soon.',None,None),
}
HTML_KEYS={'services_title':'MY <span>SERVICES</span>','why_title':'WHY <span>ME</span>','cta_title':'READY TO <span>ORDER?</span>','how_title':'HOW IT <span>WORKS</span>'}
def translations_en(s):
    a=s.index('const translations = '); b=s.index('\n};',a)+3
    js=s[a:b]+'\nprocess.stdout.write(JSON.stringify(translations.en));'
    return json.loads(subprocess.run(['node','-e',js],capture_output=True,text=True,check=True).stdout)
def build(slug,f):
    s=open(os.path.join(ROOT,f),encoding='utf-8').read()
    t=translations_en(s)
    path='/'+(slug+'/' if slug else '')
    title,desc,ogt,ogd=META[slug]; ogt=ogt or title; ogd=ogd or desc
    def one(pat,rep,s,n=1):
        s2,k=re.subn(pat,rep,s,flags=re.S); assert k==n,(pat,k); return s2
    s=one(r'<html lang="uk">','<html lang="en">',s)
    s=one(r'<title>.*?</title>',lambda m:'<title>'+html.escape(title,quote=False)+'</title>',s)
    s=one(r'<meta name="description" content="[^"]*">',lambda m:f'<meta name="description" content="{html.escape(desc)}">',s)
    s=one(r'<meta property="og:title" content="[^"]*">',lambda m:f'<meta property="og:title" content="{html.escape(ogt)}">',s)
    s=one(r'<meta property="og:description" content="[^"]*">',lambda m:f'<meta property="og:description" content="{html.escape(ogd)}">',s)
    s=one(r'<meta property="og:url" content="[^"]*">',f'<meta property="og:url" content="https://wotboosted.com/en{path}">',s)
    s=one(r'<link rel="canonical" href="[^"]*">',f'<link rel="canonical" href="https://wotboosted.com/en{path}">',s)
    # internal links -> /en/…  (крім перемикача мов)
    def link(m):
        tag=m.group(0)
        if 'lang-btn' in tag: return tag
        return re.sub(r'href="/((?:top-tanks|streams|group|modpack)/)?"',lambda k:'href="/en/'+(k.group(1) or '')+'"',tag)
    s=re.sub(r'<a\b[^>]*>',link,s)
    # active language button
    s=one(r'<a class="lang-btn active" href="([^"]*)" hreflang="uk"',r'<a class="lang-btn" href="\1" hreflang="uk"',s)
    s=one(r'<a class="lang-btn" href="([^"]*)" hreflang="en"',r'<a class="lang-btn active" href="\1" hreflang="en"',s)
    # static texts
    miss=[]
    def txt(m):
        k=m.group(3)
        if k not in t: miss.append(k); return m.group(0)
        if m.group(2)=='data-t-html' or k in HTML_KEYS: inner=HTML_KEYS.get(k,t[k])
        else: inner=html.escape(t[k],quote=False)
        return m.group(1)+inner+m.group(5)
    s=re.sub(r'(<(?P<tag>[a-zA-Z0-9]+)\b[^>]*?\b(data-t|data-t-html)="([^"]+)"[^>]*>)(?P<body>.*?)(</(?P=tag)>)',
             lambda m: txt(type('M',(),{'group':lambda self,i:{0:m.group(0),1:m.group(1),2:m.group(3),3:m.group(4),5:m.group(6)}[i]})()),s,flags=re.S)
    def aria(m):
        tag=m.group(0); k=re.search(r'data-t-aria="([^"]+)"',tag).group(1)
        if k not in t: miss.append(k); return tag
        return re.sub(r'aria-label="[^"]*"',lambda _:'aria-label="'+html.escape(t[k])+'"',tag,count=1)
    s=re.sub(r'<[a-zA-Z0-9]+\b[^>]*\bdata-t-aria="[^"]+"[^>]*>',aria,s)
    # service card images: English variants
    def pic(m):
        p=m.group(0); base=re.search(r'data-img="([^"]+)"',p).group(1); en=re.search(r'data-alt-en="([^"]*)"',p).group(1)
        p=p.replace(f'srcset="{base}.webp"',f'srcset="{base}-en.webp"').replace(f'src="{base}.jpg"',f'src="{base}-en.jpg"')
        return re.sub(r' alt="[^"]*"',lambda _:f' alt="{en}"',p,count=1)
    s=re.sub(r'<picture><source[^>]*><img[^>]*data-img="[^"]+"[^>]*></picture>',pic,s)
    out=os.path.join(ROOT,'en',slug,'index.html'); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,'w',encoding='utf-8').write(s)
    print('en'+path, 'keys:',len(t), 'missing:',sorted(set(miss)))
for slug,f in PAGES.items(): build(slug,f)

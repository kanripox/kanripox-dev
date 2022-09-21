#!/usr/bin/env python
# coding: utf-8

import xml.etree.ElementTree as ET
import xml.etree.ElementInclude as EI
import os, json, re
#from collatex import *

tei_xmlns="{http://www.tei-c.org/ns/1.0}"
xml_xmlns="{http://www.w3.org/XML/1998/namespace}"
krx_xmlns="{http://kanripo.org/ns/KRX/1.0}"

#kanji='\u3000\u3400-\u4DFF\u4e00-\u9FFF\uF900-\uFAFF'
# remove space from kanji definition:
kanji='\u3400-\u4DFF\u4e00-\u9FFF\uF900-\uFAFF'
astkanji = '\U00020000-\U0002A6DF\U0002A700-\U0002B73F\U0002B740-\U0002B81F\U0002B820-\U0002F7FF'
pua='\uE000-\uF8FF'
astpua = '\U000F0000-\U000FFFFD\U00100000-\U0010FFFD'
##this will recognize image links like [[./img]] as 1 kanji --> clear this out later?!
ent=r'\[\[.*?\]\]|\[[^\]]*\]|&[^;]*;|&amp;[CZ][X3-7]-[A-F0-9]+'
#now
kp_re = re.compile(u"(%s|[%s%s%s])" % (ent, kanji, astkanji, pua))
punc_re = re.compile(u"[\u3001-\u33FF\uFE00-\uFF7F]+")
start_re = re.compile(u"[〈《「『【〖〘〚]+")
meta_re = re.compile(u'(<[^>]*>|\n#\+BEGIN_VERSE\n|\n#\+END_VERSE\n|\xb6|\n)')

def line2arr(line):
    line = re.sub(u"[\n\t ]+", "", line)
    ex=kp_re.split(u"。"+line)
    ex.insert(0,(''))
    cs=[a for a in zip(*[iter(ex)]*2)]
    seq=[]
    n=""
    for c in cs:
        c1=[a for a in start_re.split( c[1]) if len(a) > 0]
        if len(c1) == 0:
            co=u""
        else:
            co = c1[0]
        seq.append([n, c[0], co])
        if len(c1) > 1:
            n=c1[1]
        else: 
            n=u""
    return seq[1:]

# p_content gets a dict with tags and content recursively
# caller needs to pass in res
# att are the attributes that get picked up
def p_content(el, res, att=['n', '{http://www.w3.org/XML/1998/namespace}id']):
    at={}
    tn=el.tag.replace("{http://www.tei-c.org/ns/1.0}", "")
    for a in el.attrib:
        if a in att:
            local=a.replace("{http://www.w3.org/XML/1998/namespace}", "")
            at[local]=el.attrib[a]
        at['start_name']=tn
    if el.text:
        res.append((el.text, at))
    else:
        res.append(('', at))
    for e in el:
        p_content(e, res)
    if el.tail:
        res.append((el.tail, {'end_name': tn}))


# linechildren only gets the text within the element, including nested tags
def linechildren(el):
    ret = ""
    if el.text:
        ret += el.text
#    try:
#        t = el.tail.replace("\n", "")
#    except:
#        t = ""
    for c in list(el):
        if c.text:
            ret += c.text
        for e in list(c):
            ret += linechildren(e)
        if c.tail:
            ret += c.tail
    try:
        ret += el.tail
    except:
        pass
    return ret

def mandoku2tok(p, tmap):
    tok=[]
    fs = [a for a in os.listdir(p) if a.endswith("txt")]
    fs.sort()
    for f in fs:
        lcnt = 0
        pb ="noid"
        tag = "md:line"
        level = 0
        mode = "p"
        inf=open(f"{p}/{f}", encoding="utf-8")
        for line in inf:
            line = line[:-1].replace("\r", "")
            if line.startswith("#"):
                continue
            if "<pb:" in line:
                pb=re.findall("<pb:([^>]+)>", line)[0]
                line = re.sub("<pb:[^>]+>", "", line)
                lcnt = 0
            lcnt += len(re.findall("\xb6", line))
            line = line.replace("\xb6", "")
            line = re.sub("<md:[^>]+>", "", line)
            for k in tmap.keys():
                if re.match(k, line):
                    ln=re.sub(k, tmap[k][0], line)
                    mode=tmap[k][1]
                    if (mode == "h"):
                        level = len(line) - len(ln) - 1
                    line = ln
            seq = line2arr(line)
            cnt = 0
            for s in seq:
                cnt += 1
                tok.append((mode, f"{pb}.{lcnt}", cnt, s))
        # the other modes are sticky, TODO need to make this configurable
        if mode == "h":
            mode = "p"
    return tok
# pel is the parent element. False means: do not include  2020-11-18: this is ignored for now
# create a tok and a div structure as table of contents
# 2022-09-21:  need explicit role:  root (default)= root text to be commented on,  or comm (set when applicaple)
def parse2tok(p, tmap, pel=False):
    tree = ET.parse(p)
    cwd=os.getcwd()
    os.chdir(os.path.dirname(p))
    root = tree.getroot()
    EI.include(root)
    parent_map = {c: p for p in root.iter() for c in p}
    ls = root.findall(f'.//{tei_xmlns}line')
    if len(ls) == 0:
        ls = root.findall(f'.//{tei_xmlns}seg')
    if len(ls) == 0:
        ls = root.findall(f'.//{tei_xmlns}l')
    if len(ls) == 0:
        ls = root.findall(f'.//{tei_xmlns}p')
    tok=[]
    divs=[]
    if ls[0].tag.endswith('p'):
        tl=[]
        for b in ls:
            res=[]
            p_content(b, res)
            tl.append(res)
        return tl, ["p"]
    for b in ls:
        role="root"
        p=parent_map[b]
        if pel:
            px = p.tag.replace(f'{tei_xmlns}', '') + "/"
        else:
            px = ""
        if (p.tag == '{http://www.tei-c.org/ns/1.0}head'):
            pdiv = parent_map[p]
            if f'{xml_xmlns}id' in pdiv.attrib:
                pdivid=pdiv.attrib[f'{xml_xmlns}id']
            else:
                pdivid=''
            divs.append((len(tok), b.text, pdivid))
        pm=[p]
        while p in parent_map:
            p=parent_map[p]
            pm.append(p)
        px="p"
        for p in pm:
            #print(p.tag)
            if p.tag in tmap:
                px = tmap[p.tag][1]
                break
        #tag = b.tag.replace(f'{tei_xmlns}', '')
        tag=""
        if "rend" in b.attrib:
            tag = ";" + b.attrib["rend"]
        if f'{xml_xmlns}id' in b.attrib:
            id=b.attrib[f'{xml_xmlns}id']
        else:
            id="noid"
        if "type" in b.attrib:
            role = b.attrib["type"]
        tx = linechildren(b)
        tx = tx.replace("\n", "")
        seq=line2arr(tx)
        cnt = 0
        for s in seq:
            cnt += 1
            # role is added last to avoid disturbances of the code reliying on positional identification
            tok.append((px + tag, id, cnt, s, role))
    os.chdir(cwd)
    return (tok, divs)

def write_tok(tok, tok_base, step=10000, log=False):
    """tok is the list of tokens, tok_base the stub for the filename, including branch."""
    fnbase=os.path.split(tok_base)[-1]
    if step == -1:
        step = len(tok) + 1
    for cnt, i in enumerate(range (0, len(tok), step)):
        nf="%4.4d" % (cnt)
        xid=f"{fnbase}-tok-{nf}"
        edid=f"{fnbase}"
        n=f"tok-{nf}"
        ofn="%s-tok-%s.xml" % (tok_base, nf)
        of=open(ofn, mode="w", encoding="utf8")
        of.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<tList xml:id="{xid}" ed="{edid}" n="{n}" xmlns="http://kanripo.org/ns/KRX/1.0"><tg>""")
        limit = min(len(tok), i+step)
        for j in range(i, limit, 1):
            t=tok[j]
            if len(t[3][0]) > 0:
                p=f' p="{t[3][0]}"'
            else:
                p=""
            if len(t[3][2]) > 0:
                f=f' f="{t[3][2]}"'
            else:
                f=""
            c = t[3][1].replace("&", "$")
            if j > 0:
                if tok[j-1][1] != tok[j][1]:
                    pbo = tok[j-1][1].split(".")[0]
                    pbn = tok[j][1].split(".")[0]
                    if pbo != pbn:
                        of.write(f'<pb ed="{edid}" n="{pbn}"/>')
                    if tok[j][1] == "noid.0":
                        tgid=""
                    else:
                        tgid=f' xml:id="{tok[j][1]}"'
                    of.write(f'</tg>\n<tg{tgid}>\n<lb ed="{edid}" n="{tok[j][1]}"/>\n')
            if t[1].startswith("noid"):
                tn = "noid.%d" % (j)
            else:
                tn = t[1]
            # 2022-09-21: for now, I only take the first letter of the t[4], to save some bits.
            of.write(f'<t tp="{j}" n="{tn}" role="{t[4][0]}" pos="{t[2]}"{p}{f}>{c}</t>\n')
        of.write("</tg></tList>\n")
        of.close()
def process_ptok(tl):
    tkl=[]
    tp = 0
    for p in tl:
        try:
            idx = p[0][1]['id']
        except:
            idx= None
        if idx:
            tkl.append('<tg xml:id="%s">' % (idx))
            lbl=' n="%s"' % (idx)
        else:
            tkl.append('<tg>')
            lbl=""
        lp=0
        tks=[]
        for el in p:
            try:
                if el[1]['start_name']:
                    lp = 0
            except:
                pass
            try:
                att= ' role="%s"' % (el[1]['n'])
            except:
                att= ' role="%s"' % ('d')
            elt = el[0]
            elt = re.sub("<.*=(.)>", "\\1", elt)
            if punc_re.match(elt):
                me=punc_re.match(elt)
                st = elt[0:me.end()]
                if not (start_re.match(st)):
                    tks[-1][2] = tks[-1][2] + st
            ex=line2arr(elt)
            if start_re.match(elt):
                me=start_re.match(elt)
                st = elt[0:me.end()]
                ex[0][0] = st + ex[0][0]
            for e in ex:
                lp += 1
                e.append(lp)
                e.append(tp)
                e.append(att)
                tp += 1
                tks.append(e)
        # 2022-09-21:  what is doing this?
        oldrole=''
        for t in tks:
            if len(t[0]) > 0:
                pre = ' p="%s"' % (t[0])
            else:
                pre = ""
            if len(t[2]) > 0 :
                if not(start_re.match(t[2])):
                    fol = ' f="%s"' % (t[2])
                else:
                    fol = ""
            else:
                fol = ""
            tkl.append('<t%s%s%s%s tp="%d" pos="%d">%s</t>' % (lbl, pre, fol, t[5], t[4], t[3], t[1]) )
            oldrole = t[5]
        tkl.append('</tg>')
    return tkl


def write_ptok(tl, tok_base):
    """tok is the list of tokens produced with p_content, tok_base the stub for the filename, including branch."""
    fnbase=os.path.split(tok_base)[-1]
    tkl=process_ptok(tl)
    nf="%4.4d" % (0)
    xid=f"{fnbase}-tok-{nf}"
    edid=f"{fnbase}"
    n=f"tok-{nf}"
    ofn="%s-tok-0000.xml" % (tok_base)
    of=open(ofn, mode="w", encoding="utf8")
    of.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<tList xml:id="{xid}" ed="{edid}" n="{n}" xmlns="http://kanripo.org/ns/KRX/1.0">""")
    of.write("\n".join(tkl))
    of.write("</tList>\n")
    of.close()


def maketmap(tx, txt=True):
    nmap={}
    if tx.tag == f"{krx_xmlns}tokenmap":
        for m in tx:
            rp=""
            r = m.attrib['src']
            tk=m.attrib['tok']
            if r.endswith("\\n"):
                  r = r[:-2]
            if r.startswith("^"):
                r = r[1:]
            if txt:
                r = "(%s)" % (r)
            else:
                r = "%s" % (r.replace("tei:", tei_xmlns))
                if "[" in r:
                    r, a = r.split("[")
                    rp=a[:-1]
            nmap[r]=(rp, tk)
    return nmap

def tokout(edid, loc, format, tmap, tok_base):
    if format.startswith("txt"):
        toq=mandoku2tok(loc, tmap)
    elif loc.endswith(".xml"):
        toq, dv = parse2tok(f"{loc}", tmap, pel=True)
    elif format.startswith("xml"):
        xmlfile=[a for a in os.listdir(loc) if a.endswith("xml") and not ("_" in a)][0]
        toq, dv = parse2tok(f"{loc}/{xmlfile}", tmap, pel=True)
    if len(dv) > 0 and dv[0] == "p":
        write_ptok(toq, tok_base)
    elif len(toq) > 0:
        write_tok(toq, tok_base, step=-1)
        print(len(toq))
    return

def make_toks():
    mtree=ET.parse("Manifest.xml")
    cdir = os.path.abspath(".")
    if not os.path.exists("aux/tok"):
        os.makedirs("aux/tok", exist_ok=True)

    doc = mtree.findall(f'.//{krx_xmlns}edition')
    for d in doc:
        if d.attrib['language']=='lzh':
            os.chdir(cdir)
            toq=[]
            edid=d.attrib['id']
            tok_base=os.path.abspath(f"aux/tok/{edid}")
            #print (edid, tok_base)
            loc=f"{d.attrib['location']}"
            print(edid)
            if f"{krx_xmlns}tokenmap" in [a.tag for a in list(d)]:
                tmap=maketmap(d.find(f"{krx_xmlns}tokenmap"), txt=d.attrib['format'].startswith("txt"))
            else:
                tmap={}
            tokout(edid, loc, d.attrib['format'], tmap, tok_base)



if __name__ == '__main__':
    # base="/home/chris/Dropbox/current/kanripox/KR6c0128/"
    # ed= base + "doc/CBETA/KR6c0128.xml"
    # tokd="%s/aux/tok"%(base)
    # toq, divs=parse2tok(ed)
    # if len(toq) > 0:
    #         write_tok(toq, tok_base)
    #     print(len(toq))
#    print (tok)
#    print (divs)
    
    make_toks()

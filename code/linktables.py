#!/usr/bin/env python
# coding: utf-8
from difflib import *
import xml.etree.ElementTree as ET
import os, re, sys
from collections import defaultdict


def read_tokens(textdir):
    tokd="%s/aux/tok"%(textdir)
    tf=[a.replace("-log.xml", "") for a in os.listdir(tokd) if a.endswith("log.xml")]
    tf.sort()
    # the sequences for every file will be stored here
    tseq = {}
    for t in tf:
        textid = t
        target = [a for a in os.listdir(tokd) if a.startswith("%s-tok" % (textid))]
        target.sort()
        t1 = []
        for t in target:
            tree = ET.parse("%s/%s" % (tokd, t))
            root = tree.getroot()
            p=root.findall(".//t")
            for child in p:
                if 'id' in child.attrib:
                    ix = child.attrib['id']
                else:
                    ix = "no_id"
                t1.append((child.text, ix, int(child.attrib['tp']), child.attrib['pos'] ))
        tseq[textid] = t1
    return tseq


# In[5]:


def align_tokens(tseq, textid):
    mq=[]
    sq=SequenceMatcher()
    sq.set_seq1([a[0] for a in tseq[textid]])
    for s1 in tseq:
        if s1 != textid:
            sq.set_seq2([a[0] for a in tseq[s1]])
            o=sq.get_opcodes()
            mq.append((s1, o))
    return mq


def write_table(tseq, textdir, textid):
    tokd="%s/aux/tok"%(textdir)
    tf=[a.replace("-log.xml", "") for a in os.listdir(tokd) if a.endswith("log.xml")]   
    tf.sort()
    mq=align_tokens(tseq, textid)
    sdic=[]
    for mt in range(0, len(mq)):
        lx = 0
        lid=""
        ldic=[]
        trg = mq[mt][0]
        ed="%s" % (trg)
        for tag, i1, i2, j1, j2 in mq[mt][1]:
            if tag in ['insert']:
                for l in range(j1, j2):
                    ldic.append((tag, ('i', 'i'), tseq[trg][l], ed))
            elif tag in ['delete']:
                for l in range(i1, i2):
                    sid = tseq[textid][l][1]
                    if sid != lid:
                        sdic.append(ldic)
                        ldic = []
                        lid = sid
                    ldic.append((tag, tseq[textid][l], ('d', 'd'), ed))
            elif tag in ['equal', 'replace']:
                dx= j1 - i1
                for l in range(i1, i2):
                    try:
                        sid = tseq[textid][l][1]
                    except:
                        print(textid, l, len(tseq[textid]), i2)
                        break
                    if sid != lid:
                        sdic.append(ldic)
                        ldic = []
                        lid = sid
                    try:
                        ldic.append ((tag, tseq[textid][l], tseq[trg][l+dx], ed))
                    except:
                        print("error,", tag, textid, l, trg, l+dx)
                        
        sdic.append(ldic)
        tdic=defaultdict(list)
        for a in sdic:
            try:
                ix=a[0][1][1]
                tx=a[1][2][1]
                ed=a[0][3]
            except:
                continue
            try:
                itp=a[0][1][2]
            except:
                itp=0
            try:
                ttp=a[1][2][2]
            except:
                ttp=0
            icount = len([x for x in a if x[0] == 'insert'])
            dcount = len([x for x in a if x[0] == 'delete'])
            df = max(dcount, icount)
            if (df > 0):
                diff = " diff='%d'" % (df)
            else:
                diff = ""
            key="<seg id='%s' tp='%d' tcount='%d'>\n" % (ix, itp-1, len(a) - icount)
            if tx == 'd':
                val="<ref ed='%s' corresp='#%s_%s' tp='%d' tcount='%d'%s/>\n" % (ed, ed, tx, ttp, len(a) - dcount, diff)
            else:
                val="<ref ed='%s' corresp='#%s' tp='%d' tcount='%d'%s/>\n" % (ed, tx, ttp-2, len(a) - dcount, diff)
            tdic[key].append(val)
    lnkd="%s/aux/lnk"%(textdir)
    os.makedirs(lnkd, exist_ok=True)
    of=open("%s/%s-align-tab.xml" % (lnkd, textid), "w", encoding="utf-8" )
    of.write("<div ed='%s'>\n" %(textid))
    k=[fx for fx in tdic.keys()]
    try:
        k=sorted(k, key = lambda x: int(re.findall("tp='(-?[0-9]+)'", x)[0]))
    except:
        pass
    for kn in k:
        of.write(kn)
        of.write("".join(tdic[kn]))
        of.write("</seg>\n")
    of.write("</div>\n")
    of.close()


def read_align_tabs(textdir):
    lnkd = "%s/aux/lnk" % (textdir)
    at=[a for a in os.listdir(lnkd) if a.endswith(".xml")]
    segs = defaultdict(list)
    for atb in at:
        tree = ET.parse("%s/%s" % (lnkd, atb))
        root = tree.getroot()
        for seg in root:
            segid=seg.attrib['id']
            tp=seg.attrib['tp']
            tcount=seg.attrib['tcount']
            segs[segid].append((segid, int(tp), int(tcount)))
            for ref in seg:
                segs[segid].append((ref.attrib['corresp'][1:], int(ref.attrib['tp']), int(ref.attrib['tcount'])))
    return segs

def get_alignments(ttok, s):
    "Get the alignments for a segment; ttok is the token table."
    tk = []
    for seg in s:
        idx = "_".join(seg[0].split("_")[0:2])
        if not idx in ttok:
            idx=seg[0].split("_")[0]
        tp=seg[1]
        tcount = seg[2]
        toks = ttok[idx][tp:tp+tcount]
        if len(toks) < 1:
            toks = [('', idx, 0)]
        tl = []
        for t in toks:
            tl.append({"t" : t[0], 'id' : t[1], 'tp' : t[2]})

        tk.append({'id': idx, 'tokens' : tl})
    #break
    return {'witnesses' : tk}
if __name__ == '__main__':
    tdir = sys.argv[1]
    tr = read_tokens(tdir)
    for src in tr:
         print (src)
         write_table(tr, tdir, src)
    print ("Wrote tables for %s" % (tdir))

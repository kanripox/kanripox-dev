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
    tseq = []
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
        tseq.append(t1)
    return tseq


# In[5]:


def align_tokens(tseq, m=0):
    mq=[]
    sq=SequenceMatcher()
    sq.set_seq1([a[0] for a in tseq[m]])
    for i, s1 in enumerate(tseq):
        if i != m:
            sq.set_seq2([a[0] for a in tseq[i]])
            o=sq.get_opcodes()
            mq.append((i, o))
    return mq


def write_table(tseq, textdir, src=0):
    tokd="%s/aux/tok"%(textdir)
    tf=[a.replace("-log.xml", "") for a in os.listdir(tokd) if a.endswith("log.xml")]   
    tf.sort()
    mq=align_tokens(tseq, m=src)
    sdic=[]
    for mt in range(0, len(mq)):
        lx = 0
        lid=""
        ldic=[]
        trg = mq[mt][0]
        for tag, i1, i2, j1, j2 in mq[mt][1]:
            if tag in ['insert']:
                for l in range(j1, j2):
                    ldic.append((tag, ('i', 'i'), tseq[trg][l]))
            elif tag in ['delete']:
                for l in range(i1, i2):
                    sid = tseq[src][l][1]
                    if sid != lid:
                        sdic.append(ldic)
                        ldic = []
                        lid = sid
                    ldic.append((tag, tseq[src][l], ('d', 'd')))
            elif tag in ['equal', 'replace']:
                dx= j1 - i1
                for l in range(i1, i2):
                    try:
                        sid = tseq[src][l][1]
                    except:
                        print(src, l, len(tseq[src]), i2)
                        break
                    if sid != lid:
                        sdic.append(ldic)
                        ldic = []
                        lid = sid
                    try:
                        ldic.append ((tag, tseq[src][l], tseq[trg][l+dx]))
                    except:
                        print("error,", tag, src, l, trg, l+dx)
                        
        sdic.append(ldic)
        tdic=defaultdict(list)
        for a in sdic:
            try:
                ix=a[0][1][1]
                tx=a[1][2][1]
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
            key="<seg id='%s' tp='%d' tcount='%d'>\n" % (ix, itp, len(a) - icount)
            val="<ref ed='%s' corresp='#%s' tp='%d' tcount='%d'/>\n" % (tf[trg], tx, ttp, len(a) - dcount)
            tdic[key].append(val)
    lnkd="%s/aux/lnk"%(textdir)
    os.makedirs(lnkd, exist_ok=True)
    of=open("%s/%s-align-tab.xml" % (lnkd, tf[src]), "w", encoding="utf-8" )
    of.write("<div ed='%s'>\n" %(tf[src]))
    k=[fx for fx in tdic.keys()]
    k=sorted(k, key = lambda x: int(re.findall("tp='([0-9]+)'", x)[0]))
    for kn in k:
        of.write(kn)
        of.write("".join(tdic[kn]))
        of.write("</seg>\n")
    of.write("</div>\n")
    of.close()
#    break


if __name__ == '__main__':
    tdir = sys.argv[1]
    tr = read_tokens(tdir)
    for src in range(0, len(tr)):
        print (src)
        write_table(tr, tdir, src)
    print ("Wrote tables for %s" % (tdir))

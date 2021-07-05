#!/usr/bin/env python
# coding: utf-8
# read the tokens in aux/tok and write the linktables in aux/lnk/
from difflib import *
import xml.etree.ElementTree as ET
import os, re, sys
from collections import defaultdict

krx_xmlns="{http://kanripo.org/ns/KRX/1.0}"
tx_xmlns="{http://kanripo.org/ns/KRX/1.0}"
xml_xmlns="{http://www.w3.org/XML/1998/namespace}"

# text type is defined on the parent of the edition element
def get_text_type(textdir, textid):
    os.chdir(textdir)
    mtree=ET.parse("Manifest.xml")
    root=mtree.getroot()
    parent_map = {c: p for p in root.iter() for c in p}
    doc = mtree.findall(f'.//{krx_xmlns}edition[@id="%s"]' % (textid))
    if len(doc) > 0:
        if 'type' in parent_map[doc[0]].attrib:
            return parent_map[doc[0]].attrib['type']
        else:
            "unknown"



def read_tokens(textdir):
    dmap=get_div_maps(textdir)
    tokd="%s/aux/tok"%(textdir)
#    tf=[a.replace("-log.xml", "") for a in os.listdir(tokd) if a.endswith("log.xml")]
    tf=[a.split("-")[0] for a in os.listdir(tokd) if a.endswith("000.xml")]
    tf.sort()
    # the sequences for every file will be stored here
    tseq = {}
    for t in tf:
        textid = t
        target = [a for a in os.listdir(tokd) if a.startswith("%s-tok" % (textid))]
        target.sort()
        t1 = []
        for t in target:
            print ("%s/%s" % (tokd, t))
            tree = ET.parse("%s/%s" % (tokd, t))
            root = tree.getroot()
            p=root.findall(f".//{tx_xmlns}t")
            for child in p:
                if 'n' in child.attrib:
                    ix = child.attrib['n']
                else:
                    ix = "no_id"
                t1.append((child.text, ix, int(child.attrib['tp']), child.attrib['pos'], child.attrib['role'] ))
        # adjust for realignment
        if (textid in dmap):
            sn=[]
            for dx in dmap[textid]:
                sn.extend(t1[slice(dx[1], dx[2])])
            tseq[textid] = sn
        else:
            tseq[textid] = t1

    return tseq


# In[5]:
def get_div_maps(textdir):
    os.chdir(textdir)
    mtree=ET.parse("Manifest.xml")
    doc = mtree.findall(f'.//{krx_xmlns}edition')
    dmap={}
    for d in doc:
        edid=d.attrib['id']
        divs=d.findall(f'{krx_xmlns}divisions/{krx_xmlns}div')
        if divs:
            mx=[]
            for div in divs:
                mx.append((int(div.attrib['sequence']), int(div.attrib['start']), int(div.attrib['end'])))
            mx=sorted(mx, key = lambda x : x[0])
            dmap[edid]=mx
    return dmap



def align_tokens(tseq, textid, dmap=None, ttype="root"):
    mq=[]
    sq=SequenceMatcher(autojunk=False)
    sq.set_seq1([a[0] for a in tseq[textid]])
    for t2 in tseq:
        if t2 != textid:
            if ttype=="rootx":
                # we ignore annotations if the source text is a root text
                sq.set_seq2([a[0] for a in tseq[t2] if not(a[4] == "n")])
            else:
                sq.set_seq2([a[0] for a in tseq[t2]])
            o=sq.get_opcodes()
            mq.append((t2, o))
    return mq


def write_table(tseq, textdir, textid):
    tokd="%s/aux/tok"%(textdir)
    tf=[a.replace("-log.xml", "") for a in os.listdir(tokd) if a.endswith("log.xml")]   
    tf.sort()
    dmap=get_div_maps(textdir)
    ttype=get_text_type(textdir, textid)
    mq=align_tokens(tseq, textid, dmap, ttype)
    sdic=[]
    for mt in range(0, len(mq)):
        lx = 0
        lid=""
        ldic=[]
        trg = mq[mt][0]
        if ttype=="rootx":
            s2=[a[0] for a in tseq[trg] if not(a[4] == "n")]
        else:
            s2=tseq[trg]
        ed="%s" % (trg)
        for tag, i1, i2, j1, j2 in mq[mt][1]:
            if tag in ['insert']:
                for l in range(j1, j2):
                    ldic.append((tag, ('i', 'i'), s2[l], ed))
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
                        if len(s2)>l+dx+1:
                            ldic.append ((tag, tseq[textid][l], s2[l+dx], ed))
                    except:
                        #maybe this happens if one of the texts is too short?
                        print("error,", tag, textid, l, trg, l+dx)
                        
        sdic.append(ldic)
        kdic=defaultdict(list)
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
            nex="<nexus xml:id='%s' tp='%d' tcount='%d'>\n" % (ix, itp, len(a) - icount)
            if not ix in kdic:
                kdic[ix] = nex
            key=ix
            if ttp < 2:
                continue
            if tx == 'd':
                val="<locationRef ed='%s' target='%s_%s' tp='%d' tcount='%d'/>\n" % (ed, ed, tx, ttp, len(a) - dcount)
            else:
                try:
                    val="<locationRef ed='%s' target='%s' tp='%d' tcount='%d'/>\n" % (ed, tx, ttp-2, len(a) - dcount)
                except:
                    print(ttp)
                    sys.exit()
            tdic[key].append(val)
    lnkd="%s/aux/lnk"%(textdir)
    os.makedirs(lnkd, exist_ok=True)
    of=open("%s/%s-nexuslist.xml" % (lnkd, textid), "w", encoding="utf-8" )
    of.write('<nexusList ed="%s" xmlns="http://kanripo.org/ns/KRX/1.0">\n' %(textid))
    k=[fx for fx in tdic.keys()]
    try:
        k=sorted(k, key = lambda x: int(re.findall("tp='(-?[0-9]+)'", x)[0]))
    except:
        pass
    for kn in k:
        of.write(kdic[kn])
        of.write("".join(tdic[kn]))
        of.write("</nexus>\n")
    of.write("</nexusList>\n")
    of.close()


def read_align_tabs(textdir):
    lnkd = "%s/aux/lnk" % (textdir)
    at=[a for a in os.listdir(lnkd) if a.endswith(".xml")]
    segs = defaultdict(list)
    for atb in at:
        tree = ET.parse("%s/%s" % (lnkd, atb))
        root = tree.getroot()
        textid = root.attrib['ed']
        for seg in root:
            segid=seg.attrib[f'{xml_xmlns}id']
            tp=seg.attrib['tp']
            tcount=seg.attrib['tcount']
            segs[segid].append((textid, segid, int(tp), int(tcount)))
            for ref in seg:
                segs[segid].append((ref.attrib['ed'], ref.attrib['target'], int(ref.attrib['tp']), int(ref.attrib['tcount'])))
    return segs

def get_alignments(ttok, s):
    "Get the alignments for a segment; ttok is the token table."
    tk = []
    for seg in s:
        idx = seg[0]
#        idx = "_".join(seg[0].split("_")[0:2])
#        if not idx in ttok:
#            idx=seg[0].split("_")[0]
        tp=seg[2]
        tcount = seg[3]
        try:
            toks = ttok[idx][tp:tp+tcount]
        except:
            print(idx, seg)
            return
        if len(toks) < 1:
            toks = [('', idx, 0)]
        tl = []
        for t in toks:
            tl.append({"t" : t[0], 'id' : t[1], 'tp' : t[2]})

        tk.append({'id': idx, 'tokens' : tl})
    #break
    return {'witnesses' : tk}
if __name__ == '__main__':
    try:
        tdir = sys.argv[1]
    except:
        tdir = os.path.abspath(".")
    tr = read_tokens(tdir)
    for src in tr:
         print (src)
         write_table(tr, tdir, src)
    print ("Wrote tables for %s" % (tdir))

#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os
import linktables

krx_xmlns="{http://kanripo.org/ns/KRX/Manifest/1.0}"
ET.register_namespace('',"http://kanripo.org/ns/KRX/Manifest/1.0")
textdir="."
segs = linktables.read_align_tabs(textdir)

tokd="%s/aux/tok"%(textdir)
#os.chdir(textdir)

mtree=ET.parse("Manifest.xml")
parent_map = {c: p for p in mtree.iter() for c in p}
edrefs = mtree.findall(f'.//{krx_xmlns}edRef')

tks = {}
for edref in edrefs:
    div = parent_map[edref]
    txtid = edref.attrib['key']
    if not txtid in tks:
        tkfiles = [f for f in os.listdir(tokd) if f.startswith(txtid)]
        tkfiles.sort()
        tx = {}
        for f in tkfiles:
            tktree = ET.parse("%s/%s" % (tokd, f))
            for t in tktree.findall('.//t'):
                tp = t.attrib['tp']
                idx = t.attrib['id']
                tx[tp] = idx
        tks[txtid] = tx

    start = edref.attrib['start']
    end = edref.attrib['end']
    elid = tks[txtid][start]
    endid = tks[txtid][end]
    for el in segs[elid]:
        if el[0] == txtid:
            continue
        nstart = int(el[2]) + 1
        key = el[0]
        ex = [a for a in segs[endid] if a[0] == key]
        if len (ex) > 0:
            nend = int(ex[0][2]) + 1
            if (nend > nstart):
                new = ET.SubElement(div, f'{krx_xmlns}edRef')
                new.attrib['key'] = key
                new.attrib['start'] = str(nstart)
                new.attrib['end'] = str(nend)


mtree.write("Manifest-n.xml", encoding="utf-8", xml_declaration=True, method="xml", short_empty_elements=True)

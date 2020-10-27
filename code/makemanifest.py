#!/usr/bin/env python3
# run this within the text directory
import os
import xml.etree.ElementTree as ET

tei="{http://www.tei-c.org/ns/1.0}"
krx="{http://kanripo.org/ns/KRX/Manifest/1.0}"
stub="""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns="http://kanripo.org/ns/KRX/Manifest/1.0">
  <description></description>
  <editions>
  %s
  </editions>
</manifest>
"""

ed_tpl =f"""<edition id="%s" format="%s" location="%s" type="%s" language="lzh">
      <description>%s</description>
</edition>
"""
tpx="doc"
d={"doc": "documentary", "int": "interpretative"}
col=[]
for tpx in ["doc", "int"]:
    eds = [a for a in os.listdir(tpx)]
    eds.sort()
    doc=[]
    for ed in eds:
        p=f"{tpx}/{ed}"
        f=[a for a in os.listdir(p) if a.endswith("xml")]
        if len(f) > 0:
            f=[a for a in os.listdir(p) if a.endswith("xml") and not ("_" in a)][0]
            tree = ET.parse(f"{p}/{f}")
            root = tree.getroot()
            titx = root.findall(f'.//{tei}title')
            if len(titx) > 0:
                tit = titx[0].text
            else:
                tit = ""
            fm="xml/TEI"
            tp=d[tpx]
        else:
            f1=[a for a in os.listdir(p) if a.endswith("txt")]
            r = [a for a in open(f"{p}/{f1[0]}").readlines() if a.startswith("#+TITLE:")][0]
            tit = r[:-1].split()[-1]
            fm="txt/mandoku"
            tp=d[tpx]
        doc.append(ed_tpl % (ed, fm, p, tp, tit))
    dx="".join(doc)
    # col.append (f"<{d[tpx]}>\n{dx}</{d[tpx]}>")
    col.append (f"{dx}")
of=open("Manifest.xml", mode="w", encoding="utf8")
of.write(stub % ("\n".join(col)))
of.close()

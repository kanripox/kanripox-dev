xquery version "3.1";

(:import module namespace http="http://expath.org/ns/http-client";
import module namespace json = "http://www.json.org"; :)

declare namespace output="http://www.w3.org/2010/xslt-xquery-serialization";
declare namespace tei= "http://www.tei-c.org/ns/1.0";

declare function local:iskanji($t as xs:integer){
   ((13311 < $t) and ($t  < 40960 ))  (: CJK and Ext A :)
     or ((63743 < $t) and ($t < 64256)) (: compatibility F900 - FAFF:)
     or ((63743 < $t) and ($t < 64256)) (: compatibility FE30 - FE4F :)
     or ((131071 < $t) and ($t < 194560)) (: 20000 - 2F7FF :) 
     or ((196607 < $t) and ($t <  201547))  (: Extension G :)
};

let $dx :=collection("file:/home/chris/Dropbox/current/kanripox-dev/KR6c0128/aux/tok")
,$sets := distinct-values($dx//div/@n)
for $s in $sets
 let $ret :=xml-to-json(  
 <map xmlns="http://www.w3.org/2005/xpath-functions">
  <array xmlns="http://www.w3.org/2005/xpath-functions" key="witnesses">
  {
 for $d in $dx//Q{}div
  let $id := data($d/@xml:id)
  where $d/@n = $s
  return
  <map xmlns="http://www.w3.org/2005/xpath-functions">
   <string key="id">{$id}</string>
   <array key="tokens">
  {
  for $t in $d//Q{}t
  return
  <map  xmlns="http://www.w3.org/2005/xpath-functions">
  <string key="t">{$t/text()}</string>
  {
  for $att in $t/@*
  return
  <string key="{name($att)}">{data($att)}</string>
  }</map>
  }</array></map>
  }</array></map>
  )
  return 
(:  http:send-request(<http:request http-version="1.1" href="http://127.0.0.1:7369/collate" method="post">
  <http:header name="Content-type" value="application/json"/>
  <http:body media-type="application/json" method="text">{$ret}</http:body></http:request>)  :)
 $ret
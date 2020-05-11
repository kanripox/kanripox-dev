<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:map="http://www.w3.org/2005/xpath-functions/map"
    xmlns:xf="http://www.w3.org/2005/xpath-functions"
    xmlns:http="http://expath.org/ns/http-client"    
    exclude-result-prefixes="#all"
    version="3.0">
<!--<xsl:output encoding="UTF-8" method="xml" indent="yes"/>        -->
<xsl:import href="/home/chris/expath/pkg/expath-http-client-saxon-0.14.0/content/xsl/expath-http-client-saxon.xsl"/>    
<xsl:output method="text" build-tree="no"/>

<!-- {
  "witnesses" : [
    {
      "id" : "A",
      "tokens" : [
          { "t" : "A", "ref" : 123 },Accept HTTP
          { "t" : "black" , "adj" : true },
          { "t" : "cat", "id" : "xyz" }
      ]
    },
    {
      "id" : "B",
      "tokens" : [
          { "t" : "A" },
          { "t" : "white" , "adj" : true },
          { "t" : "kitten.", "n" : "cat" }
      ]
    }
  ]
}
last-modified,can-write,path,length,name,is-hidden,content-type,can-read,can-execute,fetch,absolute-path,canonical-path,
 -->
<xsl:template match="t">
    <map xmlns="http://www.w3.org/2005/xpath-functions">
        <string key="t"><xsl:value-of select="string(.)"/></string>
        <xsl:for-each select="@*">
            <string key="{name(.)}"><xsl:value-of select="string(.)"/></string>
        </xsl:for-each>    
    </map>   
</xsl:template>        
        
<xsl:template name="newstart" match="/">
    <xsl:param name="path">/home/chris/Dropbox/current/kanripox-dev/KR6c0128/aux/tok</xsl:param>
    <xsl:variable name="input" select="for $m in collection(concat('file:',$path,'/?select=*.xml;metadata=yes;recurse=yes;on-error=warning')) return $m?name"/>
    <xsl:for-each-group  select="$input" group-by="tokenize(., '-')[last()]">
        <xsl:sort select="current-grouping-key()"/>
        <xsl:variable name="name" select="current-grouping-key()"/>
        <xsl:variable name="pos" select="position()"/>
        <xsl:if test="$pos lt 2">
        <xsl:variable name="wit">
    <map xmlns="http://www.w3.org/2005/xpath-functions">
    <array key="witnesses">    
        <xsl:for-each select="current-group()">
            <xsl:sort select="."/>
            <xsl:call-template name="procgroup">
                <xsl:with-param name="group" select="."/>
            </xsl:call-template>
        </xsl:for-each>
    </array></map>
        </xsl:variable>
         <xsl:variable name="req" as="element()">   
            <http:request href="http://localhost:7369/collate" method="post">
                <http:body media-type="application/json">
                    <xsl:value-of select="xf:xml-to-json($wit)"/>
                </http:body>
            </http:request>
         </xsl:variable>
        <xsl:sequence select="http:send-request($req)"/>    
        </xsl:if>    
    </xsl:for-each-group>    
</xsl:template>
<!-- process a group of (corresponding) token files -->
    <!-- <xsl:variable name="ind"
							select="document(concat('http://chw.zinbun.kyoto-u.ac.jp:8080/exist/servlet/tkb/bin/pname.xql?query=',
											$rm))/result"/> 
 -->
<xsl:template name="procgroup">
    <xsl:param name="group"/>
    <xsl:for-each select="$group">
        <xsl:variable name="file" select="."/>
        <map xmlns="http://www.w3.org/2005/xpath-functions">
            <string key="id"><xsl:value-of select="tokenize(tokenize($file, '/')[last()], '-')[1]"/></string>
            <array key="tokens">
               <xsl:apply-templates select="doc(.)//t"/>
            </array>
        </map>    
    </xsl:for-each>
</xsl:template>
    
    
</xsl:stylesheet>
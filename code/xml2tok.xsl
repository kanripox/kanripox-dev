<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:local="http://wittern.org/local"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs local tei"
    version="2.0">
<xsl:output encoding="UTF-8" method="xml" indent="yes"/>        
<xsl:variable name="chunksize" select="10000" as="xs:integer"/>    
<xsl:param name="path"></xsl:param>    
<xsl:function name="local:iskanji">
    <xsl:param name="t" as="xs:integer"/>
    <xsl:value-of select="((13311 &lt; $t) and ($t  &lt; 40960 ))  (: CJK and Ext A :)
     or ((63743 &lt; $t) and ($t &lt; 64256)) (: compatibility F900 - FAFF:)
     or ((65071 &lt; $t) and ($t &lt; 65104)) (: compatibility FE30 - FE4F :)
     or ((131071 &lt; $t) and ($t &lt; 194560)) (: 20000 - 2F7FF :) 
     or ((196607 &lt; $t) and ($t &lt;  201547))  (: Extension G :)
     or ((57343 &lt; $t) and ($t &lt;  63744))  (: PUA :)
     or ((983039 &lt; $t) and ($t &lt;  1048574))  (: PUA 15 :)
     or ((1048575 &lt; $t) and ($t &lt;  1114110))  (: PUA 16 :)
     "/>
 
</xsl:function>
<xsl:template name="newstart" match="/">
    <xsl:param name="path"></xsl:param>
    <xsl:param name="textid"/>
    <xsl:param name="c"/>
    <xsl:variable name="docid" select="$c/child::tei:*[1]/@xml:id"/>
    <xsl:variable name="tok">
    <xsl:for-each select="$c//text()">
        <xsl:variable name="el" select="ancestor::tei:*[position() = 1 to 2]"/>
        <xsl:variable name="pc" select="preceding::tei:*[1]"/> 
        <xsl:variable name="id" select="$el/@xml:id"/>
        <xsl:variable name="tx" select="."/>
        <xsl:variable name="cp" select="string-to-codepoints(.)"/>
        <xsl:for-each select="$cp">
           <xsl:variable name="pos" select="position()"/>
            <xsl:if test="local:iskanji(.)=true()">
            <xsl:variable name="ms" as="xs:int+">
                <xsl:for-each select="$cp">
                <xsl:if test="local:iskanji(.)=true()">
                 <xsl:value-of select="position()"/>   
                </xsl:if>    
               </xsl:for-each>     
            </xsl:variable>    
            <xsl:variable name="p">
                <xsl:if test="$pos gt 1">
                <xsl:for-each select="$cp">
                    <xsl:variable name="this" select="."/>
                    <xsl:variable name="lp" select="position()"/>
                    <!-- now we are looking at the previous three.  Better would be a way to find the adjacent one only -->
                 <xsl:if test="(($lp &lt; $pos) and ($lp &gt; $pos - 3) and local:iskanji($this) = false() and local:iskanji($cp[$pos - 1]) = false())">
                     <xsl:value-of select="codepoints-to-string($this)"/>
                 </xsl:if>    
                </xsl:for-each>
                </xsl:if>    
            </xsl:variable>
            <xsl:variable name="f">
                <xsl:if test="$pos lt count($cp)">
                <xsl:for-each select="$cp">
                    <xsl:variable name="this" select="."/>
                <xsl:variable name="lp" select="position()"/>
                 <xsl:if test="($lp &gt; $pos) and ($lp &lt; $pos + 3) and local:iskanji($this) = false() and local:iskanji($cp[$pos + 1]) = false()">
                     <xsl:value-of select="codepoints-to-string($this)"/>
                 </xsl:if>    
                </xsl:for-each>
                </xsl:if>    
            </xsl:variable>
            
            <xsl:element name="t">
                <!-- count the text nodes between here and the milestone element.  -->
                <xsl:variable name="xn">
                    <xsl:number select="$tx" from="$pc" count="text()" level="any"/>
                </xsl:variable>
<!--                <xsl:attribute name="pc" select="$xn"/>                    -->
                <!-- the first kanji after a pb gets the ms attribute -->
                <xsl:if test="(local-name($pc) = 'pb' or local-name($pc)='lb') and $pos = $ms[1] and $xn = 1">
                    <xsl:attribute name="ms" select="concat(local-name($pc), '-', $pc/@xml:id)"></xsl:attribute>
                </xsl:if>
                <xsl:if test="string-length($p) &gt; 0">
                    <xsl:attribute name="p" select="string-join($p)"/>
                </xsl:if>
                <xsl:if test="string-length($f) &gt; 0">
                    <xsl:attribute name="f" select="string-join($f)"/>
                </xsl:if>
                <xsl:if test="string-length($id[last()]) &gt; 0">
                    <xsl:attribute name="id" select="$id[last()]"/>
                </xsl:if>
                <xsl:attribute name="el" select="$el/local-name()"/>
                <xsl:attribute name="pos" select="$pos"/>
<!--                <xsl:attribute name="c" select="$tx"/>-->
                <xsl:value-of select="codepoints-to-string(.)"/>
            </xsl:element>
            </xsl:if>       
        </xsl:for-each>
    </xsl:for-each>
    </xsl:variable>
   <xsl:variable name="outputpath" select="concat($path, '/aux/tok/')"/> 
   <xsl:result-document href="{$outputpath}{$docid}-log.xml">
    <div docid="{$docid}"><head><xsl:value-of select="current-dateTime()"/></head>
    <xsl:for-each select="0 to xs:integer(count($tok//t) div $chunksize)">
        <xsl:variable name="pos-str" select="format-number(., '000')"/>
        <xsl:variable name="pos" select="."/>
        <xsl:variable name="start" as="xs:integer" select="($pos * $chunksize) + 1"/>    
        <li n="{$pos}"><ref target="#{$docid}-tok-{$pos-str}"/>
            <p start="{$start}"><xsl:value-of select="subsequence($tok//t/text(), $start, $chunksize )"/></p>
        </li>
        <xsl:result-document href="{$outputpath}{$docid}-tok-{$pos-str}.xml">
            <div xml:id="{$docid}-tok-{$pos-str}" n="tok-{$pos-str}">
            <xsl:for-each select="subsequence($tok//t, $start, $chunksize )">
                <xsl:variable name="tp" as="xs:integer" select="$start + position() - 1"/>
               <xsl:copy>
                 <xsl:attribute name="tp"><xsl:value-of select="$tp"/></xsl:attribute>
                 <!-- at this point, we might also add a normalization -->  
                 <xsl:apply-templates select="@*|node()" />
               </xsl:copy>
            </xsl:for-each>
            </div>    
        </xsl:result-document>
    </xsl:for-each>
    </div>    
   </xsl:result-document> 
<!--    <xsl:value-of select="local:iskanji(string-to-codepoints('	'))"/>-->
</xsl:template>    
<xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
</xsl:template>
    
</xsl:stylesheet>
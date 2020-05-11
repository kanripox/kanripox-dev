<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:local="http://wittern.org/local"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs local tei"
    version="2.0">
<xsl:output encoding="UTF-8" method="xml" indent="yes"/>    
<xsl:import href="xml2tok.xsl"/>    
<!--<xsl:import href="test.xsl"/>    -->
<xsl:param name="path"></xsl:param>    
<xsl:param name="textid"></xsl:param>    
<xsl:variable name="files" select="collection(concat('file:',$path,'/?select=*.xml;metadata=yes;recurse=yes;on-error=warning'))"/>    
<xsl:template name="start">
    <xsl:for-each select="for $m in $files return $m?name">
        <xsl:variable name="cf" select="tokenize(., '/')[last()]"/>
        <xsl:if test="not(matches($cf, '[_-]'))">
<!--               <xsl:value-of select="."/>                     -->
        <xsl:call-template name="newstart">
            <xsl:with-param name="path" select="$path"/>
            
            <xsl:with-param name="c" select="doc(.)"/>
        </xsl:call-template>
        </xsl:if>
    </xsl:for-each>
</xsl:template>    
</xsl:stylesheet>
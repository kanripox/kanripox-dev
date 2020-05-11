<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
  xpath-default-namespace="http://www.tei-c.org/ns/1.0"
  xmlns:krx="http://kanripo.org/ns/1.0"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  >
  <!-- the magic constant for calculating the PUA character value-->
  <!-- We use the same as in KR puamagic = 1060864 -->
  <xsl:variable name="krpmagic" as="xs:integer">1060864</xsl:variable>
  <xsl:variable name="cbgaiji" as="xs:integer">983040</xsl:variable>

  
  <xsl:function name="krx:hexval"  >
        <xsl:param name="str"/>
        <xsl:variable name="seq" select="string-to-codepoints(lower-case($str))"/>
        <xsl:variable name="h" select="string-to-codepoints('0123456789abcdef')"/>
        <xsl:variable name="ret">
            <xsl:for-each select="$seq">
                <xsl:value-of select="index-of($h, .) -1" />
                <xsl:if test="position() != last()">,</xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="a1" select="16* xs:integer(tokenize($ret, ',')[1]) + xs:integer(tokenize($ret, ',')[2])" as="xs:integer"/>
        <xsl:variable name="a2" select="16* xs:integer(tokenize($ret, ',')[3]) + xs:integer(tokenize($ret, ',')[4])" as="xs:integer"/>
        <xsl:value-of select="256*$a1 + $a2"/>
    </xsl:function>



   <xsl:template match="tei:g">
    <xsl:choose>
      <xsl:when test="contains(@ref, '#KR')">
         <xsl:value-of   select="codepoints-to-string(xs:integer(substring(@ref, 3)) +   $krpmagic)"/>
      </xsl:when>
      <xsl:when test="contains(@ref, '#CB')">
         <xsl:value-of   select="codepoints-to-string(xs:integer(substring(@ref, 4)) +   $cbgaiji)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


</xsl:stylesheet>

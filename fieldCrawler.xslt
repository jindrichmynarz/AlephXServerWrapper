<?xml version="1.0" encoding="utf-8"?>
 <xsl:stylesheet
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        version="1.0">
    <xsl:output method="xml"
                         indent="yes"
                         omit-xml-declaration="yes"/>

    <xsl:template match="/find-doc">
      <xsl:apply-templates select="*">
      <xsl:with-param name="path" select="name()"/>
      </xsl:apply-templates>  
    </xsl:template>
    
    <xsl:template match="*">
      <xsl:param name="path"/>
      <xsl:variable name="attributes">
        <xsl:call-template name="getAttributes"/>
      </xsl:variable>
      
      <xsl:variable name="storedPath" select="concat($path,'/',name(),$attributes)"/>
      
      <xsl:if test="count(*)=0">
        <xsl:variable name="myAttributes">
        <xsl:call-template name="getAttributes"/>
      </xsl:variable>
        <xsl:value-of select="concat($path, '/',name(), $myAttributes, '&#10;')" disable-output-escaping="yes"/>
      </xsl:if>
       
      <xsl:apply-templates select="*">
       <xsl:with-param name="path" select="$storedPath"/>
      </xsl:apply-templates>  
    </xsl:template>
    
    <xsl:template name="getAttributes">
      <xsl:for-each select="@*">
        <xsl:value-of select="concat('[', '@', name(), '=', '&#34;', ., '&#34;', ']')"/>  
      </xsl:for-each>
    </xsl:template>

</xsl:stylesheet> 


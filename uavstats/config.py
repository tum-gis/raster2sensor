import os
from dotenv import load_dotenv, find_dotenv
from string import Template
from typing import TypedDict

load_dotenv(find_dotenv())


GEOSERVER_URL = os.getenv('GEOSERVER_URL')
GEOSERVER_USER = os.getenv('GEOSERVER_USER')
GEOSERVER_PASSWORD = os.getenv('GEOSERVER_PASSWORD')

# DATA DIRECTORIES & FILES
GIS_DATA_DIR = './gis_data'
if not os.path.exists(GIS_DATA_DIR):
    os.makedirs(GIS_DATA_DIR)

VARI_GEO_TIFF = os.path.join(GIS_DATA_DIR, 'VARI.tif')
OUTPUT_JSON = os.path.join(GIS_DATA_DIR, 'output.json')


# LAND PARCELS
LAND_PARCELS_FILE = os.getenv('LAND_PARCELS_FILE')
LAND_PARCELS_ID_FIELD = os.getenv('LAND_PARCELS_ID_FIELD')
PROJECT_ID = os.getenv('PROJECT_ID')

# SENSOR THINGS API


class Datastream(TypedDict):
    name: str
    description: str
    sensor_id: int
    observed_property_id: int


DATASTREAMS: list[Datastream] = [{
    'name': Template('$parcel_id - NDVI'),
    'description': Template('NDVI Zonal Stats for $parcel_id'),
    'sensor_id': 1,
    'observed_property_id': 1,
}]


# WPS REQUESTS
WPS_URL = f'{
    GEOSERVER_URL}/geoserver/ows?service=WPS&version=1.0.0&request=Execute'
WPS_GET_CAPABILITIES_URL = f'{
    GEOSERVER_URL}/geoserver/ows?service=WPS&version=1.0.0&request=GetCapabilities'

XML_BODY_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?><wps:Execute version="1.0.0" service="WPS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.opengis.net/wps/1.0.0" xmlns:wfs="http://www.opengis.net/wfs" xmlns:wps="http://www.opengis.net/wps/1.0.0" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" xmlns:wcs="http://www.opengis.net/wcs/1.1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xsi:schemaLocation="http://www.opengis.net/wps/1.0.0 http://schemas.opengis.net/wps/1.0.0/wpsAll.xsd">
  <ows:Identifier>ras:RasterZonalStatistics</ows:Identifier>
  <wps:DataInputs>
    <wps:Input>
      <ows:Identifier>data</ows:Identifier>
      <wps:Reference mimeType="image/tiff" xlink:href="http://geoserver/wcs" method="POST">
        <wps:Body>
          <wcs:GetCoverage service="WCS" version="1.1.1">
            <ows:Identifier>FAIRagro:VARI</ows:Identifier>
            <wcs:DomainSubset>
              <ows:BoundingBox crs="http://www.opengis.net/gml/srs/epsg.xml#25832">
                <ows:LowerCorner>618000.0 5451000.0</ows:LowerCorner>
                <ows:UpperCorner>619000.0 5452000.0</ows:UpperCorner>
              </ows:BoundingBox>
            </wcs:DomainSubset>
            <wcs:Output format="image/tiff"/>
          </wcs:GetCoverage>
        </wps:Body>
      </wps:Reference>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>band</ows:Identifier>
      <wps:Data>
        <wps:LiteralData>0</wps:LiteralData>
      </wps:Data>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>zones</ows:Identifier>
      <wps:Reference mimeType="text/xml" xlink:href="http://geoserver/wfs" method="POST">
        <wps:Body>
          <wfs:GetFeature service="WFS" version="1.0.0" outputFormat="GML2" xmlns:FAIRagro="fairagro">
            <wfs:Query typeName="FAIRagro:parcels"/>
          </wfs:GetFeature>
        </wps:Body>
      </wps:Reference>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>classification</ows:Identifier>
      <wps:Reference mimeType="image/tiff" xlink:href="http://geoserver/wcs" method="POST">
        <wps:Body>
          <wcs:GetCoverage service="WCS" version="1.1.1">
            <ows:Identifier>FAIRagro:VARI</ows:Identifier>
            <wcs:DomainSubset>
              <ows:BoundingBox crs="http://www.opengis.net/gml/srs/epsg.xml#25832">
                <ows:LowerCorner>618000.0 5451000.0</ows:LowerCorner>
                <ows:UpperCorner>619000.0 5452000.0</ows:UpperCorner>
              </ows:BoundingBox>
            </wcs:DomainSubset>
            <wcs:Output format="image/tiff"/>
          </wcs:GetCoverage>
        </wps:Body>
      </wps:Reference>
    </wps:Input>
  </wps:DataInputs>
  <wps:ResponseForm>
    <wps:RawDataOutput mimeType="application/json">
      <ows:Identifier>statistics</ows:Identifier>
    </wps:RawDataOutput>
  </wps:ResponseForm>
</wps:Execute>
"""

XML_BODY_IMAGE_BASE64 = Template("""<?xml version="1.0" encoding="UTF-8"?><wps:Execute version="1.0.0" service="WPS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.opengis.net/wps/1.0.0" xmlns:wfs="http://www.opengis.net/wfs" xmlns:wps="http://www.opengis.net/wps/1.0.0" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" xmlns:wcs="http://www.opengis.net/wcs/1.1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xsi:schemaLocation="http://www.opengis.net/wps/1.0.0 http://schemas.opengis.net/wps/1.0.0/wpsAll.xsd">
  <ows:Identifier>ras:RasterZonalStatistics</ows:Identifier>
  <wps:DataInputs>
    <wps:Input>
      <ows:Identifier>data</ows:Identifier>
     <wps:Data>
        <wps:ComplexData mimeType="image/tiff">$image_base64</wps:ComplexData>
      </wps:Data>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>band</ows:Identifier>
      <wps:Data>
        <wps:LiteralData>0</wps:LiteralData>
      </wps:Data>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>zones</ows:Identifier>
      <wps:Reference mimeType="text/xml" xlink:href="http://geoserver/wfs" method="POST">
        <wps:Body>
          <wfs:GetFeature service="WFS" version="1.0.0" outputFormat="GML2" xmlns:FAIRagro="fairagro">
            <wfs:Query typeName="FAIRagro:parcels"/>
          </wfs:GetFeature>
        </wps:Body>
      </wps:Reference>
    </wps:Input>
    <wps:Input>
      <ows:Identifier>classification</ows:Identifier>
           <wps:Data>
        <wps:ComplexData mimeType="image/tiff">$image_base64</wps:ComplexData>
      </wps:Data>
    </wps:Input>
  </wps:DataInputs>
  <wps:ResponseForm>
    <wps:RawDataOutput mimeType="application/json">
      <ows:Identifier>statistics</ows:Identifier>
    </wps:RawDataOutput>
  </wps:ResponseForm>
</wps:Execute>
""")


XML_BODY_UPLOAD = Template("""<wps:Execute service="WPS" version="1.0.0"
             xmlns:wps="http://www.opengis.net/wps/1.0.0"
             xmlns:ows="http://www.opengis.net/ows/1.1"
             xmlns:xlink="http://www.w3.org/1999/xlink"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://www.opengis.net/wps/1.0.0
                                 http://schemas.opengis.net/wps/1.0.0/wpsExecute_request.xsd">
  <ows:Identifier>gs:Import</ows:Identifier>
  <wps:DataInputs>
    <wps:Input>
      <ows:Identifier>contents</ows:Identifier>
      <wps:Data>
        <wps:ComplexData mimeType="application/zip"><![CDATA[
          <import>
            <data type="file" format="geotiff">
              <file>$encoded_geotiff</file>
            </data>
            <targetStore name="test_upload" type="dataStore">
              <coverageStore>
                <workspace>FAIRagro</workspace>
                 <name>test_upload</name>
              </coverageStore>
            </targetStore>
          </import>
        ]]></wps:ComplexData>
      </wps:Data>
    </wps:Input>
  </wps:DataInputs>
  <wps:ResponseForm>
    <wps:RawDataOutput mimeType="application/json">
      <ows:Identifier>result</ows:Identifier>
    </wps:RawDataOutput>
  </wps:ResponseForm>
</wps:Execute>""")

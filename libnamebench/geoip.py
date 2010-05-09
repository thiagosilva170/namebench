# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Class used for determining GeoIP location."""

import re
import tempfile

# external dependencies (from third_party)
try:
  import third_party
except ImportError:
  pass

import httplib2
import simplejson

# TODO(tstromberg): Remove if we aren't going to use it.
#import pygeoip

import util
    
def GetFromGoogleJSAPI():
  """Using the Google JSAPI API, get the geodata for the current IP.
  
  NOTE: This will return the geodata for the proxy server in use!
  """
  h = httplib2.Http(tempfile.gettempdir(), timeout=10)
  resp, content = h.request("http://google.com/jsapi", 'GET')  
  geo_matches = re.search('google.loader.ClientLocation = ({.*?});', content)  
  if geo_matches:
    return simplejson.loads(geo_matches.group(1))
  else:
    return {}

def GetFromMaxmindJSAPI():
  h = httplib2.Http(tempfile.gettempdir(), timeout=10)
  resp, content = h.request("http://j.maxmind.com/app/geoip.js", 'GET')
  results = re.findall("geoip_(.*?)\(.*?\'(.*?)\'", content)
  if results:
    return dict(results)
  else:
    return {}

def GetFromMaxmindGeoLite():
  """Currently obsoleted (data file was too large to include!)"""
  data_file = util.FindDataFile('third_party/maxmind/GeoLiteCity.dat')
  print data_file
  geo_city = pygeoip.GeoIP(data_file)
  external_ip = util.GetExternalIPFromGoogle()
  print external_ip
  return geo_city.record_by_addr(external_ip)

def GetGeoData():
  try:
    jsapi_data = GetFromGoogleJSAPI()
    if jsapi_data:
      return jsapi_data
    else:
      return GetFromMaxmindJSAPI()
  except:
    print "Failed to get Geodata: %s" % util.GetLastExceptionString()
    return {}

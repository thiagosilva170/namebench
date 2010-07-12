#!/usr/bin/env python
# Copyright 2009 Google Inc. All Rights Reserved.
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

"""Define and process configuration from command-line or config file."""

__author__ = 'tstromberg@google.com (Thomas Stromberg)'


import ConfigParser
import csv
import optparse
import os.path
import re
import StringIO
import tempfile

import third_party

# from third_party
import httplib2

import data_sources
import util
import addr_util
import version

TRUNK_URL = 'http://namebench.googlecode.com/svn/trunk/'


def GetMergedConfiguration():
  """Get all of our configuration setup."""
  options = ParseCommandLineArguments()
  return MergeConfigurationFileOptions(options)

def ParseCommandLineArguments(default_config_file='config/namebench.cfg'):
  """Get our option configuration setup.

  Args:
    default_config_file: path to configuration (may be relative)

  Returns:
    stuple of (OptionParser object, args)
  """
  ds = data_sources.DataSources()
  import_types = ds.ListSourceTypes()
  parser = optparse.OptionParser()
  parser.add_option('-6', '--ipv6_only', dest='ipv6_only', action='store_true', help='Only include IPv6 name servers')
  parser.add_option('-4', '--ipv4_only', dest='ipv4_only', action='store_true', help='Only include IPv4 name servers')
  parser.add_option('-a', '--include-all', dest='include_all', action='store_true', help='Include all possible DNS servers.')
  parser.add_option('-c', '--csv_output', dest='csv_file', default=None, help='Filename to write query details to (CSV)')
  parser.add_option('-C', '--enable-censorship-checks', dest='enable_censorship_checks', action='store_true', help='Enable censorship checks')
  parser.add_option('-g', '--include-global', dest='include_global', action='store_true', help='Only test globally accessible nameservers.')
  parser.add_option('-H', '--hide_results', dest='hide_results', action='store_true',  help='Upload results, but keep them hidden from indexes.')
  parser.add_option('-i', '--input', dest='input_source', help=('Import hostnames from an filename or application (%s)' % ', '.join(import_types)))
  parser.add_option('-I', '--invalidate_cache', dest='invalidate_cache', action='store_true', help='Force health cache to be invalidated')
  parser.add_option('-J', '--benchmark_threads', dest='benchmark_thread_count', type='int', help='# of benchmark threads to use')
  parser.add_option('-j', '--health_threads', dest='health_thread_count', type='int', help='# of health check threads to use')
  parser.add_option('-l', '--runs', dest='run_count', default=1, type='int', help='Number of test runs to perform on each nameserver.')
  parser.add_option('-m', '--select_mode', dest='select_mode', default='automatic', help='Selection algorithm to use (weighted, random, chunk)')
  parser.add_option('-n', '--num_servers', dest='num_servers', type='int', help='Number of nameservers to include in test')
  parser.add_option('-o', '--output', dest='output_file', default=None, help='Filename to write output to')
  # Silly Mac OS X adding -psn_0_xxxx
  parser.add_option('-p', '--psn')
  parser.add_option('-P', '--ping_timeout', dest='ping_timeout', type='float', help='# of seconds ping requests timeout in.')
  parser.add_option('-q', '--query_count', dest='query_count', type='int', help='Number of queries per run.')
  parser.add_option('-r', '--include-regional', dest='include_regional', action='store_true', help='Only test current system nameservers.')
  parser.add_option('-s', '--include-system', dest='include_system', action='store_true',  help='Only test nameservers passed as arguments')
  parser.add_option('-S', '--servers', dest='servers', default=[], help='A list of servers to test (can also be passed as arguments)')
  parser.add_option('-t', '--template', dest='template', default='html', help='Template to use for output generation (ascii, html, resolv.conf)')
  parser.add_option('-U', '--site_url', dest='site_url', help='URL to upload results to (http://namebench.appspot.com/)')
  parser.add_option('-u', '--upload_results', dest='upload_results', action='store_true', help='Upload anonymized results to SITE_URL (False)')
  parser.add_option('-w', '--open_webbrowser', dest='open_webbrowser', action='store_true', help='Opens the final report in your browser')
  parser.add_option('-x', '--no_gui', dest='no_gui', action='store_true', help='Disable GUI')
  parser.add_option('-Y', '--health_timeout', dest='health_timeout', type='float', help='health check timeout (in seconds)')
  parser.add_option('-y', '--timeout', dest='timeout', type='float', help='# of seconds general requests timeout in.')
  parser.add_option('-z', '--config', dest='config', default=default_config_file, help='Config file to use.')

  options, args = parser.parse_args()
  if args:
    options.servers.extend(addr_util.ExtractIPTuplesFromString(' '.join(args)))
  return options

def GetLatestSanityChecks():
  return GetLatestConfig('config/hostname_reference.cfg')

def GetLocalSanityChecks():
  return _GetLocalConfig('config/hostname_reference.cfg')

def GetNameServerData(filename='config/servers.csv'):
  server_file = util.FindDataFile(filename)
  return _ParseNameServerListing(open(server_file))

def _ParseNameServerListing(fp):
  fields = ['ip', 'category', 'provider', 'instance', 'hostname', 'location',
            'coords', 'asn', 'list_note', 'urls']
  reader = csv.DictReader(fp, fieldnames=fields)
  ns_data = {}

  for row in reader:
    ip = row['ip']
    if row['location']:
      row['country_code'] = row['location'].split('/')[0]
    else:
      row['country_code'] = None

    if row['coords']:
      row['lat'], row['lon'] = row['coords'].split(',')
    else:
      row['lat'] = row['lon'] = None

    # While a DNS server can only have one category, it may end up having
    # multiple tags: global, assigned, system
    row['tags'] = set(row['category'])
    if '.' in row['ip']:
      row['tags'].add('ipv4')
    elif ':' in row['ip']:
      row['tags'].add('ipv6')

    row['urls'] = row['urls'].split(' ')
    if row['instance']:
      row['name'] = "%s (%s)" % (row['provider'], row['instance'])
    else:
      row['name'] = row['provider']

    ns_data[ip] = row
    
  return ns_data

def GetSanityChecks():
  return GetAutoUpdatingConfigFile('config/sanity_checks.cfg')

def _GetLocalConfig(conf_file):
  """Read a simple local config file."""

  local_config = _ReadConfigFile(conf_file)
  return _ExpandConfigSections(local_config)

def _ReadConfigFile(conf_file):
  """Read a local config file."""
  ref_file = util.FindDataFile(conf_file)
  local_config = ConfigParser.ConfigParser()
  local_config.read(ref_file)
  return local_config


def GetAutoUpdatingConfigFile(conf_file):
  """Get the latest copy of the config file"""

  local_config = _ReadConfigFile(conf_file)
  download_latest = int(local_config.get('config', 'download_latest'))
  local_version = int(local_config.get('config', 'version'))
  
  if download_latest == 0:
    return _ExpandConfigSections(local_config)
    
  h = httplib2.Http(tempfile.gettempdir(), timeout=10)
  url = '%s/%s' % (TRUNK_URL, conf_file)
  content = None
  try:
    unused_resp, content = h.request(url, 'GET')
    remote_config = ConfigParser.ConfigParser()
  except:
    print '* Unable to fetch remote %s: %s' % (conf_file, util.GetLastExceptionString())
    return _ExpandConfigSections(local_config)

  if content and '[config]' in content:
    fp = StringIO.StringIO(content)
    try:
      remote_config.readfp(fp)
    except:
      print '* Unable to read remote %s: %s' % (conf_file, util.GetLastExceptionString())
      return _ExpandConfigSections(local_config)

  if int(remote_config.get('config', 'version')) > local_version:
    print '- Using %s' % url
    return _ExpandConfigSections(remote_config)
  else:
    return _ExpandConfigSections(local_config)

def _ExpandConfigSections(config):
  return dict([ (y, config.items(y)) for y in config.sections() if y != 'config' ])


def MergeConfigurationFileOptions(options):
  """Process configuration file, merge configuration with OptionParser.

  Args:
    options: optparse.OptionParser() object

  Returns:
    options: optparse.OptionParser() object
    global_ns: A list of global nameserver tuples.
    regional_ns: A list of regional nameservers tuples.

  Raises:
    ValueError: If we are unable to find a usable configuration file.
  """
  config = ConfigParser.ConfigParser()
  full_path = util.FindDataFile(options.config)
  config.read(full_path)
  if not config or not config.has_section('general'):
    raise ValueError('Could not find usable configuration in %s (%s)' % (full_path, options.config))
  general = dict(config.items('general'))

  # -U implies -u
  if options.site_url:
    options.upload_results = True

  for option in general:
    if not getattr(options, option, None):
      if 'timeout' in option:
        value = float(general[option])
      elif 'count' in option or 'num' in option or 'hide' in option:
        value = int(general[option])
      else:
        value = general[option]
      setattr(options, option, value)

  for key in ('input_file', 'output_file', 'csv_file', 'input_source'):
    value = getattr(options, key, None)
    if value:
      setattr(options, key, os.path.expanduser(value))

  # This makes it easier to pass around later. Lazy-hack.
  options.version = version.VERSION
  return options

if __name__ == '__main__':
  print GetLocalNameServerList()

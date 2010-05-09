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

"""Report generation class."""

import csv
import datetime
import operator
import os.path
import platform

# external dependencies (from third_party)
try:
  import third_party
except ImportError:
  pass

import jinja2
import simplejson

import charts
import nameserver
import selectors
import util


FAQ_MAP = {
  'NXDOMAIN': 'http://code.google.com/p/namebench/wiki/FAQ#What_does_"NXDOMAIN_hijacking"_mean?',
  'Wrong result': 'http://code.google.com/p/namebench/wiki/FAQ#What_does_"Incorrect_result_for..."_mean?'
}

# Only bother showing a percentage if we have this many tests.
MIN_RELEVANT_COUNT = 50

class ReportGenerator(object):
  """Generate reports - ASCII, HTML, etc."""

  def __init__(self, config, nameservers, results, index=None, geodata=None,
               status_callback=None):
    """Constructor.

    Args:
      nameservers: A list of nameserver objects to include in the report.
      results: A dictionary of results from Benchmark.Run()
      index: A dictionary of results for index hosts.
    """
    self.nameservers = nameservers
    self.results = results
    self.index = index
    self.config = config
    self.geodata = geodata
    self.status_callback = status_callback
    self.cached_averages = {}

  def msg(self, msg, **kwargs):
    if self.status_callback:
      self.status_callback(msg, **kwargs)

  def ComputeAverages(self):
    """Process all runs for all hosts, yielding an average for each host."""
    if len(self.results) in self.cached_averages:
      return self.cached_averages[len(self.results)]
    
    records = []
    for ns in self.results:
      failure_count = 0
      nx_count = 0
      run_averages = []

      for test_run in self.results[ns]:
        # x: record, req_type, duration, response
        total_count = len(test_run)
        failure_count += len([x for x in test_run if not x[3]])
        nx_count += len([x for x in test_run if x[3] and not x[3].answer])
        duration = sum([x[2] for x in test_run])
        run_averages.append(duration / len(test_run))

      # This appears to be a safe use of averaging averages
      overall_average = util.CalculateListAverage(run_averages)
      (fastest, slowest) = self.FastestAndSlowestDurationForNameServer(ns)

      records.append((ns, overall_average, run_averages, fastest, slowest,
                     failure_count, nx_count, total_count))
    self.cached_averages[len(self.results)] = records
    return self.cached_averages[len(self.results)]

  def FastestAndSlowestDurationForNameServer(self, ns):
    """For a given nameserver, find the fastest/slowest non-error durations."""

    fastest_duration = 2**32
    slowest_duration = -1
    
    durations = []
    for test_run_results in self.results[ns]:
      for (host, req_type, duration, response, error_msg) in test_run_results:
        durations.append(duration)
        if response and response.answer:
          if duration < fastest_duration:
            fastest_duration = duration
        if duration > slowest_duration:
          slowest_duration = duration

    # If we have no error-free durations, settle for anything.
    if fastest_duration == 2**32:
      fastest_duration = min(durations)
    if slowest_duration == -1:
      slowest_duration = max(durations)
    print "fastest for %s: %s" % (ns, fastest_duration)
    return (fastest_duration, slowest_duration)

  def FastestNameServerResult(self):
    """Process all runs for all hosts, yielding an average for each host."""
    # TODO(tstromberg): This should not count queries which failed.
    fastest = [(ns, self.FastestAndSlowestDurationForNameServer(ns)[0]) for ns in self.results]
    return sorted(fastest, key=operator.itemgetter(1))

  def BestOverallNameServer(self):
    sorted_averages = sorted(self.ComputeAverages(), key=operator.itemgetter(1))
    hosts = [ x[0] for x in sorted_averages ]
    for host in [ x[0] for x in sorted_averages ]:
      if not host.is_failure_prone:
        return host
    # return something if none of them are good.
    return hosts[0]

  def NearestNameServers(self, count=2):
    min_responses = sorted(self.FastestNameServerResult(),
                           key=operator.itemgetter(1))
    return [x[0] for x in min_responses][0:count]

  def _LowestLatencyAsciiChart(self):
    """Return a simple set of tuples to generate an ASCII chart from."""
    fastest = self.FastestNameServerResult()
    slowest_result = fastest[-1][1]
    chart = []
    for (ns, duration) in fastest:
      textbar = util.DrawTextBar(duration, slowest_result)
      chart.append((ns.name, textbar, duration))
    return chart

  def _MeanRequestAsciiChart(self):
    sorted_averages = sorted(self.ComputeAverages(), key=operator.itemgetter(1))
    max_result = sorted_averages[-1][1]
    chart = []
    for result in sorted_averages:
      (ns, overall_mean) = result[0:2]
      textbar = util.DrawTextBar(overall_mean, max_result)
      chart.append((ns.name, textbar, overall_mean))
    return chart

  def CreateReport(self, format='ascii', output_fp=None, csv_path=None):
    
    # First generate all of the charts necessary.
    if format == 'ascii':
      lowest_latency = self._LowestLatencyAsciiChart()
      mean_duration = self._MeanRequestAsciiChart()
    else:
      lowest_latency = None
      mean_duration = None

    sorted_averages = sorted(self.ComputeAverages(), key=operator.itemgetter(1))
    runs_data = [(x[0].name, x[2]) for x in sorted_averages]
    mean_duration_url = charts.PerRunDurationBarGraph(runs_data)
    min_duration_url = charts.MinimumDurationBarGraph(self.FastestNameServerResult())
    distribution_url_200 = charts.DistributionLineGraph(self.DigestedResults(),
                                                        scale=200)
    distribution_url = charts.DistributionLineGraph(self.DigestedResults(), scale=self.config.timeout * 1000)
    
    # Now generate all of the required textual information.
    ns_summary = self._GenerateNameServerSummary()
    best_ns = self.BestOverallNameServer()
    recommended = [best_ns] + [x for x in self.NearestNameServers(3) if x.ip != best_ns.ip][0:2]

    compare_title = 'Undecided'
    compare_subtitle = 'Not enough servers to compare.'
    compare_reference = None
    for ns_record in ns_summary:
      if ns_record.get('is_reference'):
        if len(ns_record['durations'][0]) >= MIN_RELEVANT_COUNT:
          compare_reference = ns_record
          compare_title = "%0.1f%%" % [x['diff'] for x in ns_summary if x['ip'] == best_ns.ip][0]
          compare_subtitle = 'Faster'
        else:
          compare_subtitle = 'Too few tests (needs %s)' % (MIN_RELEVANT_COUNT)
        break

    # Fragile, makes assumption about the CSV being in the same path as the HTML file
    if csv_path:
      csv_link = os.path.basename(csv_path)
    else:
      csv_link = None

    template_name = '%s.tmpl' % format
    template_path = util.FindDataFile(os.path.join('templates', template_name))
    filtered_config = self.FilteredConfig()
    template_dir = os.path.dirname(template_path)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    rendered = template.render(
        best_ns = best_ns,
        system_primary = util.InternalNameServers()[0],
        timestamp = datetime.datetime.now(),
        lowest_latency=lowest_latency,
        version=self.config.version,
        compare_subtitle=compare_subtitle,
        compare_title=compare_title,
        compare_reference=compare_reference,
        config=filtered_config,
        mean_duration=mean_duration,
        ns_summary=ns_summary,
        mean_duration_url=mean_duration_url,
        min_duration_url=min_duration_url,
        distribution_url=distribution_url,
        distribution_url_200=distribution_url_200,
        recommended=recommended,
        csv_link=csv_link
    )
    if output_fp:
      output_fp.write(rendered)
      output_fp.close()
    else:
      return rendered

  def FilteredConfig(self):
    """Generate a watered down config listing for our report."""
    keys = [x for x in dir(self.config) if not x.startswith('_') and x != 'config' and x != 'site_url' ]
    config_items = []
    for key in keys:
      value = getattr(self.config, key)
      # > values are ConfigParser internals. None values are just noise.
      if isinstance(value, int) or isinstance(value, float) or isinstance(value, str):
        config_items.append((key, value))
    return sorted(config_items)

  def DigestedResults(self):
    """Return a tuple of nameserver and all associated durations."""
    duration_data = []
    for ns in self.results:
      durations = []
      for test_run_results in self.results[ns]:
        durations += [x[2] for x in test_run_results]
      duration_data.append((ns, durations))
    return duration_data
    
  def _GenerateNameServerSummary(self):
    nsdata = {}
    sorted_averages = sorted(self.ComputeAverages(), key=operator.itemgetter(1))
    placed_at = -1
    fastest = {}
    fastest_nonglobal = {}
    reference = {}

    # Fill in basic information for all nameservers, even those without scores.
    for ns in self.nameservers:

      # Append notes with associated URL's
      notes = []
      for note in ns.notes:
        url = None
        for keyword in FAQ_MAP:
          if keyword in note:
            url = FAQ_MAP[keyword]
        notes.append({'text': note, 'url': url})

      nsdata[ns] = {
        'ip': ns.ip,
        'name': ns.name,
        'hostname': ns.hostname,
        'sys_position': ns.system_position,
        'is_failure_prone': ns.is_failure_prone,
        'is_global': ns.is_global,
        'is_regional': ns.is_regional,
        'is_custom': ns.is_custom,
        'is_reference': False,
        'is_disabled': bool(ns.disabled),
        'check_average': ns.check_average,
        'error_count': ns.error_count,
        'timeout_count': ns.timeout_count,
        'notes': notes,
        'position': 999
      }

    # Fill the scores in.
    for (ns, avg, run_averages, fastest, slowest, failure_count, nx_count, total_count) in sorted_averages:
      placed_at += 1
      
      durations = []
      for test_run in self.results[ns]:
        durations.append([x[2] for x in self.results[ns][0]])

      nsdata[ns].update({
        'position': placed_at,
        'overall_average': util.CalculateListAverage(run_averages),
        'averages': run_averages,
        'min': fastest,
        'max': slowest,
        'nx_count': nx_count,
        'durations': durations,
        'index': self._GenerateIndexSummary(),
      })
      # Determine which nameserver to refer to for improvement scoring
      if not ns.disabled:
        if ns.system_position == 0:
          reference = ns
        elif not fastest_nonglobal and not ns.is_global:
          fastest_nonglobal = ns
      
    # If no reference was found, use the fastest non-global nameserver record.
    if not reference:
      if fastest_nonglobal:
        reference = fastest_nonglobal
      else:
        # The second ns. 
        reference = sorted_averages[1][0]

    # Update the improvement scores for each nameserver.
    for ns in nsdata:
      if nsdata[ns]['ip'] != nsdata[reference]['ip']:
        if 'overall_average' in nsdata[ns]:
          nsdata[ns]['diff'] = ((nsdata[reference]['overall_average'] / nsdata[ns]['overall_average']) - 1) * 100
      else:
        nsdata[ns]['is_reference'] = True
        
      print nsdata[ns]
    
    return sorted(nsdata.values(), key=operator.itemgetter('position'))

  def _GenerateIndexSummary(self):
    # Get the meat out of the index data.
    index = []
    if self.index:
      for ns in self.index:
        for host, req_type, duration, response, unused_x in self.index[ns]:
          answer_count, ttl = self._ResponseToCountTtlText(response)[0:2]
          index.append((host, req_type, duration, answer_count, ttl, nameserver.ResponseToAscii(response)))
    return index

  def _CreateSharingData(self):
    config = dict(self.FilteredConfig())
    config['platform'] = (platform.system(), platform.release())
    config['python'] = platform.python_version_tuple()
    nsdata_list = self._GenerateNameServerSummary()
    # Purge sensitive information
    for row in nsdata_list:
      row['ip'], row['hostname'], row['name'] = util.MaskPrivateHost(row['ip'], row['hostname'], row['name'])
      
      
    return {'config': config, 'nameservers': nsdata_list, 'geodata': self.geodata}
    
  def CreateJsonData(self):
    sharing_data = self._CreateSharingData()
    return simplejson.dumps(sharing_data)

  def _ResponseToCountTtlText(self, response):
    """For a given DNS response, parse the most important details out.

    Args:
      response: DNS response

    Returns:
      tuple of (answer_count, ttl, answer_text)
    """

    answer_text = ''
    answer_count = -1
    ttl = -1
    if response:
      if response.answer:
        answer_count = len(response.answer)
        ttl = response.answer[0].ttl
      answer_text = nameserver.ResponseToAscii(response)
    return (answer_count, ttl, answer_text)


  def SaveResultsToCsv(self, filename):
    """Write out a CSV file with detailed results on each request.

    Args:
      filename: full path on where to save results (string)

    Sample output:
    nameserver, test_number, test, type, duration, answer_count, ttl
    """
    self.msg("Opening %s for write" % filename, debug=True)
    csv_file = open(filename, 'w')
    output = csv.writer(csv_file)
    output.writerow(['IP', 'Name', 'Test_Num', 'Record',
                     'Record_Type', 'Duration', 'TTL', 'Answer_Count',
                     'Response'])
    for ns in self.results:
      self.msg("Saving detailed data for %s" % ns, debug=True)
      for (test_run, test_results) in enumerate(self.results[ns]):
        for (record, req_type, duration, response, error_msg) in test_results:
          (answer_count, ttl, answer_text) = self._ResponseToCountTtlText(response)
          output.writerow([ns.ip, ns.name, test_run, record, req_type, duration,
                           ttl, answer_count, answer_text, error_msg])
    csv_file.close()
    self.msg("%s saved." % filename, debug=True)
    

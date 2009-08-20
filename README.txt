An experiment in benchmarking DNS name services. This tool is designed to help
you as a user determine what name services are the best to use for an
individual machine.

Requirements:

  * Python 2.4 - 2.6. If you are using Mac OS X or UNIX, this is
    built-in. Otherwise, visit http://www.python.org/

Most people will simply want to run this software with no arguments:

  ./namebench.py

This will test the nameservers you have already configured this machine to use,
plus 3 popular global DNS services, and the best 4-6 additional name servers
that it can find for you. It will output some text-graphs and URL's for more
a more detailed performance analysis of each nameserver.


If you want to specify an additional set of name services, simply add the IP
to the command-line, or edit namebench.cfg:

  ./namebench.py 10.0.0.1 192.168.0.1


--[ options ]-------------------------------------------------------------------

Usage: namebench.py [options] <additional nameservers>

Options:
  -h, --help            show this help message and exit
  -r RUN_COUNT, --runs=RUN_COUNT
                        Number of test runs to perform on each nameserver.
  -c CONFIG, --config=CONFIG
                        Config file to use.
  -o OUTPUT_FILE, --output=OUTPUT_FILE
                        Filename to write query results to (CSV format).
  -j THREAD_COUNT, --threads=THREAD_COUNT
                        # of threads to use
  -y TIMEOUT, --timeout=TIMEOUT
                        # of seconds general requests timeout in.
  -Y HEALTH_TIMEOUT, --health_timeout=HEALTH_TIMEOUT
                        # of seconds health checks timeout in.
  -i INPUT_FILE, --input=INPUT_FILE
                        File containing a list of domain names to query.
  -t TEST_COUNT, --tests=TEST_COUNT
                        Number of queries per run.
  -s NUM_SERVERS, --num_servers=NUM_SERVERS
                        Number of nameservers to test

--[ sample output ]-------------------------------------------------------------

namebench 0.6 - 20 threads, 40 tests, 2 runs
------------------------------------------------------------------------------
- Checking health of 872 nameservers (20 threads)
  o N9UF-INFRA-3: NXDOMAIN Hijacking
  o N9UF-INFRA-4: NXDOMAIN Hijacking
  * Level 3 [4.2.2.1] is unhealthy: TestWwwGoogleComResponse <class 'dns.exception.Timeout'>
  * Level 3-2 [4.2.2.2] is unhealthy: TestGoogleComResponse <class 'dns.exception.Timeout'>
  o OpenDNS: NXDOMAIN Hijacking
  o OpenDNS-2: NXDOMAIN Hijacking
  o Louisiana DOE: www.google.com. may be hijacked, NXDOMAIN Hijacking
  o N9UF-INFRA: NXDOMAIN Hijacking
  o NTS-2: www.google.com. may be hijacked, NXDOMAIN Hijacking
- Saving health status of 17 best servers to cache
- Checking for slow replicas among 17 nameservers

Final list of nameservers to benchmark:
---------------------------------------
  193.121.171.135 [SYS-193.121.171.135], health tests took 81.383ms
  208.67.220.220 [OpenDNS], health tests took 284.045ms
  208.67.222.222 [OpenDNS-2], health tests took 390.756ms
  156.154.70.1 [UltraDNS], health tests took 669.783ms
  156.154.71.1 [UltraDNS-2], health tests took 705.896ms
  194.119.228.67 [Scarlet-1], health tests took 98.284ms
  217.194.96.10 [PINS], health tests took 104.837ms
  85.90.229.188 [Telecity-DNS], health tests took 112.477ms
  217.64.240.4 [MACTelecom], health tests took 116.161ms
  81.171.102.14 [EWEKA-2], health tests took 120.566ms
  213.138.110.132 [Planetsky], health tests took 122.058ms
  80.249.115.194 [ip69-ns2], health tests took 128.801ms
  212.30.96.123 [N9UF], health tests took 129.791ms

* Benchmarking 13 nameservers with 40 records each (1 of 2)..............
* Benchmarking 13 nameservers with 40 records each (2 of 2)..............

Overall Mean Request Duration (in milliseconds):
------------------------------------------------------------------------------
UltraDNS        ############ 63
Scarlet-1       ############# 68
OpenDNS         ################ 85
UltraDNS-2      ################## 92
OpenDNS-2       ################## 93
MACTelecom      ################### 97
ip69-ns2        ################### 101
N9UF            ##################### 108
Telecity-DNS    ##################### 108
Planetsky       ########################## 135
PINS            ########################## 136
EWEKA-2         ########################### 144
SYS-193.121.171 ####################################################### 288

Lowest latency for an individual query (in milliseconds):
------------------------------------------------------------------------------
Scarlet-1       ################## 9.64
SYS-193.121.171 #################### 11.02
MACTelecom      ####################### 12.19
ip69-ns2        ########################## 14.22
PINS            ########################### 14.52
Planetsky       ############################ 15.20
EWEKA-2         ############################# 15.96
Telecity-DNS    ############################## 15.99
UltraDNS        #################################### 19.55
N9UF            ###################################### 20.46
UltraDNS-2      ######################################### 22.16
OpenDNS         ######################################### 22.47
OpenDNS-2       ###################################################### 29.76

Detailed Mean Request Duration Chart URL
------------------------------------------------------------------------------
http://chart.apis.google.com/chart?chxt=y%2Cx&chd=s%3ANSTXSafhdrep0%2CGDJINHEFJFSL5&chxp=0&chxr=1%2C15.5%2C320&chxtc=1%2C-900&chco=4684ee%2C00248e&chbh=a&chs=900x320&cht=bhg&chxl=0%3A%7CSYS-193.121.171.135%7CEWEKA-2%7CPINS%7CPlanetsky%7CTelecity-DNS%7CN9UF%7Cip69-ns2%7CMACTelecom%7COpenDNS-2%7CUltraDNS-2%7COpenDNS%7CScarlet-1%7CUltraDNS%7C1%3A%7C0%7C40%7C80%7C120%7C160%7C200%7C240%7C280%7C320&chdl=Run%201%7CRun%202

Detailed Request Duration Distribution Chart URL
------------------------------------------------------------------------------
http://chart.apis.google.com/chart?cht=lxy&chs=700x428&chxt=x,y&chg=10,20&chxr=0,0,220|1,0,100&chd=t:0,9,9,10,10,10,11,11,13,15,18,50,63,72,75,130|0,1,11,30,39,48,53,64,69,73,76,80,84,88,91,95|0,4,5,5,5,6,7,8,8,10,11,13,14,17,48,51,71,91,126|0,1,8,15,33,39,43,51,55,59,63,66,70,74,78,81,85,89,93|0,10,10,11,11,12,12,12,15,16,16,17,51,66,78,85,129|0,1,9,33,38,43,49,53,56,60,66,70,74,78,81,85,89|0,7,8,8,9,9,11,11,13,14,16,21,27,46,54,67,78,97,121|0,1,6,18,25,31,38,41,46,51,56,60,64,68,71,75,79,83,86|0,6,6,6,7,7,7,8,9,9,12,13,14,15,22,44,51,67,74,95,119|0,1,5,11,21,25,31,35,40,44,48,53,56,60,64,68,71,75,79,83,86|0,7,7,8,8,8,9,10,10,11,16,24,48,56,71,83,86,89,121|0,1,8,18,24,29,34,38,41,45,49,53,56,60,64,69,73,76,80|0,6,7,7,7,8,8,8,10,11,12,13,15,18,22,47,49,56,63,78,98,124|0,1,8,14,21,25,31,35,39,43,48,51,55,59,63,66,70,74,78,81,85,89|0,7,8,8,9,9,10,11,12,13,18,27,49,56,61,68,78,87,96,127|0,1,11,19,23,28,31,35,39,45,49,53,56,60,64,68,71,75,79,83|0,10,11,11,12,14,14,14,15,15,15,19,22,26,33,44,52,78,86,136|0,1,5,10,14,18,24,44,53,59,63,66,70,74,78,81,85,89,93,96|0,5,9,14,17,44,54,57,60,67,70,72,89,119|0,1,5,9,13,16,20,24,28,33,36,40,44,48|0,14,14,14,14,15,15,16,17,17,18,19,19,20,21,23,25,28,33,58,85,207|0,1,5,13,24,29,36,40,45,49,53,56,60,65,69,73,76,80,85,89,93,96|0,9,10,10,11,11,11,12,13,14,16,23,48,72,81,89,133|0,1,16,26,30,39,51,56,60,64,68,71,75,79,83,86,90|0,7,7,8,8,8,10,11,12,13,16,19,23,30,50,58,80,93,114|0,1,10,20,25,30,34,40,44,49,53,56,60,64,68,71,75,79,83&chco=ff9900,3dbecc,ff3912,303030,4684ee,fae30a,cc3ebd,76cc3e,bdcc3e,ababab,e5a59e,9900ff,76dbf4&chdl=UltraDNS|Scarlet-1|UltraDNS-2|Telecity-DNS|MACTelecom|Planetsky|ip69-ns2|EWEKA-2|OpenDNS|SYS-193.121.171.135|OpenDNS-2|N9UF|PINS

Recommended Configuration (fastest + nearest):
----------------------------------------------
nameserver 156.154.70.1    # UltraDNS
nameserver 194.119.228.67  # Scarlet-1
nameserver 193.121.171.135 # SYS-193.121.171.135



--[ FAQ ]-----------------------------------------------------------------------
1) What does 'NXDOMAIN Hijacking' mean?

  This means that the specific DNS server returns a false entry when a
  non-existent record is requested. This entry likely points to a website
  serving a 'Host not found' page with banner ads.

2) What does 'www.google.com. may be hijacked' mean?

  This means that when a user requests 'www.google.com', they are being
  silently redirected to another server. The page may look like it's run by
  Google, but it is instead being proxied through another server. For details,
  try using the host command. In this case, this particular IP server is
  redirecting all traffic to http://google.navigation.opendns.com/

  % host www.google.com. 208.67.220.220                                                            [+0109] tstromberg@coelacanth:~/namebench
  Using domain server:
  Name: 208.67.220.220
  Address: 208.67.220.220#53
  Aliases:

  www.google.com is an alias for google.navigation.opendns.com.
  google.navigation.opendns.com has address 208.67.217.230
  google.navigation.opendns.com has address 208.67.217.231


3) What does 'google.com. may be hijacked' mean?

  The same as above, but it is a rarer condition as it breaks http://google.com/

4) What does 'thread.error: can't start new thread' mean?

  It means you are using too many threads. Try restarting namebench.py with -j8

5) What does 'unhealthy: TestWwwGoogleComResponse <class 'dns.exception.Timeout'>' mean?

  It means the specified nameserver was too slow to answer you. If all of your
  nameservers are timing out, try restarting namebench.py with -Y 4


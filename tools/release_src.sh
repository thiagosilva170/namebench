#!/bin/sh
# Create a tarball from the subversion repository.
#
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

tmp=$$
cd /tmp
svn checkout http://namebench.googlecode.com/svn/trunk/ namebench-$$
version=`grep '^VERSION' namebench-$$/libnamebench/version.py | cut -d\' -f2`
mv namebench-$$ namebench-$version
cd namebench-$version
./namebench.py -t2 -r1 -j40 -o /tmp/$$.csv 208.67.220.220
svn log > ChangeLog.txt
find . -name "*.pyc" -delete
find . -name ".svn" -exec rm -Rf {} \; 2>/dev/null
cd ..
GZIP=9 tar -zcvf namebench-${version}.tgz namebench-${version}/
rm -Rf namebench-${version}

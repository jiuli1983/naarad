# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import datetime
import gc
import logging
import os
import re
import numpy
from naarad.metrics.metric import Metric
import naarad.utils

logger = logging.getLogger('naarad.metrics.ProcMeminfoMetric')

class ProcMeminfoMetric(Metric):
  """
  logs of /proc/vmstat
  The raw log file is assumed to have a timestamp prefix of all lines. E.g. in the format of "2013-01-02 03:55:22.13456 compact_fail 36"
  The log lines can be generated by   'cat /proc/vmstat | sed "s/^/$(date +%Y-%m-%d\ %H:%M:%S.%05N)\t/" '  
  """
  
  unit = 'KBs'  # The unit of the metric. For /proc/meminfo, they are all in KBs
  sub_metrics = None
  
  def __init__ (self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end)
    
    # in particular, Section can specify a subset of all rows (default has 43 rows):  "sub_metrics=nr_free_pages nr_inactive_anon"
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())   
      
    self.metric_description = {
      'MemTotal': 'Total memory in KB',
      'MemFree': 'Total free memory in KB',
      'Buffers': 'Size of buffers in KB',
      'Cached': 'Size of page cache in KB',
     }    

      
  def parse(self):
    """
    Parse the vmstat file
    :return: status of the metric parse
    """
    logger.info('Processing : %s',self.infile)
    file_status = naarad.utils.is_valid_file(self.infile)
    if not file_status:
      return False
      
    status = True

    with open(self.infile) as fh:
      data = {}  # stores the data of each column
      for line in fh:
        words = line.split()  
        # [0] is day; [1] is seconds; [2] is field name:; [3] is value  [4] is unit
        col = words[2].strip(':')
        
        # only process sub_metrics specified in config. 
        if self.sub_metrics and col not in self.sub_metrics:
          continue
          
        ts = words[0] + " " + words[1]
      
        if col in self.csv_column_map: 
          out_csv = self.csv_column_map[col] 
        else:
          out_csv = Metric.get_csv(self,col)     
          self.csv_column_map[col] = out_csv   
          data[out_csv] = []        
      
        # provide default description (Metric.graph() requires a description)
        if not col in self.metric_description:
          self.metric_description[col] = 'No description'
      
        data[out_csv].append(ts + "," + words[3])
    
    #post processing, putting data in csv files;   
    for csv in data.keys():      
      self.csv_files.append(csv)
      with open(csv, 'w') as fh:
        fh.write('\n'.join(data[csv]))

    gc.collect()
    return status

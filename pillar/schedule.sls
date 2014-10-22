schedule:
#  monitoring:
#    function: monitor.
  system-cpu-percent:
    function: ps.cpu_percent
    seconds: 10
    maxrunning: 2
    returner: splunk

  system-disk:
    function: ps.disk_usage
    {% if grains['kernel'] == 'Linux'%}
    kwargs:
      path: '/'
    {% elif grains['kernel'] == 'Windows' %}
    kwargs:
      path: 'C:\'
    {% endif %}
    seconds: 10
    maxrunning: 1
    returner: splunk

#
#
#ps.cached_physical_memory
#ps.cpu_times
#ps.disk_io_counters
#ps.disk_usage
#ps.network_io_counters
#ps.physical_memory_buffers
#ps.physical_memory_usage
#ps.virtual_memory_usage
#

#  perf:
#    function: splunk.perf
#    seconds: 10
#    maxrunning: 5
#    returner: splunk
#    args:
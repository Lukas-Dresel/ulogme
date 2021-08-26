#!/usr/bin/env python
import sys
import datetime
import time

def rewindTime(t):
  """
  very simply utility function that takes unix time (as int)
  and returns unix time at 7am of the day that the corresponding ulogme
  event belongs to. ulogme day breaks occur at 7am, so e.g. 3am late
  night session will count towards previous day activity
  """
  d = datetime.datetime.fromtimestamp(t)
  # reset < hour settings
  d = d.replace(microsecond=0, second=0, minute=0)
  if d.hour >= 7:
    # it's between 7am-11:59pm
    d = d.replace(hour=7) # rewind time to 7am
  else:
    # it's between 12am-7am, so this event still belongs to previous day
    d = d.replace(hour=7) # rewind time to 7am
    d -= datetime.timedelta(days=1) # subtract a day

  curtime = d.timestamp()
  return curtime

if __name__ == '__main__':
  # the output is int since by definition no microseconds are left, but we take full timestamps as floats if wanted
  if len(sys.argv) <= 1:
    # use right now
    print(int(rewindTime(float(time.time()))))
  else:
    print(int(rewindTime(float(sys.argv[1]))))

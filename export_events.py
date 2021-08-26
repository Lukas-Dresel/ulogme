import time
import datetime
import json
import os
import os.path
import sys
import glob


def loadEvents(fname):
  """
  Reads a file that consists of first column of unix timestamps
  followed by arbitrary string, one per line. Outputs as dictionary.
  Also keeps track of min and max time seen in global mint,maxt
  """
  events = []

  try:
    with open(fname, 'rb') as f:
        ws = f.read().decode('utf-8').splitlines()
    events = []
    for w in ws:
      ix = w.find(' ') # find first space, that's where stamp ends
      stamp = int(w[:ix])
      str = w[ix+1:]
      events.append({'t':stamp, 's':str})
  except Exception as e:
    print('%s probably does not exist, setting empty events list.' % (fname, ))
    print('error was:')
    print(e)
    events = []
  return events

def mtime(f):
  """
  return time file was last modified, or 0 if it doesnt exist
  """
  if os.path.isfile(f):
    return int(os.path.getmtime(f))
  else:
    return 0

def updateEvents():
  """
  goes down the list of .txt log files and writes all .json
  files that can be used by the frontend
  """
  L = []
  L.extend(glob.glob("logs/keyfreq_*.txt"))
  L.extend(glob.glob("logs/mousefreq_*.txt"))
  L.extend(glob.glob("logs/window_*.txt"))
  L.extend(glob.glob("logs/notes_*.txt"))

  # extract all times. all log files of form {type}_{stamp}.txt
  ts = [int(x[x.find('_')+1:x.find('.txt')]) for x in L]
  ts = list(set(ts))
  ts.sort()

  mint = min(ts)
  maxt = max(ts)

  # march from beginning to end, group events for each day and write json
  ROOT = ''
  RENDER_ROOT = os.path.join(ROOT, 'render')
  os.makedirs(RENDER_ROOT, exist_ok=True) # make sure output directory exists
  t = mint
  out_list = []
  for t in ts:
    t0 = t
    t1 = t0 + 60*60*24 # 24 hrs later
    fout = 'events_%d.json' % (t0, )
    out_list.append({'t0':t0, 't1':t1, 'fname': fout})

    fwrite = os.path.join(RENDER_ROOT, fout)
    e1f = 'logs/window_%d.txt' % (t0, )
    e2f = 'logs/keyfreq_%d.txt' % (t0, )
    e3f = 'logs/mousefreq_%d.txt' % (t0, )
    e4f = 'logs/notes_%d.txt' % (t0, )
    e5f = 'logs/blog_%d.txt' % (t0, )

    dowrite = False

    # output file already exists?
    # if the log files have not changed there is no need to regen
    if os.path.isfile(fwrite):
      tmod = mtime(fwrite)
      if any(mtime(fname) > tmod for fname in (e1f, e2f, e3f, e4f, e5f)):
        dowrite = True # better update!
        print(f'a log file has changed, so will update {fwrite}')
    else:
      # output file doesnt exist, so write.
      dowrite = True

    if dowrite:
      # okay lets do work
      e1 = loadEvents(e1f)
      e2 = loadEvents(e2f)
      e3 = loadEvents(e3f)
      e4 = loadEvents(e4f)
      for k in e2: k['s'] = int(k['s']) # int convert

      e5 = ''
      if os.path.isfile(e5f):
        e5 = open(e5f, 'r').read()

      eout = {'window_events': e1, 'keyfreq_events': e2, 'mousefreq_events': e3, 'notes_events': e4, 'blog': e5}
      with open(fwrite, 'w') as f:
          json.dump(eout, f)
      print('wrote ' + fwrite)

  fwrite = os.path.join(RENDER_ROOT, 'export_list.json')
  with open(fwrite, 'w') as f:
      json.dump(out_list, f)
  print('wrote ' + fwrite)

# invoked as script
if __name__ == '__main__':
  updateEvents()

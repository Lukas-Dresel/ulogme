#!/usr/bin/env python3

# continually logs the key presses and their frequency over 9 second window. Logs are written 
# in logs/keyfreqX.txt every 9 seconds, where X is unix timestamp of 7am of the
# recording day.

import queue
from threading import Thread
from pynput import mouse
import pathlib
from os.path import dirname, join, abspath
import os
import time
import random
import subprocess
import sys

class MyException(Exception): pass

cwd = pathlib.Path(os.getcwd()).absolute().resolve()
assert (cwd / "rewind7am.py").is_file(), "All logging scripts have to be run in the main directory"

logs_dir = cwd / "logs"

key_events = queue.Queue()

INTERVAL = 9

def rewind(t):
  return int(subprocess.check_output([str(cwd / "rewind7am.py"), str(t)]))

def write_events(interval_start, events):
  t = rewind(interval_start)
  assert type(t) is int
  freq_file = logs_dir / f"mousefreq_{t}.txt"
  codes_file = logs_dir / f"mouse_events_{t}.txt"
  num_events = len(events)

  print(f"writing out {num_events} mouse events @ {interval_start=} to {freq_file=}, {codes_file=}")
  with freq_file.open("a") as f:
    f.write(f'{int(interval_start)} {num_events}\n')
  
  with codes_file.open('a') as f:
    for ts, ev in events:
      f.write(f'{int(ts)} {ev}\n')

def take_while(ls, pred):
  assert type(ls) is list
  res = []
  for i, x in enumerate(ls):
    if pred(x):
      res.append(x)
    else:
      return res, ls[i:]
  return [], ls


cur_end = int(time.time()) + INTERVAL
pending = []
with mouse.Events() as events:
  while True:
    max_wait = max(0, cur_end + 1 - time.time()) # wait for an extra second to give events time to come in
    e = events.get(max_wait)
    ts = time.time()
    if e is not None:
      pending.append((ts, e))

    while ts > cur_end:
      interval_events, pending = take_while(pending, lambda x: x[0] < cur_end)  # take out ones in this interval
      write_events(cur_end - INTERVAL, interval_events)  # write out
      cur_end += INTERVAL  # advance interval

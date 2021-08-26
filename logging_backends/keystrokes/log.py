#!/usr/bin/env python3

# continually logs the key presses and their frequency over 9 second window. Logs are written 
# in logs/keyfreqX.txt every 9 seconds, where X is unix timestamp of 7am of the
# recording day.

import queue
from threading import Thread
from pynput import keyboard
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

def write_key_events(interval_start, codes_since):
  
  t = rewind(interval_start)
  assert type(t) is int
  freq_file = logs_dir / f"keyfreq_{t}.txt"
  codes_file = logs_dir / f"keycodes_{t}.txt"
  released = 0
  for ts, key, pressed in codes_since:
    released += 1 if not pressed else 0

  print(f"writing out {released=}, {len(codes_since)} keys @ {interval_start=} to {freq_file=}, {codes_file=}")
  with freq_file.open("a") as f:
    f.write(f'{int(interval_start)} {released}\n')
  
  with codes_file.open('a') as f:
    for ts, key, pressed in codes_since:
      pressed = 'down' if pressed else 'up'
      f.write(f'{int(ts)} {key} {pressed}\n')


class WriterThread(Thread):
  def run(self):

    # the start of the next interval to be written out (mostly the current one)
    current_start = int(time.time()) # the interval starts are at second boundaries

    wait_time = INTERVAL + 1 # wait for a second longer to give keys time to arrive
    # when we start processing the inputs of that interval (1 second after to give the keys time to trickle in and avoid weirdness)
    wait_for = current_start + wait_time

    # ^^^^^ these should always be INTERVAL + 1 apart
    events = []
    while True:
      # process all key events we have laying around
      try:
        events.append(key_events.get(block=False))
        continue # try getting more keys, don't fall into normal logic now
      except queue.Empty:
        # okay, we have time to process things
        pass

      assert wait_for - current_start == wait_time, f"Desync, {current_start=} and {wait_for=} should always be {wait_time=} apart!"
      #print(f'[{current_start},{wait_for}] vs {time.time()}', file=sys.stderr)
      if time.time() > wait_for: # if we have an interval ready to process (no loop, might need more keys to arrive)
        to_write = []
        while events and events[0][0] < current_start + INTERVAL: # event with timestamp before interval end available
          to_write.append(events.pop(0))
        write_key_events(current_start, to_write)
        current_start += INTERVAL
        wait_for += INTERVAL
        to_sleep = max(0, wait_for - time.time())
        print(f"Finished interval, sleeping for {to_sleep=} seconds!")
        time.sleep(to_sleep) # sleep until the end of the interval hopefully
        # raise NotImplementedError

def on_press(key):
  ev = (time.time(), key, True)
  # print(f"keydown {ev=}")
  key_events.put(ev)

def on_release(key):
  ev = (time.time(), key, False)
  # print(f"keyup {ev=}")
  key_events.put(ev)

writer = WriterThread()
writer.start()

print("Listening for keyboard events!")
# Collect events until released
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
        writer.join()
    except MyException as e:
        print('{0} was pressed'.format(e.args[0]))


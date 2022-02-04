#!/usr/bin/python3

'''
Copyright 2021 - Albert Montijn (montijnalbert@gmail.com)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   ---------------------------------------------------------------------------
   Programming is the result of learning from others and making errors.
   A good programmer often follows the tips and tricks of better programmers.
   The solution of a problem seldom leads to new or original code.
   So any resemblance to already existing code is purely coincidental
'''

import threading
import time
import subprocess
import logging
log = logging.getLogger(__name__)

class WatchdogThread(threading.Thread):
    '''
    The class WatchdogThread implements a watchdog mechanism.
    After creating an instance of this class a thread is created that will
    run for <sleeptime> seconds. If the sleeptime is reached, the method 
    <action_stop> will be executed and the thread ends.
    if the method <restart> is called the running thread is ended and a new
    thread is started. This prevents the call of <action_stop>
    if <restart> is called when there is no thread running, <action_start> is
    called to inform the caller that the program resumed its normal course.
    Example:
    def action_start():
        print "program resumed"
    def action_stop():
        print "program stopped"
    watchdog_period = 10 # after 10 seconds the watchdog calls action_stop()
    
    # create and start the first watchdog thread
    wd = WatchdogThread.restart(action_start,action_stop,watchdog_period)

    while True:
        do_something_time_consuming_that_may_take_to_long()
        # restart the watchdog for a new <watchdog_period>
        wd = WatchdogThread.restart(action_start,action_stop,watchdog_period,wd)
        
    '''
    #thread_count = 0

    def __init__(self, action_start, action_stop, sleeptime=1800):
        # constructor, setting initial variables
        log.debug(f"New Watchdog with sleeptime={sleeptime}")
        self._stopevent = threading.Event(  )
        self._action_start = action_start
        self._action_stop = action_stop
        self._sleepperiod = 1
        self.sleep_time = sleeptime # default = 1800 = 30 minutes
        #WatchdogThread.thread_count += 1
        #name = f"watchdog_{WatchdogThread.thread_count}"

        threading.Thread.__init__(self) #, name=name)

    def run(self):
        """  main control loop """

        log.debug(f"Watchdog.run {threading.get_ident()}: sleeptime={self.sleep_time},nr of threads={threading.active_count()}")
        self._start_time = time.time()
        elapsed_time = 0
        while not self._stopevent.isSet(  ):
            elapsed_time += self._sleepperiod
            self._stopevent.wait(self._sleepperiod)
            if elapsed_time >= self.sleep_time:
                log.debug(f"Watchdog.run {threading.get_ident()}: Watchdog elapsed_time = {elapsed_time} >= {self.sleep_time} = self.sleep_time")
                self._action_stop(elapsed_time)
                return

    def join(self, timeout=None):
        # Stop the thread.
        seconds_run = time.time() - self._start_time
        log.debug(f"Watchdog.join ({seconds_run} seconds run) {threading.get_ident()}: with timeout={timeout},nr of threads={threading.active_count()}")
        self._stopevent.set(  )
        threading.Thread.join(self, timeout)

    def restart(action_start, action_stop, num_sec, old_thread=None):
        log.debug(f"in Watchdog.restart with old_thread={old_thread},nr of threads={threading.active_count()}")
        if old_thread is not None:
            if old_thread.is_alive():
                old_thread.join()
            else:
                old_thread._action_start()

        new_thread = WatchdogThread(action_start, action_stop, num_sec)
        new_thread.start()
        return new_thread

# end of file


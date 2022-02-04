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

import rrdtool
import json
import datetime
import os
import logging

log = logging.getLogger(__name__)

class Rrd:
    def rrd_create_file(self):
        raise NotImplementedError
    def check_input(self, input_data):
        raise NotImplementedError
    def get_datetime_for_update(self, input_data):
        raise NotImplementedError
    def input_to_data(input_data):
        raise NotImplementedError
    def lastdata_to_json(data):
        raise NotImplementedError

    def rrd_filename(self, my_datetime):
        return f'{self.rrdfiledir}{my_datetime.strftime("%Y%m%d")}.rrd'

    def get_file(self, my_datetime,create=True):
        filename = self.rrd_filename(my_datetime)
        if not os.path.exists(filename):
            if create:
                self.rrd_create_file(my_datetime)
            else:
                filename = None
        
        return filename

    def update(self, input_data):
        if self.check_input(input_data):
            data_datetime = self.get_datetime_for_update(input_data)
            filename = self.get_file(data_datetime,create=True)
            data = self.input_to_data(input_data)
            res = rrdtool.updatev(filename,"-t",self.template,data)
            if res is None or res['return_value'] != 0:
                log.error("Error during update file:[{filename}], data:[{data}]")

            if log.isEnabledFor(logging.DEBUG):
                log.debug("Res="+str(res))
                for key,value in res.items():
                    log.debug(f"K:{key}={value}")
            log.info(f'rrdtool.update({filename},{self.template},{data}')
        else:
            log.info(f"check_input returned False")
            log.info(f"Input was [{str(input_data)}")

    def get_lastdata(self):
        filename = self.get_file(datetime.datetime.now(),create=False)
        log.debug(f"Opening file {filename}")

        if os.path.exists(filename):
            data = rrdtool.lastupdate(filename)
            res = self.lastdata_to_json(data)
        else:
            res = '{}'

        return json.loads(res)


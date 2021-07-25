#!/usr/bin/env python

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
import logging
log = logging.getLogger(__name__)
from intentconfig import Text, get_text
import traceback

class SentencesError(Exception):
    """Exception raised for errors in sentences.ini.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    def handle(self):
        log.warning("================ SENTENCES ERROR ================")
        log.warning(self.message)
        log.debug(f"{traceback.format_exc()}")
        speech = get_text(Text.SENTENCES_ERROR)
        return speech

def error_missing_parameter(param="", intent="unknown"):
    raise SentencesError(f"Missing parameter {param} in intent {intent}")



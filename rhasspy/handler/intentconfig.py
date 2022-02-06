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

import os
import re
import logging
log = logging.getLogger(__name__)

from enum import Enum
Text = Enum('Text',
            'DecimalPoint Please_Wait AND MINUTE MINUTES SECONDS WEEKDAY MONTH' +
            ' ERROR Intent_Error DuckDuckGo_ERROR SENTENCES_ERROR' +
            ' Timer_Response Timer_ERROR GetTime_Response' +
            ' GetDate_Response GetAge_Response GetBirthDate_Response' +
            ' GetBirthDay_Single GetBirthDay_Multiple GetBirthDay_Month' +
            ' GetBirthDay_MonthList GetNoBirthDay')
DomoText = Enum('DomoText',
            'Error GetWind_Response GetWind_Direction GetWind_Beaufort' +
            ' Old_data AskUpdateSlotsConfirmation' +
            ' SayUpdateSlotsConfirmation SayNoUpdateSlotsConfirmation')
KodiText = Enum('KodiText',
            'Music AskPlayConfirmation SayNoMusicFound SayPlayConfirmation' +
            ' SayNoPlayConfirmation WhatsPlaying_Response WhatsPlaying_Error' +
            ' AskUpdateSlotsConfirmation' +
            ' SayUpdateSlotsConfirmation SayNoUpdateSlotsConfirmation')

# ------------------------------------------------------------
#     Configurable data
# ------------------------------------------------------------
 
config = {
    "urls" : 
        { "Rhasspy" : "http://localhost:12101"
        , "DuckDuckGo" : "https://api.duckduckgo.com"
        , "Domo" : "http://localhost:8080"
        , "Kodi" : "http://localhost:8080"
        , "SmartCity" : "https://api.smartcitizen.me"
        , "KNMI" : "https://weerlive.nl/api/json-data-10min.php"
        }
    }

text = {
"en" : {
    Text.Please_Wait: "please wait a moment",
    Text.DecimalPoint: "point",
    Text.AND: "and",
    Text.MINUTE: "minute",
    Text.MINUTES: "minutes",
    Text.SECONDS: "seconds",
    Text.WEEKDAY: [ "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday" ],
    Text.MONTH: [ "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december" ],
    Text.ERROR: "something went wrong.  Please check the error in the logfile",
    Text.SENTENCES_ERROR: "something went wrong.  Please check the logfile for SENTENCES ERROR",
    Text.Intent_Error: "i cannot find intent {INTENT}",
    Text.DuckDuckGo_ERROR: "no information found for {SEARCH}",
    Text.Timer_Response: "i set a timer for {MINUTES} {AND} {SECONDS}",
    Text.Timer_ERROR: "i could not set a timer for less than 10 seconds",
    Text.GetTime_Response: "the time is  {HOURS} hours and {MINUTES} minutes",
    Text.GetDate_Response: "today is  {WEEKDAY} {MONTH} {DAY} {YEAR}",
    Text.GetAge_Response: ".birthday. is {YEARS} old",
    Text.GetBirthDate_Response: "{NAME} is born on {WEEKDAY} {MONTH} {DAY} {YEAR}",
    Text.GetBirthDay_Single: "Today is {NAME} s birthday",
    Text.GetBirthDay_Multiple: "Today is the birthay of: ",
    Text.GetBirthDay_Month: "birthdays are coming for: ",
    Text.GetBirthDay_MonthList : " {NAME} on {DATE} ",
    Text.GetNoBirthDay: "there are no birthdays in the coming month",

    DomoText.Error : "no answer received from domoticz",
    DomoText.Old_data: "The data is old. No recent information",
    DomoText.GetWind_Response : \
        "the wind is blowing {SPEED} meter per second from the {DIRECTION}. Wind strength is {BEAUFORT} beaufort. {BEAUFORT_TEXT}",
    DomoText.GetWind_Direction : {
            "N": "north",
            "NNE": "north north east",
            "NE": "north east",
            "ENE": "east north east",
            "E": "east",
            "ESE": "east south east",
            "SE": "south east",
            "SSE": "south south east",
            "S": "south",
            "SSW": "south south west",
            "SW": "south west",
            "WSW": "west south west",
            "W": "west",
            "WNW": "west north west",
            "NW": "north west",
            "NNW": "north north west"
        },
    DomoText.GetWind_Beaufort : (
        (0,0.5,"Calm","Smoke rises vertically."),
        (1,1.5,"Light air","Direction shown by smoke drift but not by wind vanes."),
        (2,3.3,"Light breeze","Wind felt on face; leaves rustle; wind vane moved by wind."),
        (3,5.5,"Gentle breeze","Leaves and small twigs in constant motion; light flags extended."),
        (4,7.9,"Moderate breeze","Raises dust and loose paper; small branches moved."),
        (5,10.7,"Fresh breeze","Small trees in leaf begin to sway; crested wavelets form on inland waters."),
        (6,13.8,"Strong breeze","Large branches in motion; whistling heard in telegraph wires; umbrellas used with difficulty."),
        (7,17.1,"High wind","Whole trees in motion; inconvenience felt when walking against the wind."),
        (8,20.7,"Gale","Twigs break off trees; generally impedes progress."),
        (9,24.4,"Strong gale","Slight structural damage (chimney pots and slates removed)."),
        (10,28.4,"Storm","Seldom experienced inland; trees uprooted; considerable structural damage."),
        (11,32.6,"Violent storm","Very rarely experienced; accompanied by widespread damage."),
        (12,999,"Hurricane force","Devastation.")
        ),
    DomoText.AskUpdateSlotsConfirmation: "do you want me to update the domotics devices ?",
    DomoText.SayUpdateSlotsConfirmation: "the update of the domotics devices is done.",
    DomoText.SayNoUpdateSlotsConfirmation: "i will leave the domotics devices as it is",

    KodiText.Music: "music",
    KodiText.AskPlayConfirmation: "do you want me to play {TITLE} of {ARTIST} ?",
    KodiText.SayNoMusicFound: "i cannot find music of {ARTIST}",
    KodiText.SayPlayConfirmation: "i am going to play {TITLE} van {ARTIST}",
    KodiText.SayNoPlayConfirmation: "okay no music",
    KodiText.WhatsPlaying_Response : "this is track {TITLE}, of the album, {ALBUM}, of, {ARTIST}",
    KodiText.WhatsPlaying_Error: "i am sorry, but i do not know",
    KodiText.AskUpdateSlotsConfirmation: "do you want me to update the kodi library ?",
    KodiText.SayUpdateSlotsConfirmation: "the update of the kodi library is done.",
    KodiText.SayNoUpdateSlotsConfirmation: "i will leave kodi as it is"
    },

"nl" : {
    Text.Please_Wait: "een ogenblikje",
    Text.DecimalPoint: "komma",
    Text.AND: "en",
    Text.MINUTE: "minuut",
    Text.MINUTES: "minuten",
    Text.SECONDS: "seconden",
    Text.WEEKDAY: [ "maandag", "dinsdag", "woensdag",
        "donderdag", "vrijdag", "zaterdag", "zondag" ],
    Text.MONTH: [ "januari", "februari", "maart", "april", "mei", "juni",
        "juli", "augustus", "september", "october", "november", "december" ],
    Text.ERROR: "Er is iets fout gegaan. zoek in het log bestand naar error",
    Text.SENTENCES_ERROR: "Er is iets fout gegaan. zoek in het log bestand naar SENTENCES ERROR",
    Text.Intent_Error: "Ik kan de intent {INTENT} niet vinden. Controleer sentences.ini",
    Text.DuckDuckGo_ERROR: "Geen informatie gevonden voor {SEARCH}",
    Text.Timer_Response: "ik heb een taimer gezet op {MINUTES} {AND} {SECONDS}",
    Text.Timer_ERROR: "ik kan geen taimer zetten voor minder dan 10 seconden",
    Text.GetTime_Response: "Het is nu  {HOURS}  uur en {MINUTES} minuten",
    Text.GetDate_Response: "het is vandaag {WEEKDAY} {DAY} {MONTH} {YEAR}",
    Text.GetAge_Response: ".birthday. is {YEARS}",
    Text.GetBirthDate_Response: "{NAME} is geboren op {WEEKDAY} {DAY} {MONTH} {YEAR}",
    Text.GetBirthDay_Single: "Vandaag is de verjaardag van: {NAME}",
    Text.GetBirthDay_Multiple: "Vandaag is de verjaardag van: ",
    Text.GetBirthDay_Month: "komende verjaardagen zijn:  ",
    Text.GetBirthDay_MonthList : " {NAME} op {DATE} ",
    Text.GetNoBirthDay: "de rest van de maand en de volgende maand zijn er geen verjaardagen",

    DomoText.Error : "Geen of fout antwoord van domoticz ontvangen",
    DomoText.Old_data: "De informatie is verouderd. Ik kan geen antwoord geven",
    DomoText.GetWind_Response : "Het waait {SPEED} meter per seconde uit {DIRECTION}elijke richting. Het waait {BEAUFORT} bo for. {BEAUFORT_TEXT}",
    DomoText.GetWind_Direction : {
            "N": "noord",
            "NNE": "noord noord oost",
            "NE": "noord oost",
            "ENE": "oost noord oost",
            "E": "oost",
            "ESE": "oost zuid oost",
            "SE": "zuid oost",
            "SSE": "zuid zuid oost",
            "S": "zuid",
            "SSW": "zuid zuid west",
            "SW": "zuid west",
            "WSW": "west zuid west",
            "W": "west",
            "WNW": "west noord west",
            "NW": "noord west",
            "NNW": "noord noord west"
        },
    DomoText.GetWind_Beaufort :(
            (0,0.2,"windstilte","rook stijgt recht of bijna recht omhoog"),
            (1,1.5,"zwakke wind","windrichting goed af te leiden uit rookpluimen"),
            (2,3.3,"zwakke wind","wind merkbaar in gezicht"),
            (3,5.4,"matige wind","stof waait op"),
            (4,7.9,"matige wind","haar in de war, kleding flappert"),
            (5,10.7,"vrij krachtige wind","opwaaiend stof hinderlijk voor de ogen, gekuifde golven op meren en kanalen en vuilcontainers waaien om"),
            (6,13.8,"krachtige wind","paraplu's met moeite vast te houden"),
            (7,17.1,"harde wind","lastig tegen de wind in te lopen of fietsen"),
            (8,20.7,"stormachtige wind","voortbewegen zeer moeilijk"),
            (9,24.4,"storm","schoorsteenkappen en dakpannen waaien weg, kinderen waaien om"),
            (10,28.4,"zware storm","grote schade aan gebouwen, volwassenen waaien om"),
            (11,32.6,"zeer zware storm","enorme schade aan bossen"),
            (12,999,"orkaan","verwoestingen")
        ),
    DomoText.AskUpdateSlotsConfirmation: "weet je zeker dat ik de domotics dievaaises moet vurversen ?",
    DomoText.SayUpdateSlotsConfirmation: "ik ben klaar met het vurversen van de domotics dievaaises gegevens.",
    DomoText.SayNoUpdateSlotsConfirmation: "ik zal de domotics dievaaises niet vurversen",

    KodiText.Music: "muziek",
    KodiText.AskPlayConfirmation: "wil je dat ik {TITLE} van {ARTIST} ga afspelen ?",
    KodiText.SayNoMusicFound: "ik kan geen muziek van {ARTIST} vinden",
    KodiText.SayPlayConfirmation: "ik ga {TITLE} van {ARTIST} afspelen",
    KodiText.SayNoPlayConfirmation: "okee, dan niet",
    KodiText.WhatsPlaying_Response : "Dit is het nummer, {TITLE},van het album, {ALBUM}, van, {ARTIST}",
    KodiText.WhatsPlaying_Error: "Ik weet het niet, sorry",
    KodiText.AskUpdateSlotsConfirmation: "weet je zeker dat ik de kodi gegevens moet vurversen ?",
    KodiText.SayUpdateSlotsConfirmation: "ik ben klaar met het vurversen van de kodi gegevens.",
    KodiText.SayNoUpdateSlotsConfirmation: "ik zal kodi niet vurversen"
    }
}

domo_rhasspy_type_map = {
    "Wind":"util",
    "Temp + Humidity" :"util",
    "Usage":"util",
    "P1 Smart Meter":"util",
    "Dimmer":"dimmer",
    "Light/Switch":"switch",
    "Scene":"scene"
}

# ------------------------------------------------------------
#     End of Configurable data
#     Do not change below this line 
#     Unless you know what your doing
# ------------------------------------------------------------


def get_language():
    PROFILEDIR = os.getenv("RHASSPY_PROFILE_DIR",default="nl")
    return re.sub(".*/(..)$","\\1",PROFILEDIR)

def get_text(textid=Text.ERROR,textsubid=None):
    lang = get_language()
    default_lang = "nl"
    if not lang in text:
        lang = default_lang

    if textid in text[lang]:
        if textsubid is None:
            return text[lang][textid]
        elif textsubid in text[lang][textid]:
            return text[lang][textid][textsubid]

    return text[lang][Text.ERROR]

def get_url(key):
    return config["urls"][key]

def replace_decimal_point(str_in):
    decimal_point = get_text(Text.DecimalPoint)
    return str_in.replace(".", f" {decimal_point} ")
    
def get_instances(json):
    instances = {}
    if "Domo" in config["urls"]:
        try:
            from intentdomo import IntentDomo
            instances["Domo"] = IntentDomo(json)
        except Exception as exc:
            log.error(f"Exception instantiating Domo: {exc}")
    if "Kodi" in config["urls"]:
        try:
            from intentkodi import IntentKodi
            instances["Kodi"] = IntentKodi(json)
        except Exception as exc:
            log.error(f"Exception instantiating Kodi: {exc}")
    if "SmartCity" in config["urls"]:
        try:
            from intentsmartcity import IntentSmartCity
            instances["SmartCity"] = IntentSmartCity(json)
        except Exception as exc:
            log.error(f"Exception instantiating SmartCity: {exc}")
    if "KNMI" in config["urls"]:
        try:
            from intentknmi import IntentKNMI
            instances["KNMI"] = IntentKNMI(json)
        except Exception as exc:
            log.error(f"Exception instantiating SmartCity: {exc}")
    return instances

def get_slots(filename):
    fslots = open(filename, "r")
    lines = fslots.read().splitlines()
    fslots.close()
    slots = {}
    for l in lines:
        line = l.split(':')
        if len(line) == 2:
            name = re.sub('[)(]', '', line[0])
            date = line[1]
            slots[name] = date
    return slots


def get_beauforttext(speed):
    beaufort_data = get_text(DomoText.GetWind_Beaufort)
    log.debug(f"get_beauforttext:beaufort_data={beaufort_data}.")

    for line in beaufort_data:
        if line[1]>speed:
            wind = line
            return (line[0],line[2]+", "+line[3])

    return (0,text[lang][Text.ERROR])


def get_rhasspy_domo_values(name,desc):
    log.debug(f"get_slotvalues:name={name},desc={desc}.")
    slotvalue = ""
    if len(desc) > 0:
        slotvalue = desc
        log.debug(f"found Desc:{slotvalue}.")
    elif len(name) > 0:
        slotvalue = re.sub("^.*- ","",name)  # remove everyting before -
        log.debug(f"found Name:{slotvalue}.")
    slotvalue = slotvalue.strip()
    if len(slotvalue) > 0:
        if re.search("\(.*\)",slotvalue) is None:
            slotvalue = f"({slotvalue})"
        return slotvalue
    return ""


def get_rhasspy_domo_slots(domo_devices):
    slots = { "switch": [],
            "dimmer": [],
            "scene": [],
            "util": []}
    for dev in domo_devices:
        slot_value = get_rhasspy_domo_values(dev["Name"],dev["Description"])
        slot_idx = dev["idx"]
        slot_type = dev["Type"]
        log.debug(f"slot_type={slot_type},slot_value={slot_value}")
        if slot_type in domo_rhasspy_type_map:
            slot_name = domo_rhasspy_type_map[slot_type]
            slots[slot_name].append(f"{slot_value}:{slot_idx}")
            slot_type = dev["SwitchType"]
            if slot_type in domo_rhasspy_type_map:
                slot_name = domo_rhasspy_type_map[slot_type]
                slots[slot_name].append(f"{slot_value}:{slot_idx}")
    return slots


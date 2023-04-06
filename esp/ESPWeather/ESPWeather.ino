///////////////////////////////////////////////////////////////////////////////////////////////////
// BresserWeatherSensorDomoticz.ino
//
// Based on:
// Example for BresserWeatherSensorReceiver - based on BresserWeatherSensorMQTT
//
// Provides sensor data as MQTT messages via WiFi to Domoticz (https://domoticz.com/)
// (MQTT plugin for Domoticz required) 
//
// At startup, first a WiFi connection and then a connection to the MQTT broker is established.
// (Edit secrets.h accordingly!)
//
// Then receiving a complete set of data from a weather sensor is tried periodically.
// If successful, sensor data is published as MQTT message.
// From the sensor data, some additional data is calculated and included in the message.
//
// The Domoticz topic is published at an interval of >DATA_INTERVAL.
// The 'status' and the 'radio' topics are published at an interval of STATUS_INTERVAL.
//
// If sleep mode is enabled (SLEEP_EN), the device goes into deep sleep mode after data has 
// been published. If AWAKE_TIMEOUT is reached before data has been published, deep sleep is 
// entered, too. After SLEEP_INTERVAL, the controller is restarted.
//
//
// https://github.com/matthias-bs/BresserWeatherSensorReceiver
//
// Based on:
// arduino-mqtt Joël Gähwiler (256dpi) (https://github.com/256dpi/arduino-mqtt)
// ArduinoJson by Benoit Blanchon (https://arduinojson.org)

// MQTT subscriptions:
//     - none -
//
// MQTT publications:               
//     <base_topic>/radio   radio transceiver info as JSON string - see publishRadio()
//     <base_topic>/status  "online"|"offline"|"dead"$
//     domoticz/in          topic required by Domoticz
// $ via LWT
//
//
// created: 08/2022
//
//
// MIT License
//
// Copyright (c) 2022 franki29 & Matthias Prinke 
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// History:
//
// 20220815 Created from BresserWeatherSensorMQTT
// 20221006 Modified secure/non-secure client implementation
//          Modified string buffer size handling
// 20221227 Replaced DEBUG_PRINT/DEBUG_PRINTLN by Arduino logging functions
// 20230124 Improved WiFi connection robustness
//
// ToDo:
// 
// - 
//
// Notes:
//
// - To enable wakeup from deep sleep on ESP8266, GPIO16 (D0) must be connected to RST!
//   Add a jumper to remove this connection for programming!
// - MQTT code based on https://github.com/256dpi/arduino-mqtt 
// - For secure MQTT (TLS server verifycation, check the following examples:
//   - ESP32:   
//     https://github.com/espressif/arduino-esp32/blob/master/libraries/WiFiClientSecure/examples/WiFiClientSecure/WiFiClientSecure.ino
//   - ESP8266: 
//     https://github.com/esp8266/Arduino/blob/master/libraries/ESP8266WiFi/examples/BearSSL_Validation/BearSSL_Validation.ino
//
///////////////////////////////////////////////////////////////////////////////////////////////////

#include <Arduino.h>
#define OLED_ON  // Enable OLED when present and wanted

// BEGIN User specific options
#define LED_EN                  // Enable LED indicating successful data reception
// Please change Domoticz IDX settings according to your configuration
#define DOMO_WIND_IDX   227     // IDX of Domoticz virtual wind sensor
#define DOMO_RAIN_IDX   226     // IDX of Domoticz virtual rain sensor
#define DOMO_TH_IDX     225     // IDX of Domoticz virtual temperature/humidity sensor
#define LED_GPIO        2       // LED pin
#define TIMEZONE        2       // UTC + TIMEZONE
#define PAYLOAD_SIZE    256     // maximum MQTT message size
#define TOPIC_SIZE      50      // maximum MQTT topic size
#define HOSTNAME_SIZE   30      // maximum hostname size
#define RX_TIMEOUT      90000   // sensor receive timeout [ms]
#define STATUS_INTERVAL 30000   // MQTT status message interval [ms]
#define DATA_INTERVAL   15000   // MQTT data message interval [ms]
#define AWAKE_TIMEOUT   300000  // maximum time until sketch is forced to sleep [ms]
#define SLEEP_INTERVAL  300000  // sleep interval [ms]
#define WIFI_RETRIES    10      // WiFi connection retries
#define WIFI_DELAY      1000    // Delay between connection attempts [ms]
#define SLEEP_EN        false   // enable sleep mode (see notes above!)
//#define USE_SECUREWIFI          // use secure WIFI
#define USE_WIFI              // use non-secure WIFI

const char sketch_id[] = "ESPWeather-20230403.1";
char start_string[64];

#ifdef OLED_ON
//Libraries for OLED Display
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


//OLED pins
#define OLED_SDA 4
#define OLED_SCL 15 
#define OLED_RST 16
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);

void oled_clear() {
   display.clearDisplay();
}
void oled_show(const char text[], const int row=-1, const int col=-1) {
  Serial.printf("oled_show(%s,%d,%d)",text,row,col);
  display.clearDisplay();
  display.setCursor(col,row);
  display.print(text);
  display.display();
}

void oled_showf(int size, const char* format, ...){
  char text[1024];
  va_list argptr;
  va_start(argptr, format);
  vsprintf(text, format, argptr);
  va_end(argptr);
  Serial.printf("oled_showf(size=%d, string=<%s>)\n",size,text);
  display.clearDisplay();
  display.setCursor(0,0);
  display.setTextSize(size);
  display.print(text);
  display.display();
}
void oled_setup() { 
  
  //reset OLED display via software
  pinMode(OLED_RST, OUTPUT);
  digitalWrite(OLED_RST, LOW);
  delay(20);
  digitalWrite(OLED_RST, HIGH);
  
  //initialize OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3c, false, false)) { // Address 0x3C for 128x32
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }

  display.clearDisplay();
  display.setTextColor(WHITE);
  oled_showf(1,"%s",start_string);
  }

#else
void oled_setup() {}
void oled_clear() {}
void oled_show(const int row, const char text[]) {}
void oled_showf(int size, const char* format, ...){
  char text[1024];
  va_list argptr;
  va_start(argptr, format);
  vsprintf(text, format, argptr);
  va_end(argptr);
  Serial.println(text);
}
#endif

// Enable to debug MQTT connection; will generate synthetic sensor data.
//#define _DEBUG_MQTT_

// END User specific configuration

#if ( defined(USE_SECUREWIFI) && defined(USE_WIFI) ) || ( !defined(USE_SECUREWIFI) && !defined(USE_WIFI) )
    #error "Either USE_SECUREWIFI OR USE_WIFI must be defined!"
#endif

#if defined(ESP32)
    #if defined(USE_WIFI)
        #include <WiFi.h>
    #elif defined(USE_SECUREWIFI)
        #include <WiFiClientSecure.h>
    #endif
#elif defined(ESP8266)
    #include <ESP8266WiFi.h>
#endif


#include <MQTT.h>
#include <ArduinoJson.h>
#include <time.h>
#include "WeatherSensorCfg.h"
#include "WeatherSensor.h"
#include "WeatherUtils.h"


//enable only one of these below, disabling both is fine too.
// #define CHECK_CA_ROOT
// #define CHECK_PUB_KEY
// Arduino 1.8.19 ESP32 WiFiClientSecure.h: "SHA1 fingerprint is broken now!"
// #define CHECK_FINGERPRINT
////--------------------------////

#include "secrets.h"

char timeBuf[10];

char* curtime() {
    time_t     now = time(0);
    struct tm  tstruct;
    tstruct = *localtime(&now);
    // Visit http://en.cppreference.com/w/cpp/chrono/c/strftime
    // for more information about date/time format
    strftime(timeBuf, 10, "%X", &tstruct);

    return timeBuf;
}

#ifndef SECRETS
    // Optionally copy everything between BEGIN secrets / END secrets to secrets.h
    // Otherwise, leave secrets.h as an empty file and edit the contents below.

    // BEGIN secrets
    #define SECRETS
    const char ssid[] = "SSID";
    const char pass[] = "password";

    #define HOSTNAME "BresserDomo"
    #define APPEND_CHIP_ID

    const int  MQTT_PORT   = 8883; // typically 8883 with TLS / 1883 without TLS 
    const char MQTT_HOST[] = "xxx.yyy.zzz.com";
    const char MQTT_USER[] = "";   // leave blank if no credentials used
    const char MQTT_PASS[] = "";   // leave blank if no credentials used

    #ifdef CHECK_CA_ROOT
    static const char digicert[] PROGMEM = R"EOF(
    -----BEGIN CERTIFICATE-----
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    -----END CERTIFICATE-----
    )EOF";
    #endif

    #ifdef CHECK_PUB_KEY
    // Extracted by: openssl x509 -pubkey -noout -in fullchain.pem
    static const char pubkey[] PROGMEM = R"KEY(
    -----BEGIN PUBLIC KEY-----
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    xxxxxxxx
    -----END PUBLIC KEY-----
    )KEY";
    #endif

    #ifdef CHECK_FINGERPRINT
    // Extracted by: openssl x509 -fingerprint -in fullchain.pem
    static const char fp[] PROGMEM = "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD";
    #endif
#endif

WeatherSensor weatherSensor;
struct tm timeinfo;


// MQTT topics
const char MQTT_PUB_STATUS[]      = "/status";
const char MQTT_PUB_RADIO[]       = "/radio";
const char MQTT_PUB_DOMO[]        = "domoticz/in"; //mqtt plugin for domoticz needed

char mqttPubStatus[TOPIC_SIZE];
char mqttPubRadio[TOPIC_SIZE];
char Hostname[HOSTNAME_SIZE];

//////////////////////////////////////////////////////

#if (defined(CHECK_PUB_KEY) and defined(CHECK_CA_ROOT)) or (defined(CHECK_PUB_KEY) and defined(CHECK_FINGERPRINT)) or (defined(CHECK_FINGERPRINT) and defined(CHECK_CA_ROOT)) or (defined(CHECK_PUB_KEY) and defined(CHECK_CA_ROOT) and defined(CHECK_FINGERPRINT))
#error "cant have both CHECK_CA_ROOT and CHECK_PUB_KEY enabled"
#endif

// Generate WiFi network instance
#if defined(ESP32)
    #if defined(USE_WIFI)
        WiFiClient net;
    #elif defined(USE_SECUREWIFI)
        WiFiClientSecure net;
    #endif
#elif defined(ESP8266)
    #if defined(USE_WIFI)
        WiFiClient net;
    #elif defined(USE_SECUREWIFI)
     BearSSL::WiFiClientSecure net;
   #endif
#endif


//
// Generate MQTT client instance
// N.B.: Default message buffer size is too small!
//
MQTTClient client(PAYLOAD_SIZE);

uint32_t lastMillis = 0;
uint32_t statusPublishPreviousMillis = 0;
time_t now;

void publishWeatherdata(void);
void mqtt_connect(void);


//
// Wait for WiFi connection
//
void wifi_wait()
{
  int count = 0;
  while (WiFi.status() != WL_CONNECTED) {
      delay(WIFI_DELAY);
      if (++count == WIFI_RETRIES) {
          oled_showf(1,"WiFi connection timed out, will restart after %d s\n", SLEEP_INTERVAL/1000);
          ESP.deepSleep(SLEEP_INTERVAL * 1000);
      }
      oled_showf(1,"%s\nWIFI %s try %d",start_string,ssid,count); 
  }
}

//
// Setup WiFi in Station Mode
//
void mqtt_setup(void)
{
  oled_showf(1,"%s\nWIFI %s",start_string,ssid);
  WiFi.hostname(Hostname);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  wifi_wait();
  
	configTime(TIMEZONE * 3600, 0, "pool.ntp.org", "time.nist.gov");
	now = time(nullptr);
  int count = 0;
	while (now < 1510592825)
	{
    oled_showf(1,"%s\nWIFI: %s\nTime: SNTP try %d",start_string,ssid,++count); 
		delay(500);
		now = time(nullptr);
	}

  oled_showf(1,"%s\nWIFI: %s\nTime: %s",start_string,ssid,curtime()); 

    #ifdef USE_SECUREWIFI
        // Note: TLS security needs correct time
       #ifdef CHECK_CA_ROOT
            BearSSL::X509List cert(digicert);
            net.setTrustAnchors(&cert);
        #endif
        #ifdef CHECK_PUB_KEY
            BearSSL::PublicKey key(pubkey);
            net.setKnownKey(&key);
        #endif
        #ifdef CHECK_FINGERPRINT
            net.setFingerprint(fp);
        #endif
        #if (!defined(CHECK_PUB_KEY) and !defined(CHECK_CA_ROOT) and !defined(CHECK_FINGERPRINT))
            // do not verify tls certificate
            net.setInsecure();
        #endif
    #endif

    oled_showf(1,"%s\nWIFI: %s\nTime: %s\nGet MQTT:%s:%d",
      start_string,ssid,curtime(),MQTT_HOST, MQTT_PORT); 
    client.begin(MQTT_HOST, MQTT_PORT, net);
    
    // set up MQTT receive callback (if required)
    //client.onMessage(messageReceived);
    
    client.setWill(mqttPubStatus, "dead", true /* retained*/, 1 /* qos */);

    mqtt_connect();    
}


//
// (Re-)Connect to WLAN and connect MQTT broker
//
void mqtt_connect(void)
{
    Serial.print(F("Checking wifi..."));
    wifi_wait();
    Serial.print(F("Checked wifi..."));
    while (!client.connect(MQTT_HOST, MQTT_USER, MQTT_PASS))  // AM Error corrected: MQTT_HOST was Hostname
    {
    Serial.print(F("Checked wifi..."));
      oled_showf(1,"%s\nWIFI: %s\nTime: %s\nGet MQTT (%s:%d) error <%d>",
        start_string,ssid,curtime(),MQTT_HOST, MQTT_PORT, client.lastError()); 
        delay(1000);
    }

    oled_showf(1,"%s\nWIFI: %s\nTime: %s\nMQTT %s:%d\nPublish Status (topic:payload)(%s:online)",
        start_string,ssid,curtime(),MQTT_HOST, MQTT_PORT, mqttPubStatus); 
    //client.subscribe(MQTT_SUB_IN);
    client.publish(mqttPubStatus, "online");
}


//
// MQTT message received callback
//
/*
void messageReceived(String &topic, String &payload)
{
}
*/



/*!
  \brief Publish weather data as MQTT message

  \param complete Indicate that entire data is complete, regardless of the flags temp_ok/wind_ok/rain_ok
                  (which reflect only the state of the last message)
*/
void publishWeatherdata(void)
{
    char domo_payload[PAYLOAD_SIZE];
    char domo2_payload[PAYLOAD_SIZE];
    char domo3_payload[PAYLOAD_SIZE];
    float temp_c = 100.0;
    char wind_dir_buf[4] = "?";
    char* wind_dir;
    float wind_ms = 0;
    int const i = 0;

    // ArduinoJson does not allow to set number of decimals for floating point data -
    // neither does MQTT Dashboard...
    // Therefore the JSON string is created manually.
    
    // domoticz virtual wind sensor
    if (weatherSensor.sensor[i].wind_ok && weatherSensor.sensor[i].temp_ok) {
      sprintf(domo_payload, "{\"idx\":%d,\"nvalue\":0,\"svalue\":\"%.1f", 
         DOMO_WIND_IDX, weatherSensor.sensor[i].wind_direction_deg);
//      char buf[4];
      wind_dir = winddir_flt_to_str(weatherSensor.sensor[i].wind_direction_deg, wind_dir_buf);
      sprintf(&domo_payload[strlen(domo_payload)], ";%s", wind_dir);
	    wind_ms = weatherSensor.sensor[i].wind_avg_meter_sec;
      sprintf(&domo_payload[strlen(domo_payload)], ";%.1f", wind_ms *10);
      sprintf(&domo_payload[strlen(domo_payload)], ";%.1f", weatherSensor.sensor[i].wind_gust_meter_sec *10);
	    temp_c = weatherSensor.sensor[i].temp_c;
      sprintf(&domo_payload[strlen(domo_payload)], ";%.1f", temp_c);
      sprintf(&domo_payload[strlen(domo_payload)], ";%.1f", perceived_temperature(weatherSensor.sensor[i].temp_c,
                                                                                  weatherSensor.sensor[i].wind_avg_meter_sec,
                                                                                  weatherSensor.sensor[i].humidity));
      sprintf(&domo_payload[strlen(domo_payload)], "\"}");
      Serial.printf("%s: %s\n", MQTT_PUB_DOMO, domo_payload);
      client.publish(MQTT_PUB_DOMO, domo_payload, false, 0);      
    }
    
    // domoticz virtual rain sensor
    if (weatherSensor.sensor[i].rain_ok) {
      sprintf(domo2_payload, "{\"idx\":%d,\"nvalue\":0,\"svalue\":\"%.1f", 
        DOMO_RAIN_IDX, weatherSensor.sensor[i].rain_mm *100);
      sprintf(&domo2_payload[strlen(domo2_payload)], ";%.1f", weatherSensor.sensor[i].rain_mm);
      sprintf(&domo2_payload[strlen(domo2_payload)], "\"}");
      Serial.printf("%s: %s\n", MQTT_PUB_DOMO, domo2_payload);
      client.publish(MQTT_PUB_DOMO, domo2_payload, false, 0);
    }

    // domoticz virtual temp & humidity sensor
    if (weatherSensor.sensor[i].temp_ok && weatherSensor.sensor[i].humidity_ok) {
      sprintf(domo3_payload, "{\"idx\":%d,\"nvalue\":0,\"svalue\":\"%.1f", DOMO_TH_IDX, weatherSensor.sensor[i].temp_c);
      sprintf(&domo3_payload[strlen(domo3_payload)], ";%d", weatherSensor.sensor[i].humidity);
      sprintf(&domo3_payload[strlen(domo3_payload)], ";0\"}");
      Serial.printf("%s: %s\n", MQTT_PUB_DOMO, domo3_payload);
      client.publish(MQTT_PUB_DOMO, domo3_payload, false, 0);
    }
      if (temp_c < 100){
        oled_showf(2, "%s\n%.1f C\nWind %s\n%.1f m/s", curtime(), temp_c, wind_dir, wind_ms);
      }
}


//
// Publish radio receiver info as JSON string via MQTT
// - RSSI: Received Signal Strength Indication
//
void publishRadio(void)
{
    DynamicJsonDocument payload(PAYLOAD_SIZE);
    char mqtt_payload[PAYLOAD_SIZE];
    
    payload["rssi"] = weatherSensor.rssi;
    serializeJson(payload, mqtt_payload);
    Serial.printf("Publish Status (topic:payload)(%s:%s)\n", mqttPubRadio, mqtt_payload);
    client.publish(mqttPubRadio, mqtt_payload, false, 0);
    payload.clear();
}


//
// Setup
//
void setup() {
    //initialize Serial Monitor
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    snprintf(start_string, 64, "%s\nWind:%d,Rain:%d,TH:%d", 
         sketch_id,DOMO_WIND_IDX, DOMO_RAIN_IDX, DOMO_TH_IDX);
    Serial.println(start_string);
    Serial.println();

    oled_setup();

    #ifdef LED_EN
      // Configure LED output pins
      pinMode(LED_GPIO, OUTPUT);
      digitalWrite(LED_GPIO, HIGH);
    #endif

    strncpy(Hostname, HOSTNAME, 20);
    snprintf(mqttPubStatus, TOPIC_SIZE, "%s%s", Hostname, MQTT_PUB_STATUS);
    snprintf(mqttPubRadio,  TOPIC_SIZE, "%s%s", Hostname, MQTT_PUB_RADIO);

    mqtt_setup();

    weatherSensor.begin();
}


/*!
  \brief Wrapper which allows passing of member function as parameter
*/
void clientLoopWrapper(void)
{
    client.loop();
}


//
// Main execution loop
//
void loop() {
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.print(F("Checking wifi"));
        while (WiFi.waitForConnectResult() != WL_CONNECTED)
        {
            WiFi.begin(ssid, pass);
            Serial.print(".");
            delay(10);
        }
        Serial.println(F("connected"));
    }
    else
    {
        if (!client.connected())
        {
            mqtt_connect();
        }
        else
        {
            client.loop();
        }
    }
    
    const uint32_t currentMillis = millis();
    if (currentMillis - statusPublishPreviousMillis >= STATUS_INTERVAL) {
        // publish a status message @STATUS_INTERVAL
        statusPublishPreviousMillis = currentMillis;
        Serial.printf("Publish Status (topic:payload)(%s:%s)\n", mqttPubStatus, "online");
        client.publish(mqttPubStatus, "online");
        publishRadio();
    }

    bool decode_ok = false;
    #ifdef _DEBUG_MQTT_
        decode_ok = weatherSensor.genMessage(0 /* slot */, 0x01234567 /* ID */, 1 /* type */, 0 /* channel */);
    #else
        // Clear sensor data buffer
        weatherSensor.clearSlots();

        // Attempt to receive entire data set with timeout of RX_TIMEOUT
        decode_ok = weatherSensor.getData(RX_TIMEOUT, DATA_TYPE | DATA_COMPLETE, SENSOR_TYPE_WEATHER1, &clientLoopWrapper);
    #endif

    #ifdef LED_EN
        if (decode_ok) {
          digitalWrite(LED_GPIO, LOW);
        } else {
          digitalWrite(LED_GPIO, HIGH);
        }
    #endif
    
    // publish a data message @DATA_INTERVAL
    if (millis() - lastMillis > DATA_INTERVAL) { 
        lastMillis = millis();
        if (decode_ok)
            publishWeatherdata();
    }

    bool force_sleep = millis() > AWAKE_TIMEOUT;

    // Go to sleep only after complete set of data has been sent
    if (SLEEP_EN && (decode_ok || force_sleep)) {
        #ifdef _DEBUG_MODE_
            if (force_sleep) {
                Serial.println(F("Awake time-out!"));
            } else {
                Serial.println(F("Data forwarding completed.")); 
            }
        #endif
        Serial.printf("Sleeping for %d ms\n", SLEEP_INTERVAL); 
        Serial.printf("Publish Status (topic:payload)(%s:%s)\n", mqttPubStatus, "offline");
        Serial.flush();
        client.publish(mqttPubStatus, "offline", true /* retained */, 0 /* qos */);
        client.disconnect();
        client.loop();
        #ifdef LED_EN
            pinMode(LED_GPIO, INPUT);
        #endif
        ESP.deepSleep(SLEEP_INTERVAL * 1000);
    }
} // loop()

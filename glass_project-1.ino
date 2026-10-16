/*
 * ESP8266 Live Location Voice Alert System
 *
 * Supports BOTH:
 *  1. Online Mode via Vercel (HTTPS Cloud Server)
 *  2. Local Mode via Localhost:5000 (Local Wi-Fi)
 *
 * Reads Pin D0 (GPIO 16) and sends output signal to Pin D1 (GPIO 5).
 * When D0 = 0: Speaks "You're in the bypass location" on the website!
 */

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>

// ==========================================
// 1. Wi-Fi Configuration
// ==========================================
const char* ssid     = "Airtel_Aurora_Academy";
const char* password = "Onemillionsoon";

// ==========================================
// 2. Server Configuration (Online vs Local)
// ==========================================
// Set to 'true' to use your online Vercel website!
// Set to 'false' to use your PC on localhost:5000
const bool USE_ONLINE_VERCEL = true;

// Online Vercel Domain:
const char* vercel_host = "glass-liart-seven.vercel.app";

// Local PC Server settings:
const char* local_host = "192.168.1.14";
const int   local_port = 5000;

// ==========================================
// 3. Hardware Pin Definitions
// ==========================================
#ifndef D0
#define D0 16  // GPIO 16 (Digital Input)
#endif

#ifndef D1
#define D1 5   // GPIO 5 (Digital Output)
#endif

#ifndef LED_BUILTIN
#define LED_BUILTIN 2 // Onboard Blue LED
#endif

int last_d0_state = -1;
unsigned long last_heartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 1000;

// Function to send current pin state to server
void sendUpdateToServer(int d0, int d1) {
  if (WiFi.status() != WL_CONNECTED) return;

  String url = "/api/update?d0=" + String(d0) + "&d1=" + String(d1);

  if (USE_ONLINE_VERCEL) {
    // Online Vercel Mode (HTTPS port 443)
    WiFiClientSecure secureClient;
    secureClient.setInsecure(); // Skip SSL fingerprint check for seamless Vercel connection
    secureClient.setTimeout(2000);

    if (secureClient.connect(vercel_host, 443)) {
      secureClient.print(String("GET ") + url + " HTTP/1.1\r\n" +
                         "Host: " + vercel_host + "\r\n" +
                         "User-Agent: ESP8266\r\n" +
                         "Connection: close\r\n\r\n");
      secureClient.stop();
    }
  } else {
    // Local Mode (HTTP port 5000)
    WiFiClient client;
    client.setTimeout(250);

    if (client.connect(local_host, local_port)) {
      client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                   "Host: " + local_host + ":" + String(local_port) + "\r\n" +
                   "Connection: close\r\n\r\n");
      client.stop();
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n--- ESP8266 Location Monitor System Started ---");

  pinMode(D0, INPUT);
  pinMode(D1, OUTPUT);
  digitalWrite(D1, LOW);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // OFF by default

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[SUCCESS] Connected to Wi-Fi!");
  if (USE_ONLINE_VERCEL) {
    Serial.print("Online Vercel Target: https://");
    Serial.println(vercel_host);
  } else {
    Serial.print("Local Server Target: http://");
    Serial.print(local_host);
    Serial.print(":");
    Serial.println(local_port);
  }
}

void loop() {
  int d0_state = digitalRead(D0);
  int d1_state = LOW;

  // When D0 = 0 (triggered), drive D1 HIGH
  if (d0_state == LOW) {
    d1_state = HIGH;
    digitalWrite(D1, HIGH);
    digitalWrite(LED_BUILTIN, LOW); // LED ON
  } else {
    d1_state = LOW;
    digitalWrite(D1, LOW);
    digitalWrite(LED_BUILTIN, HIGH); // LED OFF
  }

  // Send update on state change or heartbeat
  unsigned long now = millis();
  if (d0_state != last_d0_state || (now - last_heartbeat >= HEARTBEAT_INTERVAL)) {
    sendUpdateToServer(d0_state, d1_state);
    last_d0_state = d0_state;
    last_heartbeat = now;
  }

  delay(20);
}

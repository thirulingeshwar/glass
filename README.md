# Smart Glass ESP8266 Live Location Monitor

A real-time IoT bypass location monitoring system using **ESP8266**, **Python Flask**, and **Vercel** with built-in browser **Text-To-Speech (Voice Alert)**.

---

## 🚀 Features

* **Hardware Input (D0):** Reads digital sensor input on Pin D0 (GPIO 16).
* **Hardware Output (D1):** Automatically drives Pin D1 (GPIO 5) when triggered.
* **Online Cloud Server (Vercel):** Hosts the live web dashboard accessible from anywhere in the world.
* **Real-time Voice Alert:** When `D0 = 0`, a popup appears and automatically speaks aloud:  
  🗣️ **"You're in the bypass location"**
* **Dual Operation Mode:**
  1. **Online (Vercel):** Operates over HTTPS from any internet connection.
  2. **Local (localhost:5000):** Operates offline on your local Wi-Fi.

---

## 📌 Pinout & Wiring

| ESP8266 Pin | GPIO | Function | Description |
|---|---|---|---|
| **D0** | GPIO 16 | **INPUT** | Digital Input Sensor (Active LOW) |
| **D1** | GPIO 5 | **OUTPUT** | Output Signal (HIGH when triggered) |
| **GND** | GND | Ground | Common Ground |
| **3V3 / Vin** | Power | Power | 3.3V / 5V Power Supply |

---

## 🌐 Deploy to Vercel (1-Click)

1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Select your repository: **`glass`**.
4. Leave all default settings unchanged (Vercel automatically detects Python via `api/index.py` and `requirements.txt`).
5. Click **"Deploy"**.
6. Once deployed, Vercel gives you your live URL (e.g., `https://glass-yourname.vercel.app`).

---

## ⚡ Connecting ESP8266 to Vercel Online

In `glass_project-1.ino`:
1. Change `vercel_host` to your deployed Vercel domain:
   ```cpp
   const char* vercel_host = "your-app.vercel.app";
   ```
2. Upload the sketch to your ESP8266 using Arduino IDE!
3. Open your Vercel URL on your phone or laptop from anywhere!

---

## 💻 Local Testing (localhost:5000)

If testing locally without Vercel:
1. Run the local server:
   ```bash
   python server.py
   ```
2. Open [http://localhost:5000](http://localhost:5000) in your browser.

"""
Localhost:5000 Web Server for ESP8266 Location Monitor
Clean message page with Text-To-Speech (Voice):
When D0 = 0, displays the popup AND speaks aloud "You're in the bypass location".
When D0 = 1, no message (standby).
"""

from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# State dictionary to store latest readings from ESP8266
sensor_data = {
    "d0": 1,
    "d1": 0,
    "count": 0,
    "last_seen": 0,
    "connected": False
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Location Monitor - Voice Alert</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: #090d16;
      color: #ffffff;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      overflow: hidden;
      cursor: pointer;
    }

    /* Idle / Waiting Screen */
    .idle-container {
      text-align: center;
      transition: opacity 0.3s ease;
    }
    .radar {
      width: 70px;
      height: 70px;
      border-radius: 50%;
      border: 3px solid #38bdf8;
      margin: 0 auto 20px;
      position: relative;
      animation: ripple 2s infinite ease-out;
    }
    @keyframes ripple {
      0% { transform: scale(0.8); opacity: 1; }
      100% { transform: scale(1.6); opacity: 0; }
    }
    .idle-text {
      font-size: 18px;
      color: #64748b;
      letter-spacing: 1px;
    }

    /* Popup Modal when D0 = 0 */
    .popup-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.78);
      backdrop-filter: blur(8px);
      display: flex;
      justify-content: center;
      align-items: center;
      opacity: 0;
      pointer-events: none;
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .popup-overlay.show {
      opacity: 1;
      pointer-events: auto;
    }

    .popup-card {
      background: #111827;
      border: 2px solid #ef4444;
      border-radius: 28px;
      padding: 45px 35px;
      max-width: 480px;
      width: 90%;
      text-align: center;
      box-shadow: 0 0 50px rgba(239, 68, 68, 0.4);
      transform: scale(0.85);
      transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .popup-overlay.show .popup-card {
      transform: scale(1);
    }

    .alert-icon {
      font-size: 56px;
      margin-bottom: 12px;
      display: inline-block;
      animation: pulse 1s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.12); }
      100% { transform: scale(1); }
    }

    .popup-title {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #f87171;
      margin-bottom: 12px;
    }

    .popup-message {
      font-size: 26px;
      font-weight: 800;
      line-height: 1.3;
      color: #ffffff;
      margin-bottom: 14px;
    }

    .voice-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid rgba(239, 68, 68, 0.4);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      color: #fca5a5;
      font-weight: 600;
      margin-bottom: 14px;
    }

    .popup-time {
      font-size: 13px;
      color: #94a3b8;
    }

    /* Voice Status Bar at Bottom */
    .audio-hint {
      position: fixed;
      bottom: 20px;
      font-size: 12px;
      color: #475569;
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 6px 14px;
      border-radius: 20px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
  </style>
</head>
<body>

  <!-- Idle Screen -->
  <div class="idle-container" id="idleBox">
    <div class="radar"></div>
    <div class="idle-text">Waiting for location update...</div>
  </div>

  <!-- Popup Box (Appears when D0 = 0) -->
  <div class="popup-overlay" id="popupBox">
    <div class="popup-card">
      <div class="alert-icon">🚨</div>
      <div class="popup-title">Location Notification</div>
      <div class="popup-message" id="messageText">You're in the bypass location</div>
      <div class="voice-badge">
        <span>🔊</span>
        <span>Voice Alert Playing</span>
      </div>
      <div class="popup-time" id="timePassed"></div>
    </div>
  </div>

  <div class="audio-hint">
    <span>🔊</span>
    <span id="audioStatus">Voice Enabled (Click anywhere to test)</span>
  </div>

  <script>
    let wasActive = false;
    let voiceUnlocked = false;

    // Unlock browser audio on user gesture
    function unlockAudio() {
      if (!voiceUnlocked && 'speechSynthesis' in window) {
        voiceUnlocked = true;
        document.getElementById('audioStatus').innerText = 'Voice Ready';
      }
    }
    window.addEventListener('click', unlockAudio);
    window.addEventListener('keydown', unlockAudio);

    // Text to Speech Function
    function speakVoice(text) {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop any pending speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;  // Normal speed
        utterance.pitch = 1.0; // Normal pitch
        utterance.lang = 'en-US';
        window.speechSynthesis.speak(utterance);
      }
    }

    async function checkStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();

        const popup = document.getElementById('popupBox');
        const idle = document.getElementById('idleBox');
        const timePassed = document.getElementById('timePassed');

        // If D0 = 0 -> Popup & Speak
        if (data.d0 === 0) {
          if (!wasActive) {
            const now = new Date();
            timePassed.innerText = 'Detected at: ' + now.toLocaleTimeString();

            // Speak the text aloud!
            speakVoice("You're in the bypass location");

            wasActive = true;
          }
          popup.classList.add('show');
          idle.style.opacity = '0.15';
        } else {
          // If D0 = 1 -> Dismiss Popup & cancel speech
          popup.classList.remove('show');
          idle.style.opacity = '1';
          if (wasActive) {
            if ('speechSynthesis' in window) {
              window.speechSynthesis.cancel();
            }
            wasActive = false;
          }
        }
      } catch (err) {}
    }

    // Fast 100ms polling for instant popup & voice
    setInterval(checkStatus, 100);
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/update', methods=['GET', 'POST'])
def update_signal():
    """Endpoint called by ESP8266."""
    global sensor_data

    if request.method == 'POST' and request.is_json:
        payload = request.get_json()
        d0 = int(payload.get('d0', 0))
        d1 = int(payload.get('d1', 0))
    else:
        d0 = int(request.args.get('d0', sensor_data['d0']))
        d1 = int(request.args.get('d1', sensor_data['d1']))

    if d0 == 0 and sensor_data['d0'] == 1:
        sensor_data['count'] += 1

    sensor_data['d0'] = d0
    sensor_data['d1'] = d1
    sensor_data['last_seen'] = time.time()
    sensor_data['connected'] = True

    return jsonify({"status": "ok", "d0": sensor_data['d0']})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Polled by frontend browser every 100ms."""
    is_connected = (time.time() - sensor_data['last_seen']) < 5.0 if sensor_data['last_seen'] > 0 else False
    return jsonify({
        "d0": sensor_data['d0'],
        "connected": is_connected
    })

if __name__ == '__main__':
    print("Starting Clean Popup Server with Voice on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)

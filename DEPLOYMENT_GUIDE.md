# 🍼 The "Very Simple" OmniClaw Guide (v4.0.0)

Welcome! If you want to build a super-smart robot assistant that you can text from your phone, and you want it to run **24 hours a day, 7 days a week** for your personal life or business—this guide is for you! 

We will go step-by-step. No confusing words, no assumed knowledge. You will not need to watch a YouTube tutorial to figure this out. Everything is right here.

## 🌟 Real-World Practical Scenarios
Before deploying, here is what OmniClaw allows you to do immediately out of the box:
- **Autonomous Bug Bounty**: Let OmniClaw scan authorized scopes overnight using its Context-Aware Fuzzer. Wake up to pre-written disclosure PDFs with validated PoCs.
- **Smart Infrastructure Monitoring**: It can hook into your server's eBPF events and automatically apply firewall blocks or restart failing services without paging you at 3 AM.
- **The "Do My Work" Chatbot**: Link it to Telegram and simply message `/task Update my daily standup notes from the GitHub commits I've made today and post to Slack`.
- **Trading/Automated Analytics**: Schedule it to autonomously summarize crypto/stock trends every hour.

---

## 📱 Quick Navigation
1. [Creating the Walkie-Talkie (Telegram Bot)](#-step-1-creating-your-walkie-talkie-telegram-bot)
2. [Choosing Where Your Robot Lives (PC, Cloud, or Termux)](#-step-3-where-will-your-robot-live-the-computer)
3. [The Ultimate Android Termux Guide (Zero to Hero)](#choice-c-an-android-phone-using-termux---the-complete-guide)
4. [Connecting the Brain (Ollama)](#-step-4-giving-omniclaw-the-brain-ollama)
5. [Starting the System](#-step-5-turning-on-the-robot-247-mode)
6. [Talk to Your Robot!](#-step-6-talk-to-your-robot)
7. [Mission Control (The Visual Dashboard)](#-step-7-mission-control-the-visual-dashboard)

---

## 🏗️ The Architecture: What Are We Building?

Imagine you are hiring a super-smart digital employee. 
- **The Brain**: This is the AI model (like Llama3 or GPT-4) that does the thinking and reasoning.
- **The Body**: This is OmniClaw running on a computer, doing the physical typing, clicking, parsing, and file reading.
- **The Walkie-Talkie**: This is Telegram (or Discord/Slack)! You will text your robot from your phone, and it texts you back.

---

## 📱 Step 1: Creating Your Walkie-Talkie (Telegram Bot)

We need to create the actual chat account for your robot on Telegram.

1. Open the **Telegram app** on your phone or computer.
2. In the search bar at the top, type exactly: `@BotFather`
3. Click the one with the blue checkmark ✅.
4. Type and send: `/newbot`
5. BotFather will ask for a **Name** (e.g., "My OmniClaw Bot"). Type it and send.
6. BotFather will ask for a **Username** (must end in `bot`, e.g., `SuperOmniClaw_bot`). Type it and send.
7. **BINGO!** BotFather will give you a long string of letters and numbers called a **Token** (it looks like `123456789:ABCdefGHIjklMNO`). 
8. **Copy this Token** and save it in a Notes app right now. You need it later.

---

## 🔐 Step 2: Getting Your Secret Telegram ID

If anyone finds your bot, you do NOT want them controlling your computer. We need to tell the robot to **only listen to YOU**.

1. In Telegram, search for `@userinfobot`. 
2. Send it `/start`.
3. It will reply with your personal "Id" (e.g., `Id: 987654321`).
4. **Copy this Number** and save it next to your Token.

---

## 💻 Step 3: Where Will Your Robot Live? (The Computer)

To run 24/7, the software needs a computer that never turns off. You have three choices. **Pick one.**

### Choice A: Your Own Computer (Free)
If you leave an old laptop or a Raspberry Pi plugged in and connected to WiFi 24/7, it can live there. 
*(Warning: If the laptop goes to sleep or loses WiFi, the robot stops working until it wakes up).*

### Choice B: A Cloud Computer (Best for 24/7 Business)
You can rent a computer in the cloud that stays on forever. It's called a **VPS** (Virtual Private Server). 
1. Go to **DigitalOcean**, **Hetzner**, or **Linode**.
2. Create an account.
3. Rent the cheapest "Ubuntu Linux" computer (usually $5 to $10 per month).
4. They will give you an **IP Address** and a password. You log into it using a terminal.

### Choice C: An Android Phone (Using Termux) - The Complete Guide
Why leave a PC running when an old Android phone uses 2 Watts of power? You can turn any Android device into a 24/7 AI Node. Here is exactly how to do it from scratch:

#### 1. Avoid the Play Store
1. Open Google Chrome on the Android phone.
2. Go to **f-droid.org** and download the F-Droid app store APK. Install it.
3. Open F-Droid, search for **Termux**, and install it. *(Do NOT use the Google Play Store version, it is permanently broken).*

#### 2. Termux Initial Setup
Open the Termux app on the phone. You will see a black terminal screen.
Type these exact commands, pressing Enter after each one:
```bash
# Give Termux permission to see your phone's files
termux-setup-storage
# Update all the internal tools (say 'y' to any prompts)
pkg update && pkg upgrade -y
```

#### 3. Enable Remote Access (SSH)
Typing complex code on a tiny phone screen is horrible. Let's cast it to your PC.
Type these into the phone:
```bash
# Install the SSH server software
pkg install openssh -y
# Set a password for your phone (you won't see the letters as you type, just push enter)
passwd
# Start the server
sshd
# Find your phone's IP address (look for the wlan0 section, it looks like 192.168.1.something)
ifconfig
# Find your username (it usually looks like u0_a123)
whoami
```
**Now, put the phone down.** Go to your Windows/Mac computer on the same WiFi. Open Command Prompt (Windows) or Terminal (Mac) and type:
`ssh -p 8022 your_username@192.168.1.something`
It will ask for your password. Boom! You are now controlling your phone from your PC keyboard!

#### 4. Install The Required Tools
Now that you are connected, paste this into the terminal to install everything OmniClaw needs:
```bash
pkg install git python rust binutils nodejs-lts -y
```

---

## 🧠 Step 4: Giving OmniClaw the Brain (Ollama)

OmniClaw needs an AI model to do the thinking. Ollama is the easiest way to run local AI completely offline for free.

**If you are on PC/Linux/VPS:**
Go to [Ollama.com](https://ollama.com) and click Download. 

**If you are on Android/Termux:**
Paste this into your Termux SSH window:
```bash
pkg install ollama -y
# Start the Ollama background brain (the & symbol keeps it running in the background)
ollama serve &
```

---

## ⚙️ Step 5: Turning On The Robot (24/7 Mode)

Now we push the big green button to turn it on! You can use the magical `setup.sh` script to do it all for you.

In your terminal (whether PC, Mac, VPS, or Termux SSH), just type:
```bash
# 1. Download the code
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw

# 2. Put in your Walkie-Talkie secrets
cp config.example.yaml config.yaml
nano config.yaml
```
*(In the file, find the `telegram` section. Paste your Token and your User ID that you saved from Step 1 and 2. Press `CTRL+X`, then `Y`, then `Enter` to save).*

```bash
# 3. Launch it!
chmod +x setup.sh
./setup.sh
```

### What happens when I hit enter?
- The script looks at how strong your computer is.
- If it's a weak computer/phone (< 6GB RAM), it downloads a tiny, lightning-fast brain (`gemma:1b`).
- If it's a strong computer (6GB+ RAM), it downloads a big brain (`llama3.1:8b`).
- It starts OmniClaw in the background and keeps it running!

---

## 💬 Step 6: Talk to Your Robot!

1. Open Telegram on your phone.
2. Search for the Username you made in Step 1 (e.g., `SuperOmniClaw_bot`).
3. Hit **START** and say "Hello!".
4. The robot should reply! Since you put your ID in the `allowed_users` list, it knows it's the boss.

### What can I ask it to do?
Try typing exactly this:
- `/task Look up the weather in New York and summarize it`
- `/task Write a simple python script in /tmp/ that prints the time`
- `/task Check my system memory usage`
- `/status`

### Running the Red Team Exploitation Suite 🛑
You can directly run the new automated vulnerability assessment module (includes Contextual Fuzzer, Adversarial Refiner, PoC Validator, and Disclosure Engine) via its orchestrator:
```bash
python orchestrator.py
```
*Note: Make sure Ollama is running (`ollama serve &`) and adjust the `config` within `orchestrator.py` to point to an authorized sandbox target.*

Congratulations! You now own an autonomous, 24/7 AI employee that lives in a computer or phone and takes orders from anywhere in the world! 🎉

---

## 🖥️ Step 7: Mission Control (The Visual Dashboard)

Want a beautiful cyberpunk command center to watch your AI Agents work in real-time? OmniClaw comes with a lightning-fast Native UI built on Tauri and React.

**If you installed OmniClaw on your PC / Mac:**
1. Make sure the OmniClaw daemon is running (`omniclaw-daemon`).
2. Navigate to the `mission-control` folder inside your `omniclaw` directory.
3. Run `npm run tauri dev` to launch the live dashboard (or `npm run tauri build` to generate a standalone executable app for your OS).
4. A beautiful native window will pop up showing live swarm metrics, live terminal outputs (stdout), and specialized Agent chat panels!

*(Note: If OmniClaw is running headlessly on a VPS or Termux phone, you primarily use the Telegram "Walkie Talkie". The Mission Control GUI is designed for local desktop monitoring).*

---

## ⚡ Performance Tips (V3.2 Sovereign Sentinel)

If you are running on Termux or a low-end VPS, use these tips to keep OmniClaw fast:
- **Git Bloat**: Ensure you are on V3.2+. Previous versions tracked `node_modules`, which slowed down the agent dramatically. Run `git pull origin main` to get the latest optimized `.gitignore`.
- **Memory Decay**: If the agent starts hallucinating after days of 24/7 run, say `/task clear temporal memory` to reset the FAISS index buffers.

---

## 🛠️ Troubleshooting & Common Fixes

### 1. `SyntaxError: unmatched ')'` or `create_git_hook` Errors
If you see a crash on startup mentioning `contract_enforcer.py`, you are on a buggy older version. 
**The Fix:** 
```bash
git pull origin main
```
This was fixed in the **Sovereign Sentinel (V3.2)** update.

### 2. "Too many active changes" in VS Code
If your Git icon shows 10k+ changes, your `.gitignore` is missing the `node_modules` exclusion.
**The Fix:** Update to V3.2 or manually add `node_modules/` to your `.gitignore` file.

### 3. "Port 8022" Connection Refused (Termux)
Ensure you ran `sshd` inside the Termux app on the phone first. If you reboot the phone, you must open Termux and type `sshd` again.

### 4. API Key Not Working (401 Unauthorized)
If your robot says it can't talk to the AI, check your `config.yaml`.
**The Fix:** Make sure there are no extra spaces in your API key and that your billing/credits are active on the provider's website (OpenAI, Anthropic, etc.).

### 5. Ollama "Connection Refused"
If you are using a local brain and it won't connect.
**The Fix:** Ensure Ollama is running. On PC, check the system tray icon. On Termux, run `ollama serve &` again.

### 6. Robot is "Sleeping" on Android
Android often kills background apps to save battery.
**The Fix:** Go to your phone's **Settings > Battery > Battery Optimization**. Find Termux and set it to **"Don't Optimize"**. Also, keep the Termux notification visible in your pull-down bar.

### 7. ModuleNotFoundError: No module named 'omniclaw_advanced_features'
If you are trying to use High-Power features and they aren't loading.
**The Fix:** Ensure you have the `core/advanced_features/` folder present. If missing, run `git pull origin main`.

### 8. Mission Control WebSocket Error
If the visual dashboard won't show live logs.
**The Fix:** Ensure OmniClaw is started with the `gui` or `daemon` mode. WebSocket logic is disabled in simple `chat` mode to save resources.

### 9. How to Read Logs (The Secret Weapon)
If your robot crashes and you don't know why, the answer is always in the logs.
**The Fix:** Type `tail -f logs/omniclaw.log` in your terminal. This will show you exactly what the robot is "thinking" and where it is getting stuck in real-time. Look for lines that say **"ERROR"** or **"CRITICAL"**.


---

### 🛑 Strict Legal Warning
**Using OmniClaw for automated hacking, network penetration, or malicious activity is strictly illegal and punishable by law. We do not encourage or endorse such actions. You use this AI tool entirely at your own risk and liability.**

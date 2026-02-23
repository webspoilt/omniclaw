# 🍼 The "Explain Like I'm 10" OmniClaw Guide

Welcome! If you want to build a super-smart robot assistant that you can text from your phone, and you want it to run **24 hours a day, 7 days a week** for your personal life or business—this guide is for you! 

We will go step-by-step. No confusing words. Just clear instructions.

---

## 🏗️ Step 1: Understanding What We Are Building

Imagine you are hiring a super-smart digital employee. 
- **The Brain**: This is the AI model (like Llama3 or GPT-4) that does the thinking.
- **The Body**: This is OmniClaw running on a computer, doing the physical typing, clicking, and file reading.
- **The Walkie-Talkie**: This is Telegram! You will text your robot from your phone, and it text you back.

## 📱 Step 2: Creating Your Walkie-Talkie (Telegram Bot)

We need to create the phone number (bot account) for your robot on Telegram.

1. Open the **Telegram app** on your phone or computer.
2. In the search bar at the top, type exactly: `@BotFather`
3. Click the one with the blue checkmark ✅.
4. Type and send: `/newbot`
5. BotFather will ask for a **Name** (e.g., "My OmniClaw Bot"). Type it and send.
6. BotFather will ask for a **Username** (must end in `bot`, e.g., `SuperOmniClaw_bot`). Type it and send.
7. **BINGO!** BotFather will give you a long string of letters and numbers called a **Token** (it looks like `123456789:ABCdefGHIjklMNO`). 
8. **Copy this Token** and save it somewhere safe. 

## 🔐 Step 3: Getting Your Secret Telegram ID

If anyone finds your bot, you do NOT want them controlling your computer. We need to tell the robot to **only listen to YOU**.

1. In Telegram, search for `@userinfobot`. 
2. Send it `/start`.
3. It will reply with your personal "Id" (e.g., `Id: 987654321`).
4. **Copy this Number**.

## 💻 Step 4: Where Will Your Robot Live? (The Computer)

To run 24/7, the software needs a computer that never turns off. You have two choices:

### Choice A: Your Own Computer (Free, but must stay on)
If you leave an old laptop or a Raspberry Pi plugged in and connected to WiFi 24/7, it can live there. 
*(Warning: If the laptop goes to sleep or loses WiFi, the robot stops working until it wakes up).*

### Choice B: A Cloud Computer (Best for 24/7 Business)
You can rent a computer in the cloud that stays on forever. It's called a **VPS** (Virtual Private Server). 
1. Go to **DigitalOcean**, **Hetzner**, or **Linode**.
2. Create an account.
3. Rent the cheapest "Ubuntu Linux" computer (usually $5 to $10 per month).
4. They will give you an **IP Address** and a password. You log into it using a terminal.

## ⚙️ Step 5: Giving OmniClaw Your Secrets

Now that you have your computer ready (Choice A or Choice B), let's put OmniClaw on it and give it the Walkie-Talkie secrets.

1. Open your computer's terminal and type:
   ```bash
   git clone https://github.com/webspoilt/omniclaw.git
   cd omniclaw
   ```

2. Open the `config.yaml` file. If it doesn't exist, copy it:
   ```bash
   cp config.example.yaml config.yaml
   nano config.yaml
   ```

3. Look for the `messaging` part and put your Token and ID exactly like this:
   ```yaml
   messaging:
     telegram:
       enabled: true
       token: "PASTE_YOUR_BOTFATHER_TOKEN_HERE"
       allowed_users: ["PASTE_YOUR_USERINFOBOT_ID_HERE"]
   ```
4. Save the file!

## 🚀 Step 6: Turning On The Robot (24/7 Mode)

Now we push the big green button to turn it on! You can use the magical `setup.sh` script to do it all for you.

In your terminal, just type:
```bash
chmod +x setup.sh
./setup.sh
```

### What happens when I hit enter?
- The script looks at how strong your computer is.
- If it's a weak computer (< 6GB RAM), it downloads a tiny brain (`gemma:1b`).
- If it's a strong computer (6GB+ RAM), it downloads a big brain (`llama3.1:8b`).
- It installs all the required programs.
- It starts OmniClaw in the background and keeps it running!

## 💬 Step 7: Talk to Your Robot!

1. Open Telegram on your phone.
2. Search for the Username you made in Step 2.
3. Hit **START** and say "Hello!".
4. The robot should reply! Since you put your ID in the `allowed_users` list, it knows it's the boss.

### What can I ask it to do?
Try typing exactly this:
- `/task Look up the weather in New York and summarize it`
- `/task Create a simple Python script for a calculator`
- `/status`

Congratulations! You now own an autonomous, 24/7 AI employee that lives in a computer and takes orders from your phone! 🎉

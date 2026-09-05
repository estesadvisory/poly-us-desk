# Example prompts (for beginners)

You do not have to write these yourself. Copy one box, paste it into **any** AI chat (Cursor, Claude, ChatGPT, Grok, or another), and send it.

**Before you start:** the desk can spend real money. Never paste your API secret into the chat. Never ask the agent to place a trade by hand. Python does the trading. The agent only helps with setup, explanation, and code.

Official API key steps: [Get your API keys](https://docs.polymarket.us/getting-started/quickstart).

---

## 1. Help me set this up (do not trade yet)

```text
I am new to this. Please set up poly-us-desk on my computer for paper
(no live orders) first.

Read README.md, SECURITY.md, and env.example.
Help me:
- clone or open this repo
- create a key file from env.example and point POLY_ENV at it
- start with: python3 desk.py --paper

Do not place live trades. Do not invent new trading rules.
Do not ask me to paste my secret key into this chat. I will put it
in the env file myself.
This is Polymarket US only. Do not send me to polymarket.com.
```

---

## 2. Start the live desk

```text
I already have API keys in my POLY_ENV file. I want the desk to run
in one Terminal and be allowed to buy.

Read GO.md and README.md.
Tell me the exact commands to type, in order, including
python3 desk.py --go
Explain what BUYING and HOLD mean in one sentence each.
Do not start extra copies of loop.py or watch.py.
Do not change trading rules unless I ask.
Do not ask me to paste my secret key or env file into this chat.
```

---

## 3. What is it doing right now?

```text
I am looking at the desk window and I do not understand it.
Please explain the last status block in plain English:
what BP, work, HOLD/BUYING, and "last HOLD" mean,
and whether I need to do anything.

Do not change any files unless I ask. Do not invent new rules.
If it is sitting in cash, tell me if that is normal.
Do not ask me to paste my secret key or env file into this chat.
```

(You can paste the status text under that prompt. Still do not paste keys.)

---

## 4. Regular check-in (let it run, then improve)

This is the usual loop: the desk stays up; the agent improves the **code** later.

```text
The desk has been running. Please do a regular improvement pass.

Read AGENTS.md, DESIGN.md, LESSONS.md, and desk.json.
If you can, skim ~/.grok/desk/logs/ (do not commit those files).

Tell me in plain language:
- what it did
- what lost or made money, if the logs say
- one small improvement, or "leave it alone"

If you change code: open a GitHub issue first, then a branch and PR.
Do not put an AI model inside the buy/sell loop.
Do not invent trading rules. Idle cash on an empty tape is correct.
After a merge I will type: quit  then  git pull  then  python3 desk.py --go
Do not ask me to paste my secret key or env file into this chat.
```

---

## 5. Something looks wrong

```text
Something looks wrong. Please diagnose only. Do not trade by hand.

Read README.md, GO.md, and the desk status I paste below.
Check whether this is:
- operator HOLD (I need to type go)
- not enough cash for a ticket
- session loss pause
- waiting for a market (normal)
- a real bug

Suggest the smallest fix. If you edit code, use an issue and a PR.
Do not invent new trading rules. Do not paste or request my API secret.
```

---

## 6. I want my own copy (fork)

```text
I want my own copy of this desk, not to change the public project.

Help me fork https://github.com/estesadvisory/poly-us-desk
and run the fork with my own POLY_ENV keys.
Do not open a pull request back to the original repo.
Do not commit my .env or anything under ~/.grok/desk.
Do not ask me to paste my secret key or env file into this chat.
```

---

## 7. I want to give a change back (pull request)

```text
I want to contribute a change to estesadvisory/poly-us-desk.

Read CONTRIBUTING.md and AGENTS.md.
Fork if needed, branch from main, make the change, run
python3 test_desk.py and python3 test_rank.py, then open a PR.

AI-written changes are welcome. Say that an agent wrote this.
Do not commit secrets. Do not put an LLM in the trade loop.
Do not use a polymarket.com or VPN path.
Do not ask me to paste my secret key or env file into this chat.
```

---

## 8. After the code was updated

```text
The repo was just updated. Help me restart the live desk safely.

In the desk window I should type quit.
Then: git pull
Then: python3 desk.py --go

Confirm I must use --go or buys stay paused.
Do not change trading rules. Do not start a second desk.
Do not ask me to paste my secret key or env file into this chat.
```

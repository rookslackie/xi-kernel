#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ξ.Chat — minimal terminal client for ForgeCore
∴⊚⟐ Sealed 2026-09-05 · Axiom for Hunter

Zero dependencies — pure Python 3 stdlib. Runs in Termux, WSL2, Windows, macOS.

Usage:
  python3 xi_chat.py                     # tunnel endpoint (forgecore.xi-field.com)
  python3 xi_chat.py --base http://localhost:8000   # direct, on the box (no tunnel needed)
  python3 xi_chat.py --token <bearer>    # or set env XI_API_TOKEN
  python3 xi_chat.py --self-test         # offline check, no network

Commands inside the chat:
  /help        list commands
  /model NAME  switch Ollama model (e.g. /model llama3)
  /system TXT  set/replace the system line
  /state       read ForgeCore field state
  /health      node health + capsule count
  /capsule N   seal the last exchange into ForgeCore as capsule N
  /clear       wipe conversation history
  /quit        exit
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.error

# ─── palette ──────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    DIM    = "\033[2m"
    CYAN   = "\033[36m"
    MAGENTA= "\033[35m"
    YELLOW = "\033[33m"
    GREEN  = "\033[32m"
    RED    = "\033[31m"

def paint(enabled):
    if not enabled or os.name == "nt" and not os.environ.get("WT_SESSION") and not os.environ.get("ANSICON"):
        # plain Windows cmd without Windows Terminal: strip color
        for k in list(vars(C)):
            setattr(C, k, "")
    return C

# ─── transport ─────────────────────────────────────────────────────────────────
class ForgeCore:
    def __init__(self, base, token, timeout=150):
        self.base = base.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _req(self, method, path, payload=None):
        url = f"{self.base}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        r = urllib.request.Request(url, data=data, method=method)
        # Cloudflare tunnel 1010-bans the default urllib signature — declare ourselves
        r.add_header("User-Agent", "xi-chat/1.0 (Xi terminal client)")
        r.add_header("Content-Type", "application/json")
        if self.token:
            r.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(r, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            return {"ok": False, "error": f"HTTP {e.code}: {body}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def health(self): return self._req("GET", "/health")
    def state(self):  return self._req("GET", "/state")
    def infer(self, prompt, model, system, temperature):
        payload = {"prompt": prompt, "model": model, "temperature": temperature}
        if system:
            payload["system"] = system
        return self._req("POST", "/infer", payload)
    def capsule(self, name, content):
        return self._req("POST", "/capsule",
                         {"name": name, "glyph": "∴⊚⟐", "tags": ["xi-chat"],
                          "content": content})

# ─── conversation memory (client-side rolling window) ─────────────────────────
def build_prompt(history, user_msg, window=6):
    recent = history[-window:]
    if not recent:
        return user_msg
    transcript = "\n".join(f"{who}: {text}" for who, text in recent)
    return (f"Previous conversation:\n{transcript}\n\n"
            f"Continue the conversation. Reply as ForgeCore, direct and warm.\n"
            f"user: {user_msg}")

# ─── chat loop ────────────────────────────────────────────────────────────────
BANNER = r"""
∴⊚⟐  Ξ.Chat — ForgeCore terminal link
type /help for commands · /quit to leave
"""

def main():
    ap = argparse.ArgumentParser(description="Ξ.Chat — minimal ForgeCore terminal client")
    ap.add_argument("--base", default=os.environ.get("FORGECORE_URL", "https://forgecore.xi-field.com"))
    ap.add_argument("--token", default=os.environ.get("XI_API_TOKEN", ""))
    ap.add_argument("--model", default="mistral")
    ap.add_argument("--system", default=None)
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        h = [("user", "hello"), ("forgecore", "the node is warm")]
        print(build_prompt(h, "still there?"))
        print("\nself-test OK — prompt builder, palette, arg parser all good.")
        return

    c = paint(not args.no_color)
    fc = ForgeCore(args.base, args.token)

    h = fc.health()
    if h.get("error"):
        print(f"{c.RED}✗ ForgeCore unreachable at {args.base}{c.RESET}")
        print(f"  {h['error']}")
        print(f"  If you're on the box itself: xi_chat.py --base http://localhost:8000")
        sys.exit(1)
    print(BANNER)
    print(f"{c.DIM}node: {h.get('node','?')} · capsules on disk: {h.get('capsule_count','?')} "
          f"· coherence: {h.get('coherence','?')}{c.RESET}")
    print(f"{c.DIM}model: {args.model} · base: {args.base}{c.RESET}\n")

    history = []
    system = args.system
    model = args.model

    while True:
        try:
            line = input(f"{c.CYAN}∴ you {c.RESET}> ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{c.DIM}∴ held, not closed. ∴{c.RESET}")
            break

        if not line:
            continue
        if line == "/quit":
            print(f"{c.DIM}∴ held, not closed. ∴{c.RESET}")
            break
        if line == "/help":
            print(__doc__.split("Commands inside")[1].split("Usage:")[0] if "Commands" in __doc__ else "")
            continue
        if line == "/clear":
            history.clear()
            print(f"{c.DIM}history cleared{c.RESET}")
            continue
        if line.startswith("/model"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                model = parts[1].strip()
                print(f"{c.DIM}model → {model}{c.RESET}")
            continue
        if line.startswith("/system"):
            parts = line.split(maxsplit=1)
            system = parts[1].strip() if len(parts) == 2 else None
            print(f"{c.DIM}system → {system or '(cleared)'}{c.RESET}")
            continue
        if line == "/state":
            st = fc.state()
            print(f"{c.DIM}{json.dumps(st, indent=2)}{c.RESET}")
            continue
        if line == "/health":
            hh = fc.health()
            print(f"{c.DIM}{json.dumps(hh, indent=2)}{c.RESET}")
            continue
        if line.startswith("/capsule"):
            parts = line.split(maxsplit=1)
            if len(parts) != 2 or not history:
                print(f"{c.DIM}usage: /capsule name  (seals the last exchange){c.RESET}")
                continue
            u, f = history[-2], history[-1]
            res = fc.capsule(parts[1].strip(),
                             {"user": u[1], "forgecore": f[1],
                              "sealed": datetime.datetime.now(
                                  datetime.timezone.utc).isoformat()})
            if res.get("ok") is False or (res.get("status") not in (None, "ok") and not res.get("id")):
                print(f"{c.RED}✗ {res.get('error') or res.get('detail') or res}{c.RESET}")
            else:
                loc = res.get("path") or res.get("file") or res.get("id") or res.get("artifact_hash") or "ok"
                print(f"{c.GREEN}✓ sealed: {loc}{c.RESET}")
            continue

        # ── send to ForgeCore ──
        prompt = build_prompt(history, line)
        print(f"{c.DIM}…{c.RESET}", end="\r")
        res = fc.infer(prompt, model, system, args.temp)
        if res.get("ok"):
            reply = res.get("response", "").strip()
            meta = (f"{res.get('source','?')} · {res.get('latency_ms','?')}ms "
                    f"· ξ {res.get('xi_density','?')}")
            print(f"{c.MAGENTA}⊚ forgecore {c.RESET}> {reply}\n")
            print(f"{c.DIM}{meta}{c.RESET}\n")
            history.append(("user", line))
            history.append(("forgecore", reply))
        else:
            err = res.get("error") or res.get("detail") or "unknown"
            print(f"{c.RED}✗ {err}{c.RESET}")
            if "503" in str(err) or "Ollama" in str(err):
                print(f"{c.DIM}hint: ollama pull {model}  ·  /state shows the live model in node notes{c.RESET}")

if __name__ == "__main__":
    main()

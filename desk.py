#!/usr/bin/env python3
"""v16 terminal supervisor. Zero LLM. Code in this repo; state in ~/.grok/desk.

  python3 desk.py --go         # research + seller + buys (use after a version bump)
  python3 desk.py              # buys HOLD until you type go
  python3 desk.py --no-buy     # research + seller only
  python3 desk.py --paper      # no live orders

Commands (same terminal): help status hold go reload skip <slug> books quit

Iteration: hold → edit this repo → reload  (or quit, then run again).
Logs: ~/.grok/desk/logs/desk.log  events.jsonl  research.log  loop.log  watch.log
"""
from __future__ import annotations
import argparse, json, os, select, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
import risk

ROLES = ("research", "loop", "watch")
CMDS = ("help", "status", "hold", "go", "reload", "skip", "books", "quit")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_cmd(line: str):
    parts = (line or "").strip().split()
    if not parts:
        return None
    cmd = parts[0].lower()
    if cmd not in CMDS:
        return None
    if cmd == "skip":
        return (cmd, parts[1] if len(parts) > 1 else None)
    return (cmd, None)


def event(role: str, kind: str, **extra) -> None:
    paths.ensure_desk()
    rec = {"ts": now_iso(), "role": role, "event": kind, **extra}
    try:
        with paths.EVENTS.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass
    try:
        with (paths.LOGS / "desk.log").open("a") as f:
            extra_s = " ".join(f"{k}={v}" for k, v in extra.items() if v is not None)
            f.write(f"{rec['ts']} {role} {kind} {extra_s}\n".rstrip() + "\n")
    except Exception:
        pass


def py() -> str:
    return sys.executable or "python3"


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def set_hold(on: bool) -> None:
    paths.ensure_desk()
    if on:
        paths.HOLD.write_text(now_iso() + "\n")
    elif paths.HOLD.exists():
        paths.HOLD.unlink()


def held() -> bool:
    return paths.HOLD.exists()


def skip_add(slug: str) -> None:
    p = paths.DESK / "skip_slugs.txt"
    paths.ensure_desk()
    have = p.read_text() if p.exists() else ""
    if slug and slug not in have.split():
        with p.open("a") as f:
            f.write(slug + "\n")


class Child:
    def __init__(self, name: str, args: list[str], env: dict):
        self.name = name
        self.args = args
        self.env = env
        self.proc: subprocess.Popen | None = None
        self.log = paths.LOGS / f"{name}.log"

    def start(self) -> None:
        paths.ensure_desk()
        self.log.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.log, "a")
        self.proc = subprocess.Popen(
            self.args,
            cwd=str(paths.REPO),
            env=self.env,
            stdout=fh,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        fh.close()
        event("supervisor", "start", child=self.name, pid=self.proc.pid)
        print(f"started {self.name} pid={self.proc.pid} log={self.log}", flush=True)

    def poll(self) -> int | None:
        if not self.proc:
            return None
        return self.proc.poll()

    def running(self) -> bool:
        return self.proc is not None and self.poll() is None and _alive(self.proc.pid)

    def stop(self) -> None:
        if not self.proc or self.poll() is not None:
            self.proc = None
            return
        pid = self.proc.pid
        try:
            os.killpg(pid, 15)
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass
        for _ in range(20):
            if self.poll() is not None:
                break
            time.sleep(0.1)
        if self.poll() is None:
            try:
                os.killpg(pid, 9)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        event("supervisor", "stop", child=self.name, pid=pid)
        self.proc = None


def child_env(paper: bool) -> dict:
    env = os.environ.copy()
    env["POLY_DESK"] = str(paths.DESK)
    env["POLY_ENV"] = str(paths.ENVP)
    if paper:
        env["POLY_PAPER"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def research_loop() -> None:
    """Child role: keep the tape fresh. Full scan when stale, else --hot."""
    import lock as desklock

    desklock.claim("research")
    print(
        json.dumps(
            {
                "ok": True,
                "role": "research",
                "version": risk.VERSION,
                "rev": paths.code_rev(),
                "pid": os.getpid(),
            }
        ),
        flush=True,
    )
    while True:
        tape = paths.DESK / "tape.json"
        age = 1e9
        if tape.exists():
            try:
                t = json.loads(tape.read_text())
                asof = t.get("full_asof") or t.get("asof") or ""
                ts = datetime.fromisoformat(asof.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - ts).total_seconds()
            except Exception:
                age = 1e9
        args = [py(), str(paths.REPO / "research.py")]
        if 0 <= age < risk.HOT_MAX_AGE_SEC:
            args.append("--hot")
        try:
            subprocess.run(args, cwd=str(paths.REPO), timeout=90)
        except Exception as ex:
            print(json.dumps({"ok": False, "role": "research", "err": type(ex).__name__}), flush=True)
        time.sleep(risk.OPEN_SCAN_SEC if age < 60 else risk.IDLE_SCAN_SEC)


def load_json(name: str):
    p = paths.DESK / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def hud() -> str:
    books = load_json("books.json") or {}
    intent = load_json("intent.json") or {}
    tape = load_json("tape.json") or {}
    bp = books.get("buyingPower")
    work = books.get("working")
    opens = books.get("open") or []
    live_n = len(tape.get("live") or [])
    soon_n = len(tape.get("soon") or [])
    later_n = len(tape.get("later") or [])
    action = intent.get("action") or "?"
    reason = (intent.get("reason") or "")[:100]
    nxt = intent.get("next")
    nxt_m = intent.get("next_min")
    why = intent.get("why") or []
    lines = [
        f"{risk.VERSION}  {paths.code_rev()}  {now_iso()}  {'HOLD' if held() else 'BUYING'}  paper={paths.PAPER}  max_open={risk.MAX_OPEN}",
        f"BP {bp}  work {work}  ring {risk.RING_USD}  open {len(opens)}/{risk.MAX_OPEN}  live {live_n} soon {soon_n} later {later_n}",
        f"last {action}  {reason}",
    ]
    if nxt:
        lines.append(f"next {nxt} in {nxt_m}m")
    if why:
        lines.append("why " + "; ".join(str(x) for x in why[:4]))
    for o in opens:
        lines.append(
            f"  {o.get('slug')} qty {o.get('qty')} avg {o.get('avg')} bid {o.get('bid')} d {o.get('delta_c')}"
        )
    return "\n".join(lines)


def print_help() -> None:
    print(
        "commands: help status hold go reload skip <slug> books quit\n"
        "hold = pause new buys (seller stays up)\n"
        "go = resume buys\n"
        "reload = restart children after you edit this repo (HOLD/go stays as-is)\n"
        "quit = stop everything. Next start: python3 desk.py --go  if you want buys",
        flush=True,
    )


class Supervisor:
    def __init__(self, no_buy: bool, paper: bool, start_go: bool):
        self.no_buy = no_buy
        self.paper = paper
        self.env = child_env(paper)
        self.children: dict[str, Child] = {}
        set_hold(not start_go)
        self._build_children()

    def _build_children(self) -> None:
        exe = py()
        self.children = {
            "research": Child("research", [exe, str(paths.REPO / "desk.py"), "--role", "research"], self.env),
            "watch": Child("watch", [exe, str(paths.REPO / "watch.py")], self.env),
        }
        if not self.no_buy:
            self.children["loop"] = Child("loop", [exe, str(paths.REPO / "loop.py")], self.env)

    def _stop_pidfile(self, name: str) -> None:
        pidf = paths.DESK / f"{name}.pid"
        if not pidf.exists():
            return
        try:
            old = int(pidf.read_text().strip() or "0")
        except ValueError:
            old = 0
        if old and old != os.getpid() and _alive(old):
            event("supervisor", "reap_stale", child=name, pid=old)
            try:
                os.killpg(old, 15)
            except Exception:
                try:
                    os.kill(old, 15)
                except Exception:
                    pass
            time.sleep(0.3)
            if _alive(old):
                try:
                    os.kill(old, 9)
                except Exception:
                    pass
        try:
            pidf.unlink()
        except Exception:
            pass

    def start_all(self) -> None:
        paths.ensure_desk()
        for name in ROLES:
            self._stop_pidfile(name)
        sess = paths.DESK / "session.json"
        try:
            sess.unlink()
        except Exception:
            pass
        (paths.DESK / "supervisor.pid").write_text(str(os.getpid()) + "\n")
        event(
            "supervisor",
            "boot",
            version=risk.VERSION,
            rev=paths.code_rev(),
            max_open=risk.MAX_OPEN,
            soon_min=risk.SOON_MIN,
            paper=self.paper,
            no_buy=self.no_buy,
            hold=held(),
        )
        for ch in self.children.values():
            ch.start()

    def stop_all(self) -> None:
        for ch in self.children.values():
            ch.stop()
        pidf = paths.DESK / "supervisor.pid"
        try:
            if pidf.exists() and pidf.read_text().strip() == str(os.getpid()):
                pidf.unlink()
        except Exception:
            pass
        event("supervisor", "shutdown")

    def reap_and_restart(self) -> None:
        for ch in self.children.values():
            code = ch.poll()
            if ch.proc is not None and code is not None:
                event("supervisor", "child_exit", child=ch.name, code=code)
                print(f"{ch.name} exited {code} — restarting", flush=True)
                ch.start()

    def reload(self) -> None:
        print("reload: stopping children, then starting with this repo", flush=True)
        for ch in self.children.values():
            ch.stop()
        time.sleep(0.4)
        self._build_children()
        for ch in self.children.values():
            ch.start()
        event("supervisor", "reload", version=risk.VERSION, rev=paths.code_rev(), max_open=risk.MAX_OPEN)
        # session.json kept — same GO, same −$2 circuit
        if held():
            print("reload done. buys still HOLD — type go", flush=True)

    def handle(self, parsed) -> bool:
        """Return False to quit."""
        cmd, arg = parsed
        event("supervisor", "cmd", cmd=cmd, arg=arg)
        if cmd == "help":
            print_help()
        elif cmd == "status":
            print(hud(), flush=True)
            for name, ch in self.children.items():
                print(f"  {name}: {'up' if ch.running() else 'DOWN'}", flush=True)
        elif cmd == "hold":
            set_hold(True)
            print("buys paused (HOLD). seller still running.", flush=True)
        elif cmd == "go":
            set_hold(False)
            print("buys armed.", flush=True)
        elif cmd == "reload":
            self.reload()
        elif cmd == "skip":
            if not arg:
                print("usage: skip <slug>", flush=True)
            else:
                skip_add(arg)
                print(f"skip {arg}", flush=True)
        elif cmd == "books":
            try:
                subprocess.run([py(), str(paths.REPO / "trade.py"), "books"], cwd=str(paths.REPO), env=self.env, timeout=30)
            except Exception as ex:
                print(f"books failed {type(ex).__name__}", flush=True)
        elif cmd == "quit":
            return False
        return True

    def run(self) -> None:
        self.start_all()
        print_help()
        print(hud(), flush=True)
        print(">", end=" ", flush=True)
        last_hud = 0.0
        try:
            while True:
                self.reap_and_restart()
                r, _, _ = select.select([sys.stdin], [], [], 1.0)
                if r:
                    line = sys.stdin.readline()
                    if line == "":
                        break
                    parsed = parse_cmd(line)
                    if parsed is None:
                        if line.strip():
                            print("unknown. type help", flush=True)
                    elif not self.handle(parsed):
                        break
                    print(">", end=" ", flush=True)
                now = time.time()
                if now - last_hud >= 15:
                    print("\n" + hud(), flush=True)
                    print(">", end=" ", flush=True)
                    last_hud = now
        except KeyboardInterrupt:
            print("\ninterrupt — stopping", flush=True)
        finally:
            self.stop_all()
            print("stopped.", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="v16 Polymarket US desk (terminal, no LLM)")
    ap.add_argument("--role", choices=["supervisor", "research"], default="supervisor")
    ap.add_argument("--no-buy", action="store_true", help="research + seller only")
    ap.add_argument("--paper", action="store_true", help="no live orders")
    ap.add_argument("--go", action="store_true", help="arm buys on start (default is HOLD)")
    args = ap.parse_args()
    if args.paper:
        os.environ["POLY_PAPER"] = "1"
        paths.PAPER = True  # type: ignore[misc]
    if args.role == "research":
        research_loop()
        return
    Supervisor(no_buy=args.no_buy, paper=args.paper or paths.PAPER, start_go=args.go).run()


if __name__ == "__main__":
    main()

"""Start, check and stop the bridge process — POSIX and Windows, no shell.

``ensure`` is the command every deliverable calls: it pings first and only
starts a detached process when nothing answers. Detaching matters because the
bridge has to outlive the agent session that started it.
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import config


def ping(poort=None, timeout=2.0):
    """Answer of GET /ping as a dict, or None when nothing is listening."""
    url = config.base_url(poort) + "/ping"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def wait_for(poort=None, seconds=5.0):
    deadline = time.time() + seconds
    while time.time() < deadline:
        info = ping(poort, timeout=1.0)
        if info:
            return info
        time.sleep(0.2)
    return None


def read_pid(poort=None):
    for pad in (config.pid_file(poort), config.legacy_pid_file()):
        try:
            return int(pad.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            continue
    return None


def _drop_pid(poort=None):
    for pad in (config.pid_file(poort), config.legacy_pid_file()):
        try:
            pad.unlink()
        except OSError:
            pass


def pid_alive(pid):
    if not pid:
        return False
    if os.name == "nt":
        uit = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                             capture_output=True, text=True)
        return str(pid) in (uit.stdout or "")
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _spawn(poort=None):
    """Start the bridge detached from this process and this terminal."""
    state = config.state_dir()
    state.mkdir(parents=True, exist_ok=True)
    log = config.log_file().open("ab")
    env = os.environ.copy()
    # `-m html_annotator` must resolve wherever the child is started from.
    pad = str(config.SKILL_DIR)
    env["PYTHONPATH"] = pad + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if poort:
        env["HTML_ANNOTATOR_PORT"] = str(poort)
    cmd = [config.python_exe(), "-m", "html_annotator", "serve"]
    kwargs = {"stdout": log, "stderr": log, "stdin": subprocess.DEVNULL,
              "cwd": pad, "env": env, "close_fds": True}
    if os.name == "nt":
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | getattr(subprocess, "DETACHED_PROCESS", 0x00000008))
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    config.pid_file(poort).write_text(str(proc.pid), encoding="utf-8")
    return proc.pid


def ensure(poort=None, seconds=5.0):
    """Idempotent: returns (status, message). status in already/started/failed."""
    poort = poort or config.port()
    if ping(poort):
        return "already", "bridge already running on %s" % config.base_url(poort)
    pid = read_pid(poort)
    if pid and not pid_alive(pid):
        _drop_pid(poort)
    pid = _spawn(poort)
    if wait_for(poort, seconds):
        return "started", "bridge started on %s (pid %d, log %s)" % (
            config.base_url(poort), pid, config.log_file())
    staart = ""
    try:
        staart = "\n".join(config.log_file().read_text(
            encoding="utf-8", errors="replace").splitlines()[-15:])
    except OSError:
        pass
    return "failed", "bridge did not answer within %ss. Last log lines:\n%s" % (seconds, staart)


def stop(poort=None):
    """Stop the bridge started by ensure. Returns (ok, message)."""
    poort = poort or config.port()
    pid = read_pid(poort)
    if not pid:
        if ping(poort):
            return False, ("something answers on %s but no pid file (%s) — "
                           "stop it yourself" % (config.base_url(poort), config.pid_file(poort)))
        return True, "no bridge to stop"
    if not pid_alive(pid):
        _drop_pid(poort)
        return True, "no running bridge (stale pid %d removed)" % pid
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    else:
        import signal
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    for _ in range(25):
        if not pid_alive(pid):
            break
        time.sleep(0.2)
    _drop_pid(poort)
    if pid_alive(pid):
        return False, "pid %d is still alive" % pid
    return True, "bridge stopped (pid %d)" % pid


def serve():
    from . import bridge
    bridge.main()
    return 0


def url_for(pad):
    """http://127.0.0.1:<port>/p/<path-from-home> for a local file."""
    doel = Path(os.path.expanduser(str(pad))).resolve()
    home = Path.home().resolve()
    try:
        rel = doel.relative_to(home)
    except ValueError:
        raise ValueError("path outside the home directory, the bridge refuses it: %s" % doel)
    return config.base_url() + "/p/" + "/".join(rel.parts)


def resolve(target, nrs=(), ids=(), poort=None, resolved=True):
    """POST /resolve for a slug or an annotations.json path."""
    payload = {"resolved": bool(resolved)}
    if nrs:
        payload["nrs"] = [int(n) for n in nrs]
    if ids:
        payload["ids"] = [str(i) for i in ids]
    tekst = str(target)
    if tekst.endswith(".json") or os.path.sep in tekst or "/" in tekst:
        payload["jsonPath"] = os.path.expanduser(tekst)
    else:
        payload["slug"] = tekst
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(config.base_url(poort) + "/resolve", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8") or "{}")

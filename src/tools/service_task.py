# -*- coding: utf-8 -*-
"""把知识库服务注册成 Windows 计划任务：登录即启动、崩溃自动重启、不占窗口。

生成的 XML 带：
  · 没有触发器 —— 只在你手动启动时运行，重启电脑后不会自己起
  · RestartOnFailure    运行中进程挂了，1 分钟后自动重试，最多 3 次
  · ExecutionTimeLimit=PT0S  不限运行时长（默认 3 天会被结束）
  · 电池上也运行

用法：
    .venv\\Scripts\\python.exe src\\tools\\service_task.py install          # 服务任务
    .venv\\Scripts\\python.exe src\\tools\\service_task.py install-backup   # 每日备份任务
    .venv\\Scripts\\python.exe src\\tools\\service_task.py start|stop|status|uninstall
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]              # src/
PROJECT = ROOT.parent
TASK = "RAG-KnowledgeBase"
BACKUP_TASK = "RAG-KnowledgeBackup"
PORT = 8000
LOG = PROJECT / "server.log"

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>RAG 知识库网页服务（手动启动；运行中崩溃会自动重启）</Description>
    <Author>{user}</Author>
  </RegistrationInfo>
  <Triggers />

  <Principals>
    <Principal id="Author">
      <UserId>{sid}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""

BACKUP_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>每天凌晨备份 RAG 知识库的 data 与 config</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T02:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{sid}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <Arguments>src\\tools\\backup.py --keep 10</Arguments>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def ps(cmd: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def current_sid() -> str:
    return ps("([Security.Principal.WindowsIdentity]::GetCurrent()).User.Value") or ""


def port_open() -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def http_ok() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/stats", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def task_exists(name: str = TASK) -> bool:
    return name in ps(f'schtasks /Query /TN "{name}" 2>$null')


def register(xml: str, name: str) -> bool:
    tmp = PROJECT / f"_{name}.xml"
    tmp.write_text(xml, encoding="utf-16")
    out = ps(f'schtasks /Create /TN "{name}" /XML "{tmp}" /F')
    tmp.unlink(missing_ok=True)
    ok = task_exists(name)
    print(f"  {'✅' if ok else '❌'} {name} 注册{'成功' if ok else '失败'}")
    if not ok and out:
        print("   ", out[:300])
    return ok


def install() -> int:
    sid = current_sid()
    if not sid:
        print("❌ 取不到当前用户 SID")
        return 1
    xml = XML_TEMPLATE.format(
        user=os.environ.get("USERNAME", "user"), sid=sid,
        command=str(ROOT / "tools" / "run_service.bat"), workdir=str(PROJECT))
    print("[注册] 服务任务（手动启动 + 运行中崩溃自动重启 + 不限时长）")
    return 0 if register(xml, TASK) else 1


def install_backup() -> int:
    sid = current_sid()
    py = PROJECT / ".venv" / "Scripts" / "python.exe"
    xml = BACKUP_XML.format(sid=sid, command=str(py), workdir=str(PROJECT))
    print("[注册] 每日备份任务（凌晨 02:00，保留 10 份）")
    return 0 if register(xml, BACKUP_TASK) else 1


def start() -> int:
    if http_ok():
        print(f"[已在运行] http://127.0.0.1:{PORT}/")
        return 0
    if not task_exists():
        print("[提示] 任务还不存在，先注册")
        if install() != 0:
            return 1
    ps(f'schtasks /Run /TN "{TASK}"')
    print(f"[启动] 已触发任务「{TASK}」，等待就绪…")
    for _ in range(40):
        time.sleep(0.75)
        if http_ok():
            print(f"[就绪] http://127.0.0.1:{PORT}/")
            return 0
    print(f"[警告] 30 秒内没就绪，看日志：{LOG}")
    return 1


def stop() -> int:
    ps(f'schtasks /End /TN "{TASK}"')
    ps(f'Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue '
       f'| ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}')
    time.sleep(1)
    ensure = ROOT / "tools" / "ensure_ollama.py"
    if ensure.exists():
        subprocess.run([sys.executable, str(ensure), "--stop"], capture_output=True)
    print("[已停止] 知识库服务（含本地模型）" if not port_open() else "[警告] 端口仍被占用")
    return 0


def status() -> int:
    import json

    running = http_ok()
    print(f"服务地址 : http://127.0.0.1:{PORT}/")
    print(f"运行状态 : {'✅ 正常响应' if running else '❌ 没有响应'}")
    print(f"服务任务 : {'已注册（手动启动·崩溃重启）' if task_exists() else '未注册'}")
    print(f"备份任务 : {'已注册（每天 02:00）' if task_exists(BACKUP_TASK) else '未注册'}")
    if running:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/stats", timeout=3) as r:
                d = json.loads(r.read().decode("utf-8"))
                print(f"索引     : {d['count']} 块 / {len(d['files'])} 文件")
                print(f"对话模型 : {d.get('llm') or '未配置'}")
        except Exception:
            pass
    bdir = PROJECT / "backups"
    backups = sorted(bdir.glob("ragkb-*.zip")) if bdir.exists() else []
    if backups:
        latest = max(backups, key=lambda p: p.stat().st_mtime)
        print(f"最近备份 : {latest.name}（共 {len(backups)} 份）")
    return 0 if running else 1


def uninstall() -> int:
    for name in (TASK, BACKUP_TASK):
        ps(f'schtasks /Delete /TN "{name}" /F')
        print(f"[已删除] {name}")
    return 0


def main() -> int:
    action = (sys.argv[1] if len(sys.argv) > 1 else "start").lower()
    table = {"install": install, "install-backup": install_backup, "start": start,
             "stop": stop, "status": status, "uninstall": uninstall}
    fn = table.get(action)
    if fn is None:
        print("用法：service_task.py install|install-backup|start|stop|status|uninstall")
        return 2
    return fn()


if __name__ == "__main__":
    sys.exit(main())

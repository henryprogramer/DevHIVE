# run.py
import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class ReloadHandler(FileSystemEventHandler):
    def __init__(self, runner):
        self.runner = runner

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"\n🔄 Alteração detectada em {event.src_path}")
            self.runner.restart()


class AppRunner:
    def __init__(self):
        self.process = None

    def start(self):
        print("🚀 Iniciando aplicação...")
        self.process = subprocess.Popen([sys.executable, "principal.py"])

    def stop(self):
        if self.process:
            print("🛑 Parando aplicação...")
            self.process.terminate()
            self.process.wait()

    def restart(self):
        self.stop()
        time.sleep(0.5)
        self.start()


if __name__ == "__main__":
    path = Path(".").resolve()
    runner = AppRunner()
    runner.start()

    event_handler = ReloadHandler(runner)
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()

    print("👀 Observando alterações... (Ctrl+C para sair)\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        runner.stop()

    observer.join()

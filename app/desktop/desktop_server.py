import contextlib
import threading
import time

import kiln_studio.server as kiln_server
import uvicorn


def server_config(port=8757):
    return uvicorn.Config(
        kiln_server.app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        use_colors=False,
    )


class ThreadedServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        self.stopped = False
        thread = threading.Thread(target=self.run_safe, daemon=True)
        thread.start()
        try:
            while not self.started and not self.stopped:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()

    def run_safe(self):
        try:
            self.run()
        finally:
            self.stopped = True

    def running(self):
        return self.started and not self.stopped


def run_studio():
    uvicorn.run(kiln_server.app, host="127.0.0.1", port=8757, log_level="warning")


def run_studio_thread():
    thread = threading.Thread(target=run_studio)
    thread.start()
    return thread

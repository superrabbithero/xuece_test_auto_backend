from threading import Thread
import subprocess
import socket
import time

ADB_PATH = "adb"
SCRCPY_SERVER_PATH = "./scrcpy-server"
DEVICE_SERVER_PATH = "/data/local/tmp/scrcpy-server.jar"
LOCAL_PORT = 12345

class Scrcpy:
    def __init__(self):
        self.video_socket = None
        self.audio_socket = None
        self.control_socket = None

        self.android_thread = None
        self.video_thread = None
        self.audio_thread = None
        self.control_thread = None
        self.android_process = None

    def push_server_to_device(self):
        print("Pushing scrcpy-server.jar to device...")
        result = subprocess.run([ADB_PATH, "push", SCRCPY_SERVER_PATH, DEVICE_SERVER_PATH], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error pushing server: {result.stderr}")
            return False
        return True

    def setup_adb_forward(self):
        print(f"Setting up ADB forward: tcp:{LOCAL_PORT} -> localabstract:scrcpy")
        subprocess.run([ADB_PATH, "forward", f"tcp:{LOCAL_PORT}", "localabstract:scrcpy"], check=True)

    def start_server(self):
        print("Starting scrcpy server in background...")
        cmd = [
            ADB_PATH, "shell",
            f"CLASSPATH={DEVICE_SERVER_PATH} app_process / com.genymobile.scrcpy.Server 3.1 tunnel_forward=true log_level=VERBOSE video_bit_rate=" + self.video_bit_rate
        ]
        self.android_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while not self.stop:
            stderr_line = self.android_process.stderr.readline().decode().strip()
            if not stderr_line:
                break
            if stderr_line:
                print(f"Server error: {stderr_line}")
        self.android_process.wait()
        print("Server stopped")

    def receive_video_data(self):
        print("Receiving video data (H.264)...")
        try:
            self.video_socket.recv(1)
            while not self.stop:
                data = self.video_socket.recv(20480)
                if not data:
                    break
                self.video_callback(data)
        except (ConnectionAbortedError, ConnectionResetError, OSError):
            pass
        print("Video data reception stopped")

    def receive_audio_data(self):
        print("Receiving audio data...")
        try:
            self.audio_socket.recv(1)
            while not self.stop:
                data = self.audio_socket.recv(1024)
                if not data:
                    break
        except (ConnectionAbortedError, ConnectionResetError, OSError):
            pass
        print("Audio data reception stopped")

    def handle_control_conn(self):
        print("Control connection established (idle)...")
        try:
            self.control_socket.recv(1)
            while not self.stop:
                data = self.control_socket.recv(1024)
                if not data:
                    break
                print("Control Mesg:", data)
        except (ConnectionAbortedError, ConnectionResetError, OSError):
            pass
        print("Control connection stopped")

    def scrcpy_start(self, video_callback, video_bit_rate):
        self.video_bit_rate = video_bit_rate
        self.video_callback = video_callback
        self.stop = False

        result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
        if "device" not in result.stdout:
            print("No device found. Please connect your Android device via USB.")
            return
        print(result.stdout)

        if not self.push_server_to_device():
            print("Failed to push server files to device.")
            return

        self.setup_adb_forward()
        self.android_thread = Thread(target=self.start_server, daemon=True)
        self.android_thread.start()
        time.sleep(1)

        # video connection
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.connect(('localhost', LOCAL_PORT))
        print("Video connection established")

        # audio connection
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket.connect(('localhost', LOCAL_PORT))
        print("Audio connection established")

        # contorl connection
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.connect(('localhost', LOCAL_PORT))
        print("Control connection established")

        self.video_thread = Thread(target=self.receive_video_data, daemon=True)
        self.audio_thread = Thread(target=self.receive_audio_data, daemon=True)
        self.control_thread = Thread(target=self.handle_control_conn, daemon=True)
        self.video_thread.start()
        self.audio_thread.start()
        self.control_thread.start()
        print("Background tasks started")

    def scrcpy_stop(self):
        print("Stopping Scrcpy")
        self.stop = True

        def safe_close(sock, name):
            if sock is None:
                return
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

        safe_close(self.video_socket, "video")
        safe_close(self.audio_socket, "audio")
        safe_close(self.control_socket, "control")
        self.video_socket = self.audio_socket = self.control_socket = None

        for t in (self.video_thread, self.audio_thread, self.control_thread):
            if t and t.is_alive():
                t.join(timeout=2)

        if self.android_process and self.android_process.poll() is None:
            self.android_process.terminate()
            try:
                self.android_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.android_process.kill()

        if self.android_thread and self.android_thread.is_alive():
            self.android_thread.join(timeout=2)

        self.android_process = None
        self.video_thread = self.audio_thread = self.control_thread = self.android_thread = None
        print("Scrcpy stopped")

    def scrcpy_send_control(self, data):
        if self.control_socket is None:
            return
        try:
            self.control_socket.send(data)
        except OSError:
            pass
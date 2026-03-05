#在 sockets.py中，处理实时截图数据和前端发来的控制指令
import subprocess
import threading
from flask_socketio import emit
from . import socketio  # 导入的是 __init__.py 中已创建的实例
from flask import request,Flask
import base64
from .utils.appium_connector import AppiumDeviceConnector
from .utils.scrcpy import Scrcpy

# 全局字典，管理不同设备连接
active_connections = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# connector = None


@socketio.on('connect')
def handle_connect():
    print(f'客户端 {request.sid} 已连接')

@socketio.on('disconnect')
def handle_disconnect():
    global scpy_ctx, client_sid
    print(f'客户端 {request.sid} 已断开')
    # 清理 scrcpy（若断开的是 scrcpy 客户端）
    if client_sid == request.sid:
        client_sid = None
        if scpy_ctx is not None:
            scpy_ctx.scrcpy_stop()
            scpy_ctx = None
            print('scrcpy stopped (client disconnected)')
    # 清理该客户端关联的设备连接
    for udid, conn_data in list(active_connections.items()):
        if conn_data['sid'] == request.sid:
            conn_data['connector'].disconnect()
            del active_connections[udid]
            break

@socketio.on('start_stream')
def handle_start_stream(data):
    """前端请求开始实时流"""
    device_udid = data['udid']
    if device_udid not in active_connections:
        connector = AppiumDeviceConnector(device_udid)
        if connector.connect():
            temSid = request.sid
            active_connections[device_udid] = {'connector': connector, 'sid': request.sid}
        else:
            socketio.emit('error', {'message': f'无法连接设备 {device_udid}'})
    else:
        socketio.emit('stream_started', {'udid': device_udid})

@socketio.on('tap')
def handle_tap(data):
    """处理前端发来的点击事件"""
    device_udid = data['udid']
    x = data['x']
    y = data['y']
    if device_udid in active_connections:
        connector = active_connections[device_udid]['connector']
        success = connector.perform_tap(x, y)
        emit('tap_result', {'success': success})

@socketio.on('ui_tree')
def get_ui_tree(data):
    device_udid = data['udid']
    screenshot_bytes =  data["with_screenshot"]
    
    if device_udid in active_connections:
        connector = active_connections[device_udid]['connector']
        # print(connector)
        ui_tree = connector.get_ui_tree()

        screenshot_base64 = ""
        if screenshot_bytes:
            screenshot_bytes = connector.driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        # print(ui_tree)
        emit('ui_tree_data', {
            'data': ui_tree,
            'screenshot': screenshot_base64})

#基于web-scrcpy的实时屏幕控件
import queue
scpy_ctx = None
client_sid = None
message_queue = queue.Queue()
video_bit_rate = "1024000"

def video_send_task():
    global client_sid
    while client_sid != None:
        try:
            message = message_queue.get(timeout=0.01)
            socketio.emit('video_data', message, to=client_sid)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error sending data: {e}")
        finally:
            socketio.sleep(0.001)
    print(f"video_send_task stopped")

def send_video_data(data):
    message_queue.put(data)

@socketio.on('scrcpy_connect')
def handle_scrcpy_connect():
    global scpy_ctx, client_sid
    print('scrcpy_connect from client', request.sid)

    if scpy_ctx is not None:
        print('scrcpy already running, stopping old instance first')
        scpy_ctx.scrcpy_stop()
        scpy_ctx = None
        client_sid = None

    client_sid = request.sid
    scpy_ctx = Scrcpy()
    scpy_ctx.scrcpy_start(send_video_data, video_bit_rate)
    socketio.start_background_task(video_send_task)
    print('scrcpy started for client', request.sid)

@socketio.on('scrcpy_disconnect')
def handle_scrcpy_disconnect():
    global scpy_ctx, client_sid
    print('scrcpy_disconnect from client', request.sid)
    if client_sid == request.sid and scpy_ctx is not None:
        client_sid = None
        scpy_ctx.scrcpy_stop()
        scpy_ctx = None
        print('scrcpy stopped (user closed view)')

@socketio.on('scrcpy_ping')
def handle_scrcpy_ping(data):
    """用于测量网络延迟：客户端发送时间戳，服务端原样回传"""
    emit('scrcpy_pong', data)

@socketio.on('control_data')
def handle_control_data(data):
    global scpy_ctx
    if scpy_ctx is not None:
        scpy_ctx.scrcpy_send_control(data)
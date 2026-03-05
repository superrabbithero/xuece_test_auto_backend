# Android 设备自动化测试后端

这是一个基于 Flask 和 Socket.IO 的 Android 设备自动化测试后端应用，提供实时设备控制、屏幕镜像和 UI 树分析功能。

## 功能特性

- 📱 **设备管理**：通过 ADB 获取已连接的 Android 设备列表
- 🎥 **实时屏幕流**：使用 Scrcpy 实现低延迟的设备屏幕镜像
- 🖱️ **远程控制**：支持通过 Web 界面远程点击设备屏幕
- 📊 **UI 树分析**：获取设备当前界面的 UI 结构树
- 🚀 **Appium 集成**：使用 Appium 进行高级自动化操作

## 技术栈

- **后端框架**：Flask
- **实时通信**：Socket.IO
- **设备交互**：ADB、Appium
- **屏幕镜像**：Scrcpy
- **编程语言**：Python

## 安装和依赖

### 系统依赖

- Python 3.10+
- ADB (Android Debug Bridge)
- Appium Server
- Android SDK

### Python 依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动后端服务

```bash
python run.py
```

服务将在 `http://0.0.0.0:5000` 启动。

### 设备连接

1. 确保 Android 设备已启用开发者选项和 USB 调试
2. 使用 USB 数据线连接设备到电脑
3. 验证设备连接：
   ```bash
   adb devices
   ```

## API 接口

### GET /api/devices

获取已连接的 Android 设备列表。

**响应示例**：
```json
[
  {
    "udid": "1234567890abcdef",
    "status": "device"
  }
]
```

## Socket.IO 事件

### 客户端事件

#### connect
建立 Socket.IO 连接。

#### start_stream
开始设备屏幕流。
```json
{
  "udid": "设备ID"
}
```

#### tap
执行屏幕点击操作。
```json
{
  "udid": "设备ID",
  "x": 100,
  "y": 200
}
```

#### ui_tree
获取设备 UI 树。
```json
{
  "udid": "设备ID",
  "with_screenshot": true
}
```

#### scrcpy_connect
建立 Scrcpy 连接。

#### control_data
发送控制数据到 Scrcpy 服务。

### 服务端事件

#### error
发送错误信息。
```json
{
  "message": "错误信息"
}
```

#### stream_started
屏幕流已开始。
```json
{
  "udid": "设备ID"
}
```

#### tap_result
点击操作结果。
```json
{
  "success": true
}
```

#### ui_tree_data
UI 树数据。
```json
{
  "data": "UI树XML",
  "screenshot": "base64编码的截图"
}
```

#### video_data
视频流数据（H.264）。

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── routes.py            # REST API 路由
│   ├── sockets.py           # Socket.IO 事件处理
│   ├── utils/
│   │   ├── appium_connector.py  # Appium 设备连接
│   │   ├── networkMonitor.py    # 网络监控
│   │   └── scrcpy.py            # Scrcpy 屏幕镜像
│   └── models..py           # 数据模型
├── appium.config.json       # Appium 配置
├── check.json               # 检查配置
├── config.py                # 应用配置
├── requirements.txt         # Python 依赖
├── run.py                   # 应用入口
└── scrcpy-server            # Scrcpy 服务器文件
```

## 核心模块说明

### AppiumDeviceConnector
负责与 Appium Server 通信，提供设备连接、UI 树获取和屏幕操作功能。使用 lxml 库解析 UI 树 XML 数据。

### Scrcpy
实现与 Scrcpy 服务器的通信，提供高性能的屏幕镜像功能。通过 socket 接收 H.264 视频流并转发给前端。

## 配置说明

### Appium 配置

在 `app/utils/appium_connector.py` 中配置 Appium 服务器地址和 ADB 路径：

```python
options.adb_exec_path = r'C:\Users\PFMXB0715004X\AppData\Local\Android\Sdk\platform-tools\adb.exe'
self.driver = webdriver.Remote(command_executor=self.appium_server_url, options=options)
```

### Scrcpy 配置

在 `app/utils/scrcpy.py` 中配置视频比特率：

```python
video_bit_rate = "1024000"
```

## 开发说明

### 调试模式

服务默认以调试模式启动，可在 `run.py` 中修改：

```python
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

### 日志

服务运行日志会输出到控制台，可在代码中添加更多日志记录：

```python
print("调试信息")
```

## 注意事项

1. 确保 Appium Server 已启动：
   ```bash
   appium
   ```

2. 第一次连接设备时，可能需要在设备上授权 USB 调试。

3. Scrcpy 功能需要设备支持 H.264 视频编码。

4. 长时间运行时，服务会自动发送保活命令以维持连接。

## 故障排除

### 设备连接失败

- 检查设备是否已启用开发者选项和 USB 调试
- 验证 ADB 路径是否正确
- 尝试重启 ADB 服务：
  ```bash
  adb kill-server
  adb start-server
  ```

### 屏幕流无响应

- 检查 Scrcpy 服务器文件是否存在
- 验证设备是否支持 H.264 编码
- 尝试调整视频比特率

## 许可证

MIT License

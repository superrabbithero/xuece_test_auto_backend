# 这个类是后端与设备交互的核心，负责启动 Appium 会话、定期截图、执行操作

import base64
from appium import webdriver
from appium.options.android import UiAutomator2Options
import threading
import time
from lxml import etree

class AppiumDeviceConnector:
    def __init__(self, device_udid, appium_server_url='http://localhost:4723'):
        self.device_udid = device_udid
        self.appium_server_url = appium_server_url
        self.driver = None
        self.screenshot_callbacks = []  # 注册回调函数，用于推送截图
        self.keep_alive_thread = None

    def connect(self, desired_caps=None):
        """连接设备并启动会话"""
        if desired_caps is None:
            desired_caps = {
                "platformName": "Android",
                "appium:udid": self.device_udid,  # 使用传入的设备 UDID
                "appium:automationName": "UiAutomator2",
                "appium:noReset": True,           # 避免每次重置应用
                "appium:fullReset": False,
                # 如需测试特定应用，请添加 appPackage 和 appActivity
                "appium:appPackage": "com.uni.xuecestupad",
                "appium:appActivity": "cn.unisolution.onlineexamstu.MainActivity",
            }
        options = UiAutomator2Options().load_capabilities(desired_caps)
        options.adb_exec_path = r'C:\Users\PFMXB0715004X\AppData\Local\Android\Sdk\platform-tools\adb.exe'
        self.driver = webdriver.Remote(command_executor=self.appium_server_url, options=options)

        if self.driver is not None:
            self.keep_alive_thread = self._start_keep_alive()

        return self.driver is not None

    def _start_keep_alive(self, interval=30):
        """定时发送保持连接的命令"""
        def _keep_alive():
            while getattr(thread, "do_run", True):
                try:
                     print(f"###保活线程###Session ID: {self.driver.execute_script('mobile: getDeviceTime')}")
                except:
                    pass
                time.sleep(interval)
        
        thread = threading.Thread(target=_keep_alive, daemon=True)
        thread.do_run = True
        thread.start()
        return thread


    # 获得ui树
    def get_ui_tree(self):
        ui_tree = self.driver.page_source # 返回 XML 格式的 UI 树
        # 假设 page_source 是获取的 XML
        tree = etree.fromstring(ui_tree.encode('utf-8'))
        print(tree)
        return ui_tree

    def start_screenshot_stream(self, interval=1.0):
        """在后台线程中定期获取截图并通知回调"""
        def screenshot_loop():
            while self.driver is not None:
                try:
                    screenshot_b64 = self.driver.get_screenshot_as_base64()
                    print("截图成功")
                    for callback in self.screenshot_callbacks:
                        print("有回调函数")
                        callback(screenshot_b64)  # 将 base64 截图发送给所有回调
                except Exception as e:
                    print(f"获取截图时出错: {e}")
                time.sleep(interval)
        thread = threading.Thread(target=screenshot_loop, daemon=True)
        thread.start()

    def perform_tap(self, x, y):
        """在设备屏幕的指定坐标执行点击操作"""
        if self.driver:
            try:
                # Appium 的 Tap 操作通常通过 TouchAction 或 W3C Actions 实现。
                # 这里使用更常见的 W3C Actions 中的指针操作。
                actions = ActionChains(self.driver)
                actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                actions.w3c_actions.pointer_action.move_to_location(x, y)
                actions.w3c_actions.pointer_action.pointer_down()
                actions.w3c_actions.pointer_action.pause(0.1)
                actions.w3c_actions.pointer_action.pointer_up()
                actions.perform()
                return True
            except Exception as e:
                print(f"执行点击操作时出错: {e}")
                return False
        return False

    def register_screenshot_callback(self, callback):
        """注册一个回调函数，当有新截图时调用"""
        self.screenshot_callbacks.append(callback)


    def disconnect(self):
        """安全断开连接"""
        if self.keep_alive_thread:
            self.keep_alive_thread.do_run = False  # 停止保活线程
            self.keep_alive_thread.join(timeout=5)
        
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error quitting driver: {str(e)}")
            finally:
                self.driver = None
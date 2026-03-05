from appium import webdriver
from pprint import pprint
import json
import time
import matplotlib.pyplot as plt
from collections import defaultdict
import subprocess

class NetworkMonitor:
    def __init__(self, app_package):
        self.app_package = app_package
        self.requests = defaultdict(list)
        self.driver = None
        
    def start_capture(self):
        # Appium 配置 - 移除了不支持的performance日志配置
        caps = {
            "platformName": "Android",
            "deviceName": "emulator-5554",
            "appPackage": self.app_package,
            "appActivity": "cn.unisolution.onlineexamstu.MainActivity",
            "automationName": "UiAutomator2",
            "newCommandTimeout": 600
        }
        
        self.driver = webdriver.Remote(
            'http://localhost:4723', 
            caps
        )
        
    def collect_requests(self, duration=60):
        """使用ADB命令收集网络请求"""
        start_time = time.time()
        
        # 获取应用的UID
        uid_cmd = f"adb shell dumpsys package {self.app_package} | findstr userId"
        uid_result = subprocess.run(uid_cmd, shell=True, capture_output=True, text=True)
        uid = uid_result.stdout.split('=')[1].strip() if 'userId=' in uid_result.stdout else None
        


        if not uid:
            print("无法获取应用UID")
            return
            
        while time.time() - start_time < duration:
            try:
                # 使用ADB获取网络统计
                cmd = f"adb shell cat /proc/net/dev | findstr {uid}"
                print(cmd)
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    # 解析网络数据
                    for line in result.stdout.splitlines():
                        parts = line.split()
                        if len(parts) >= 8:
                            rx_bytes = int(parts[5])
                            tx_bytes = int(parts[7])
                            timestamp = time.time()
                            
                            self.requests['total'].append({
                                'timestamp': timestamp,
                                'rx_bytes': rx_bytes,
                                'tx_bytes': tx_bytes
                            })
                
                time.sleep(1)  # 每秒收集一次
                
            except Exception as e:
                print(f"收集错误: {e}")
    
    def visualize_requests(self):
        """可视化网络流量"""
        if not self.requests.get('total'):
            print("未捕获到网络流量数据")
            return
            
        timestamps = [r['timestamp'] for r in self.requests['total']]
        rx_data = [r['rx_bytes']/1024 for r in self.requests['total']]  # 转换为KB
        tx_data = [r['tx_bytes']/1024 for r in self.requests['total']]
        
        plt.figure(figsize=(12, 6))
        
        # 接收流量
        plt.subplot(2, 1, 1)
        plt.plot(timestamps, rx_data, 'b-', label='Download')
        plt.title('Network Traffic (KB)')
        plt.ylabel('Download (KB)')
        plt.legend()
        
        # 发送流量
        plt.subplot(2, 1, 2)
        plt.plot(timestamps, tx_data, 'r-', label='Upload')
        plt.ylabel('Upload (KB)')
        plt.xlabel('Time (timestamp)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('network_traffic.png')
        plt.show()
    
    def stop(self):
        if self.driver:
            self.driver.quit()

# 使用示例
if __name__ == "__main__":
    monitor = NetworkMonitor("com.uni.xuecestupad")  # 替换为你的应用包名
    
    try:
        print("🚀 启动Appium并开始监控网络...")
        monitor.start_capture()
        monitor.collect_requests(duration=30)  # 监控30秒
        print("📊 生成可视化报告...")
        monitor.visualize_requests()
        
    finally:
        monitor.stop()
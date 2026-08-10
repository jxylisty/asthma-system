import requests

backend = "http://localhost:8000"
# 启动后端测试
try:
    r = requests.get(f"{backend}/api/v1/prescriptions/1", timeout=10)
    if r.status_code == 200:
        data = r.json()
        has_herbs = 'herbs' in data
        has_data = 'data' in data
        has_data_herbs = 'herbs' in data.get('data', {}) if isinstance(data.get('data'), dict) else False
        print(f"prescription/1 response: code_in_top={('code' in data)}  herbs_in_top={has_herbs}  data_in_top={has_data}")
        if has_data:
            print(f"  data type: {type(data['data']).__name__}")
            if isinstance(data['data'], dict):
                print(f"  data keys: {list(data['data'].keys())[:5]}")
        print(f"  top-level keys: {[k for k in data.keys() if k != 'data']}")
except Exception as e:
    print(f"Backend not running: {e}")

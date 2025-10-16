# Flask 应用添加简单密码保护

## 方案 A: 使用环境变量设置密码

在 `api/index.py` 中添加：

```python
import os
from flask import Flask, request, jsonify
from functools import wraps

# 简单的密码保护中间件
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从环境变量获取密码
        expected_password = os.environ.get('APP_PASSWORD')
        
        if not expected_password:
            # 如果没有设置密码，允许访问
            return f(*args, **kwargs)
        
        # 检查请求头中的密码
        auth_password = request.headers.get('X-App-Password')
        
        if auth_password != expected_password:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# 在需要保护的路由上使用
@app.route('/api/notes', methods=['GET'])
@require_auth
def get_notes():
    # ... 你的代码
    pass
```

### 在 Vercel 中设置密码：

1. Vercel Dashboard → Settings → Environment Variables
2. 添加 `APP_PASSWORD` = 你的密码
3. Redeploy

### 前端使用：

```javascript
// 在 index.html 中添加
const APP_PASSWORD = prompt('请输入访问密码：');

fetch('/api/notes', {
    headers: {
        'X-App-Password': APP_PASSWORD
    }
})
```

## 方案 B: 使用 HTTP Basic Authentication

在 `api/index.py` 中：

```python
from flask import Flask, Response, request
from functools import wraps

def check_auth(username, password):
    """验证用户名和密码"""
    expected_username = os.environ.get('AUTH_USERNAME', 'admin')
    expected_password = os.environ.get('AUTH_PASSWORD')
    return username == expected_username and password == expected_password

def authenticate():
    """发送 401 响应，要求用户认证"""
    return Response(
        'Could not verify your access level.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# 保护整个应用
@app.before_request
def before_request():
    if request.endpoint not in ['health']:  # 允许健康检查不需要认证
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
```

### 在 Vercel 设置：

1. 添加环境变量：
   - `AUTH_USERNAME` = admin
   - `AUTH_PASSWORD` = 你的密码

## 方案 C: 使用 OAuth（Google, GitHub 等）

安装 Flask-Login 和 Authlib：

```bash
pip install flask-login authlib
```

然后实现 OAuth 登录流程。

## 方案 D: IP 白名单（在 Vercel 中）

仅 Vercel Pro 及以上计划可用：

```
Settings → Deployment Protection → IP Allowlist
添加允许访问的 IP 地址
```

## 推荐方案总结

### 免费/简单方案：
- ✅ 使用方案 B（HTTP Basic Authentication）
- 最简单，浏览器内置支持
- 适合个人项目

### 专业方案：
- ✅ 升级 Vercel Pro 计划
- 使用 Vercel 的 Deployment Protection
- 最安全，最简单配置

### 生产级方案：
- ✅ 实现完整的用户系统
- JWT Token 认证
- 数据库存储用户信息
- OAuth 第三方登录

你想使用哪种方案？我可以帮你实现！

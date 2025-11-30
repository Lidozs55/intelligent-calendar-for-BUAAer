from services.buaa_api import login_buaa

# 测试登录功能
def test_login():
    try:
        # 使用测试账号密码（实际使用时需要替换为真实账号密码）
        username = 'test_username'
        password = 'test_password'
        
        print(f"尝试登录北航系统，用户名: {username}")
        cookies = login_buaa(username, password)
        print(f"登录成功! 获取到Cookie: {cookies}")
    except Exception as e:
        print(f"登录失败: {e}")

if __name__ == "__main__":
    test_login()
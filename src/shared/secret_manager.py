import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json
from pathlib import Path

class SecretManager:
    """
    敏感信息管理器，用于加密和解密环境变量中的敏感信息
    """
    def __init__(self, key_file: str = ".secret_key"):
        self.key_file = Path(key_file)
        self.key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """
        加载或生成密钥
        """
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            # 生成新密钥
            key = Fernet.generate_key()
            # 保存密钥到文件
            with open(self.key_file, "wb") as f:
                f.write(key)
            # 设置文件权限，仅允许当前用户访问
            self.key_file.chmod(0o600)
            print(f"[密钥] 生成新的密钥文件: {self.key_file}")
            return key

    def encrypt(self, plaintext: str) -> str:
        """
        加密明文
        """
        encrypted = self.cipher_suite.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        解密密文
        """
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = self.cipher_suite.decrypt(encrypted)
        return decrypted.decode()

    def encrypt_file(self, input_file: str, output_file: str):
        """
        加密文件
        """
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        encrypted_content = self.encrypt(content)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(encrypted_content)
        
        print(f"[加密] 文件已加密: {input_file} -> {output_file}")

    def decrypt_file(self, input_file: str, output_file: str):
        """
        解密文件
        """
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        decrypted_content = self.decrypt(content)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(decrypted_content)
        
        print(f"[解密] 文件已解密: {input_file} -> {output_file}")

    def encrypt_env_file(self, input_file: str, output_file: str):
        """
        加密环境变量文件
        """
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        encrypted_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # 只加密敏感信息
                if any(key in sensitive_key for sensitive_key in ["API_KEY", "SECRET_KEY", "PASSWORD", "TOKEN"]):
                    encrypted_value = self.encrypt(value)
                    encrypted_lines.append(f"{key}=ENCRYPTED:{encrypted_value}\n")
                else:
                    encrypted_lines.append(f"{key}={value}\n")
            else:
                encrypted_lines.append(line + "\n")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(encrypted_lines)
        
        print(f"🔒 环境变量文件已加密: {input_file} -> {output_file}")

    def decrypt_env_file(self, input_file: str, output_file: str):
        """
        解密环境变量文件
        """
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        decrypted_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if value.startswith("ENCRYPTED:"):
                    encrypted_value = value.split("ENCRYPTED:", 1)[1]
                    decrypted_value = self.decrypt(encrypted_value)
                    decrypted_lines.append(f"{key}={decrypted_value}\n")
                else:
                    decrypted_lines.append(f"{key}={value}\n")
            else:
                decrypted_lines.append(line + "\n")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(decrypted_lines)
        
        print(f"🔓 环境变量文件已解密: {input_file} -> {output_file}")

    def get_secret(self, key: str) -> str:
        """
        获取解密后的环境变量
        """
        value = os.environ.get(key)
        if not value:
            return ""
        
        if value.startswith("ENCRYPTED:"):
            encrypted_value = value.split("ENCRYPTED:", 1)[1]
            return self.decrypt(encrypted_value)
        return value


# 示例用法
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="敏感信息加密工具")
    parser.add_argument("action", choices=["encrypt", "decrypt", "encrypt-file", "decrypt-file", "encrypt-env", "decrypt-env"], help="操作类型")
    parser.add_argument("input", help="输入文件或明文")
    parser.add_argument("output", nargs="?", help="输出文件")
    
    args = parser.parse_args()
    
    manager = SecretManager()
    
    if args.action == "encrypt":
        encrypted = manager.encrypt(args.input)
        print(f"加密结果: {encrypted}")
    elif args.action == "decrypt":
        decrypted = manager.decrypt(args.input)
        print(f"解密结果: {decrypted}")
    elif args.action == "encrypt-file":
        if not args.output:
            print("错误: 缺少输出文件")
        else:
            manager.encrypt_file(args.input, args.output)
    elif args.action == "decrypt-file":
        if not args.output:
            print("错误: 缺少输出文件")
        else:
            manager.decrypt_file(args.input, args.output)
    elif args.action == "encrypt-env":
        if not args.output:
            print("错误: 缺少输出文件")
        else:
            manager.encrypt_env_file(args.input, args.output)
    elif args.action == "decrypt-env":
        if not args.output:
            print("错误: 缺少输出文件")
        else:
            manager.decrypt_env_file(args.input, args.output)

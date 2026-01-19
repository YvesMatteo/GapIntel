
import os
import sys

try:
    from cryptography.fernet import Fernet
    print("Cryptography module found.")
except ImportError:
    print("Cryptography module NOT found.")
    sys.exit(0)

# Key from .env (viewer earlier)
# ENCRYPTION_KEY=uMC3MiYrZ3srTMincDg0wI3j9THndtryV3l2F28633Q=
KEY = "uMC3MiYrZ3srTMincDg0wI3j9THndtryV3l2F28633Q="

try:
    f = Fernet(KEY)
    print("✅ Key is valid Fernet key.")
    token = f.encrypt(b"test")
    print(f"Encrypted: {token}")
    decrypted = f.decrypt(token)
    print(f"Decrypted: {decrypted}")
except Exception as e:
    print(f"❌ Key validation failed: {e}")

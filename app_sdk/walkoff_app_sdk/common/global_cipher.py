import base64

from Crypto import Random
from Crypto.Cipher import AES


class GlobalCipher(object):

    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    @staticmethod
    def pad(x):
        return x + (32 - len(x) % 32) * chr(32 - len(x) % 32)

    @staticmethod
    def unpad(x):
        return x[:-ord(x[len(x)-1:])]
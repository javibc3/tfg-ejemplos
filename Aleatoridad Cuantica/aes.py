# -*- coding: utf-8 -*-
# zato: ide-deploy=True
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
# Zato
from zato.server.service import Service

# ##############################################################################

class AESService(Service):

    name = 'quantum.quantum-aes'

    def handle(self) -> None:
        key = self.invoke('quantum.qrng', runs=32*8)
        iv = self.invoke('quantum.qrng', runs=16*8)
        cipher = Cipher(algorithms.AES(key['integer'].to_bytes(32,'big')), modes.CBC(iv['integer'].to_bytes(16,'big')))   
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        data = padder.update(self.request.payload['message'].encode()) + padder.finalize()
        ct = encryptor.update(data) + encryptor.finalize()
        output = {
            "message": self.request.payload['message'],
            "encrypted": ct
        }
        self.response.payload = str(output)


import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

password = b"this is a not very secure password"


def derive_key(password, salt):
    # According to https://datatracker.ietf.org/doc/html/rfc9106#section-4
    kdf = Argon2id(
        salt=salt,
        length=16,
        iterations=1,
        lanes=4,
        memory_cost=2**21,
    )
    return kdf.derive(password)


salt = os.urandom(16)
key = derive_key(password, salt)
print(key)


def encrypt(blob, file_id):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    aad = file_id.to_bytes(8, "big")
    ct = aesgcm.encrypt(nonce, blob, aad)
    return nonce + ct


def decrypt(enc_blob, file_id):
    aesgcm = AESGCM(key)
    nonce = enc_blob[:12]
    enc_data = enc_blob[12:]
    aad = file_id.to_bytes(8, "big")
    pt = aesgcm.decrypt(nonce, enc_data, aad)
    return pt


test_data = b"this is some test data"
file_id = 0
ct = encrypt(test_data, file_id)

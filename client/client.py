import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
import requests
from json import loads, dumps
from base64 import b64encode, b64decode
from hashlib import sha256
from getpass import getpass

N_FILES = 2**10


def H(data):
    return sha256(data).digest()


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


def encrypt(key, blob, file_id):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    aad = file_id.to_bytes(8, "big")
    ct = aesgcm.encrypt(nonce, blob, aad)
    return nonce + ct


def decrypt(key, enc_blob, file_id):
    aesgcm = AESGCM(key)
    nonce = enc_blob[:12]
    enc_data = enc_blob[12:]
    aad = file_id.to_bytes(8, "big")
    pt = aesgcm.decrypt(nonce, enc_data, aad)
    return pt


def empty_root():
    hash = H(b"")
    for _ in range(N_FILES.bit_length() - 1):
        hash = H(hash + hash)
    return hash


def calculate_root_hash(file_id, file_hash, hashes):
    current_index = N_FILES - 1 + file_id
    new_hash = file_hash
    for hash in hashes:
        l_sibling = new_hash if current_index % 2 == 1 else bytes.fromhex(hash)
        r_sibling = new_hash if current_index % 2 == 0 else bytes.fromhex(hash)
        current_index = (current_index + 1) // 2 - 1
        new_hash = H(l_sibling + r_sibling)

    return new_hash


def verify(json_data):
    file_b64 = json_data.get("blob", None)
    if file_b64 is None:
        return False

    hashes = json_data.get("hashes", None)
    if hashes is None:
        return False

    file = b64decode(file_b64)
    file_id = json_data.get("file_id")

    total_hash = calculate_root_hash(file_id, H(file), hashes)

    return total_hash.hex() == root_hash.hex()


def upload_file(key, file_id, file_path):

    with open(file_path, "rb") as file:
        blob = file.read()

    enc_blob = encrypt(key, blob, file_id)
    data = {"file_id": file_id, "blob": b64encode(enc_blob).decode()}
    r = requests.post("http://127.0.0.1:5000/save", json=data)
    if not r.ok:
        raise Exception(f"{r.status_code}: {r.json().get('msg', 'Unknown reason')}")

    res_data = r.json()
    old_hash = res_data["old_file_hash"]
    hashes = res_data["hashes"]

    if root_hash != calculate_root_hash(file_id, bytes.fromhex(old_hash), hashes):
        raise Exception("Server is trying to trick youuuu....")

    return True, calculate_root_hash(file_id, H(enc_blob), hashes)


def get_file(key, file_id, save_to_file_path):
    r = requests.get(f"http://127.0.0.1:5000/get-file/{file_id}")
    if not r.ok:
        raise Exception(f"{r.status_code}: {r.json().get('msg', 'Unkown reason')}")

    res_data = r.json()
    verified = verify(res_data)
    if not verified:
        raise Exception(f"Data failed verification")

    blob = res_data.get("blob", None)
    if blob is None:
        raise Exception(f"No blob in response")

    raw = decrypt(key, b64decode(blob), file_id)
    with open(save_to_file_path, "wb") as out_file:
        out_file.write(raw)
        return True


def get_root_hash():
    r = requests.get("http://127.0.0.1:5000/root")
    if not r.ok:
        return b""

    data = r.json()
    hash = data.get("root", None)
    if hash is None:
        return b""

    return bytes.fromhex(hash)


if __name__ == "__main__":
    if os.path.exists("root_hash"):
        with open("root_hash", "rb") as hash_file:
            root_hash = hash_file.read()

    else:
        root_hash = get_root_hash()

    if os.path.exists("salt"):
        with open("salt", "rb") as salt_file:
            salt = salt_file.read()

    else:
        salt = os.urandom(16)
        with open("salt", "wb") as salt_file:
            salt_file.write(salt)

    password = getpass().encode()
    key = derive_key(password, salt)

    while True:
        command = input("> ").split(" ")
        match command[0].lower():
            case "get":
                try:
                    file_id = int(command[1])
                    save_to_file_path = command[2]
                except:
                    print(
                        "Bad command. Should be: get <file_id (int)> <file_path_to_save_to>"
                    )
                    continue

                try:
                    success = get_file(key, file_id, save_to_file_path)
                except Exception as e:
                    print(f"Something went wrong: {e}")
                    continue

                if success:
                    print(
                        f"File {file_id} has been verified saved to device at {os.path.join(os.getcwd(), save_to_file_path)}"
                    )
                else:
                    print("Something went wrong :(")

            case "upload":
                try:
                    file_id = int(command[1])
                    file_path = command[2]
                except:
                    print("Bad command. Should be: upload <file_id (int)> <file_path>")
                    continue

                try:
                    success, new_hash = upload_file(key, file_id, file_path)
                except Exception as e:
                    print(f"Something went wrong: {e}")
                    continue

                if success:
                    root_hash = new_hash
                    with open("root_hash", "wb") as hash_file:
                        hash_file.write(root_hash)

                    print(
                        f"Successfully uploaded {file_path} to server at file_id {file_id}"
                    )
                else:
                    print("Something went wrong :(")

            case "q":
                exit(0)

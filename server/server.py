from hashlib import sha256
from flask import Flask, json, request, jsonify
from http import HTTPStatus
from base64 import b64encode, b64decode

app = Flask(__name__)


def H(data):
    return sha256(data).digest()


# 2^10 = 1024
N_FILES = 2**10
files = [b"" for _ in range(N_FILES)]

"""
                1
        2               3
    4       5       6       7

but bigger
"""
merkle_tree = [b"" for _ in range(N_FILES * 2 - 1)]


def update_merkle_tree(file_id, blob):
    merkle_index = N_FILES - 1 + file_id
    merkle_tree[merkle_index] = H(blob)
    current_index = merkle_index
    while current_index > 0:
        current_index = (current_index + 1) // 2 - 1
        l_child = (current_index + 1) * 2 - 1
        r_child = (current_index + 1) * 2
        merkle_tree[current_index] = H(merkle_tree[l_child] + merkle_tree[r_child])


def get_hashes(file_id):
    # Gets the hashes from bottom to top of the merkle tree, only with the hashes needed to compute the parent
    hashes = []
    merkle_index = N_FILES - 1 + file_id
    current_index = merkle_index
    while current_index > 0:
        sibling_index = ((current_index + 1) ^ 1) - 1
        hashes.append(merkle_tree[sibling_index].hex())
        current_index = (current_index + 1) // 2 - 1

    return hashes


def save_file(file_id, blob):
    files[file_id] = blob
    update_merkle_tree(file_id, blob)


for i, file in enumerate(files):
    update_merkle_tree(i, file)


@app.route("/save", methods=["POST"])
def save():
    if not request.is_json:
        return jsonify({"msg": "Data must be json"}), HTTPStatus.UNPROCESSABLE_ENTITY

    data = request.json
    file_id = data.get("file_id", None)
    if file_id is None:
        return jsonify({"msg": "Missing file_id"}), HTTPStatus.BAD_REQUEST

    if file_id < 0 or file_id >= N_FILES:
        return (
            jsonify(
                {
                    "msg": f"Invalid file_id, it must be between 0 and {N_FILES} (not inclusive)"
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    blob = b64decode(data.get("blob", None))
    if blob is None:
        return jsonify({"msg": "Blob is empty"}), HTTPStatus.BAD_REQUEST

    save_file(file_id, blob)
    print(merkle_tree[0])
    new_hashes = get_hashes(file_id)
    return jsonify(
        {"msg": "success", "file_id": file_id, "hashes": new_hashes}
    ), HTTPStatus.CREATED


@app.route("/get-file/<int:file_id>", methods=["GET"])
def get_file(file_id: int):
    if file_id < 0 or file_id >= N_FILES:
        return (
            jsonify(
                {
                    "msg": f"Invalid file_id, it must be between 0 and {N_FILES} (not inclusive)"
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )
    file = files[file_id]
    hashes = get_hashes(file_id)
    data = {"file_id": file_id, "blob": b64encode(file).decode(), "hashes": hashes}
    return jsonify(data)


@app.route("/root", methods=["GET"])
def get_root():
    return jsonify({"root": merkle_tree[0].hex()})


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)

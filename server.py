from hashlib import sha256


def H(data):
    return sha256(data).digest()


# 2^10 = 1024
N_FILES = 2**2
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


for i, file in enumerate(files):
    update_merkle_tree(i, file)


print(merkle_tree)

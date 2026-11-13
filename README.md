# Samolss-cryptography

## HTTP

Because its simple
Upload a file at
/save
Pass along some json with:
"file_id" (int) what file_id the server should save the file under,
"blob" the encrypted data of the file with the nonce as a prefix, all of this as b64.

It will return a json object. If the request fails it will only contain a message under the key "msg".
If the upload is successful, the json will include, "file_id"(int), "old_file_hash"(the hash for the file that was there before, for verification, as hexstring), "hashes"(a list of hexstrings of the complementary hashes, from the bottom of the tree to the top)

/get-file/<file_id (int)>
Returns the encrypted blob, hashes and file_id.
file_id should be between 0 and N_FILES (not inclusive and currently 2^10)
If the request fails it returns a json object with only the "msg" key.
Otherwise, it will include "file_id"(int), "blob"(b64 encrypted file) and "hashes" (list of hexstrings of complementary hashes)

/root
Returns the roothash as of this moment, if you want to trust it.
Json object with "root" key, the value is the root hash as hex.

## Why do the way it do it??

### AES-GCM

Its secure, theres no need to use HMAC, everything is just done for you automatically and securely. Very good, very nice.

### SHA-256

It was recommended.

### Argon2id

From what ive heard its supposed to be the gold standard for password hashing (partly because of the slowness) so i thought it would be nice to use it. I used this with the recommended parameters from <https://datatracker.ietf.org/doc/html/rfc9106#section-4>, except for the keylength which i used 16 bytes since i couldn't be bothered to change to 32 bytes in the cipher.

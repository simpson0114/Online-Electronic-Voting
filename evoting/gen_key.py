from nacl.signing import SigningKey
from nacl.encoding import Base64Encoder


signing_key = SigningKey.generate()

verify_key = signing_key.verify_key
with open("private_key", "wb") as f:
    f.write(signing_key.encode(encoder=Base64Encoder))
with open("public_key", "wb") as f:
    f.write(verify_key.encode(encoder=Base64Encoder))
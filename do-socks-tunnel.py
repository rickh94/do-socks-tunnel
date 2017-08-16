"""Not-so-simple script to initiate a digitalocean droplet and tunnel through
it using a socks proxy.  """
import os
import stat
import digitalocean
from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from random_words import RandomWords


def make_keys():
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=4096
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )
    rw = RandomWords()

    keyname = '_'.join(rw.random_words(count=4))
    keypath_pub = os.path.join('/tmp', keyname + '.pub')
    keypath_priv = os.path.join('/tmp', keyname + '.pem')
    with open(keypath_priv, 'wb') as privkeyfile:
        privkeyfile.write(private_key)
    os.chmod(keypath_priv, stat.S_IRUSR)
    with open(keypath_pub, 'wb') as pubkeyfile:
        pubkeyfile.write(public_key)

    return {
        'name': keyname,
        'public key': keypath_pub,
        'private key': keypath_priv
    }


def create_droplet(key):
    droplet = digitalocean.Droplet()


def main():
    ssh_key = make_keys()


if __name__ == '__main__':
    main()

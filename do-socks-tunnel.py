"""Not-so-simple script to initiate a digitalocean droplet and tunnel through
it using a socks proxy.  """
import os
import stat
import base64
import hashlib
import subprocess
import time
import digitalocean
from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from random_words import RandomWords


def make_keys(keyname):
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
    keypath_pub = os.path.join('/tmp', keyname + '.pub')
    keypath_priv = os.path.join('/tmp', keyname + '.pem')
    with open(keypath_priv, 'wb') as privkeyfile:
        privkeyfile.write(private_key)
    os.chmod(keypath_priv, stat.S_IRUSR)
    with open(keypath_pub, 'wb') as pubkeyfile:
        pubkeyfile.write(public_key)
    print(keyname)
    return {
        'name': keyname,
        'public key': keypath_pub,
        'private key': keypath_priv
    }


def upload_key(key_dict, login_token, manager):
    with open(key_dict['public key'], 'rb') as keyfile:
        user_ssh_key = keyfile.read().decode('utf-8')
    key = digitalocean.SSHKey(token=login_token,
                              name=key_dict['name'],
                              public_key=user_ssh_key,
                              )
    key.create()
    keys = manager.get_all_sshkeys()
    for key in keys:
        if key.name == key_dict['name']:
            return key.id


def create_droplet(dropname, sshkey_id, login_token, manager):
    droplet = digitalocean.Droplet(
        token=login_token,
        name=dropname,
        region='nyc3',
        image=17384153,
        size_slug='512mb',
        vcpus=1,
        ssh_keys=[sshkey_id],
        backups=False,
    )
    droplet.create()
    all_droplets = manager.get_all_droplets()
    for droplet in all_droplets:
        if droplet.name == dropname:
            return {
                'ipaddr': droplet.networks['v4'][0]['ip_address'],
                'id': droplet.id,
            }


def destroy_key(keyid, login_token):
    key = digitalocean.SSHKey(token=login_token,
                              id=keyid,
                              )
    key.destroy()


def destroy_droplet(dropid, login_token):
    droplet = digitalocean.Droplet(
        token=login_token,
        id=dropid,
    )
    droplet.destroy()
# def create_tunnel(privkeypath, ipaddr)


def cleanup(key_dict, dropid, login_token):
    destroy_droplet(dropid, login_token)
    destroy_key(key_dict['id'], login_token)
    os.remove(key_dict['private key'])
    os.remove(key_dict['public key'])


def main():
    rw = RandomWords()
    keyname = '_'.join(rw.random_words(count=4))
    dropname = '-'.join(rw.random_words(count=2))
    token = os.environ['DO_API_TOKEN']
    ssh_key = make_keys(keyname)
    manager = digitalocean.Manager(token=token)
    ssh_key['id'] = upload_key(ssh_key, token, manager)
    droplet = create_droplet(dropname, ssh_key['id'], token, manager)
    # subprocess.run(['ssh', '-i',
    #                 ssh_key['private key'],
    #                 'root@{}'.format(droplet['ipaddr'])])
    input('press enter to destroy the droplet')
    cleanup(ssh_key, droplet['id'], token)


if __name__ == '__main__':
    main()

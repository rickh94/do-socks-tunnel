"""A (not-so-)simple script to initiate a digitalocean droplet and tunnel
through it using a socks proxy."""
import atexit
import os
import stat
import subprocess
import signal
import time
import digitalocean
import random
from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from random_words import RandomWords


def make_keys(keyname):
    """Generate an ssh keypair.

    Arguments:
    keyname: the desired name for the key.
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=4096
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    )
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
    """Upload the key to Digital Ocean.

    Arguments:
    key_dict: the dict from key creation with paths to the keypair and its
    name.
    login_token: the token used for authentication.
    manager: a digitalocean.Manager instance for retrieving information from
    the api.
    """
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
    """Create the droplet with the ssh keys.

    Arguments:
    dropname: a name for the droplet
    sshkey_id: the internal id of the key reported by the api.
    login_token: the token used for authentication.
    manager: a digitalocean.Manager instance for retrieving information from
    the api.
    """
    droplet = digitalocean.Droplet(
        token=login_token,
        name=dropname,
        region='nyc3',
        image='ubuntu-16-04-x64',
        size_slug='512mb',
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
    """Remove the key from Digital Ocean.

    Arguments:
    keyid: the internal id of the key reported by the api.
    login_token: the token used for authentication.
    """
    key = digitalocean.SSHKey(token=login_token,
                              id=keyid,
                              )
    key.destroy()


def destroy_droplet(dropid, login_token):
    """Destroy the droplet.

    Arguments:
    dropid: the internal id of the droplet reported by the api.
    login_token: the token used for authentication.
    """
    droplet = digitalocean.Droplet(
        token=login_token,
        id=dropid,
    )
    droplet.destroy()


def clean_hosts(dropip):
    """Remove the droplet from the known_hosts file.

    Arguments:
    dropip: the ip address of the droplet.
    """
    subprocess.run(['ssh-keygen', '-R', dropip])


def rm_key(key_dict):
    """Delete the generated keys.

    Arguments:
    key_dict: dict returned by key creation with paths to keypair.
    """
    os.remove(key_dict['private key'])
    os.remove(key_dict['public key'])


def kill_ssh(ssh_cmd):
    """Kill the ssh command.

    Arguments:
    ssh_cmd: list of the ssh command and arguments as passed to subprocess.
    """
    pid = subprocess.check_output(['pgrep', '-f', ' '.join(ssh_cmd)])
    os.killpg(int(pid), signal.SIGTERM)


def main():
    """The main function."""
    # setup
    rw = RandomWords()
    keyname = '_'.join(rw.random_words(count=4))
    dropname = '-'.join(rw.random_words(count=2))
    token = os.environ['DO_API_TOKEN']
    manager = digitalocean.Manager(token=token)
    portnum = random.randrange(1025, 65536)

    ssh_key = make_keys(keyname)
    atexit.register(rm_key, ssh_key)

    ssh_key['id'] = upload_key(ssh_key, token, manager)
    atexit.register(destroy_key, ssh_key['id'], token)

    print('Creating Droplet...', end='')
    droplet = create_droplet(dropname, ssh_key['id'], token, manager)
    atexit.register(destroy_droplet, droplet['id'], token)
    print('Droplet Created')
    time.sleep(5)

    print("Connecting to Droplet. This could take a moment.")
    time.sleep(30)
    ssh_cmd = ['ssh',
               '-o', 'IdentitiesOnly=yes',
               '-o', 'StrictHostKeyChecking=no',
               '-i', ssh_key['private key'],
               '-N',
               '-C',
               '-f',
               '-D', str(portnum),
               'root@{}'.format(droplet['ipaddr'])]
    run_ssh = subprocess.run(ssh_cmd)
    atexit.register(kill_ssh, ssh_cmd)
    atexit.register(clean_hosts, droplet['ipaddr'])

    print('port number: {}'.format(portnum))
    input('press enter to destroy the droplet and disconnect')


if __name__ == '__main__':
    main()

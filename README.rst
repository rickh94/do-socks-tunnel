Digital Ocean Socks Tunnel
==========================
A script to initialize a socks tunnel through a digital ocean droplet
on-the-fly to have a secure connection over a potentially insecure network.

Installation
============
For now
::

$ git clone https://github.com/rickh94/do-socks-tunnel.git
$ python setup.py install


SOON:
``$ pip install --user do-socks-tunnel``

You need:

* OpenSSH installed on your system.

* You will also need a `Digital Ocean <https://digitalocean.com>`_ account and
  API token. (You can `generate one here
  <https://cloud.digitalocean.com/settings/api/tokens>`_).

* A browser or system that can be configured to use socks5 proxy (chrome and
  firefox both support this in different ways).

* The ``pgrep`` utility (comes with most linux distros). It is used
  to kill the forked ssh command.

You do NOT need:

* A VPN

* A 24/7 server


Usage
=====
Export your Digital Ocean API authentication token to your environment [1]_ it
under the name ``DO_API_TOKEN``:

``$ export DO_API_TOKEN='mytoken'``

Then run ``$ do-socks-tunnel`` to create a tunneled connection using openssh.
It will print the port number to stdout. Then just send all your traffic
through localhost:portnumber to have your traffic encrypted.
It is important to keep the originating terminal open (or run the script as a
daemon with something like systemd) as long as you want to have your tunnel
open. It is also important that the script exits cleanly so the cleanup
script is run.


Under the hood
==============
Each run generates a new ssh key pair (using the python cryptography
library), adds the public key to your digital ocean account, then instantiates a new droplet using
that key (no other keys in your account will have access). The keys are
stored on the file system in ``/tmp``.
Once everything is created, it will run ssh in the background to create the
tunnel on a random port between 1025 and 65536.
When you exit the script, the keys are deleted from the disk and your
account and the droplet is destroyed and removed from your known hosts file.
The point of this is to keep things secure and clean on your system and in
the cloud.

Defaults
========
The default configuration is currently hard-coded and is as follows\:

* Droplet

  - name: two random words as word1-word2

  - region: nyc3

  - image: ubuntu-16-04-x64

  - size slug: 512mb (1 CPU, 512MB RAM, 20GB Disk)

  - ssh_keys: on-the-fly generated key

  - no backups

* Keys

  - name: four random words as word1\_word2\_word3\_word4(.pem,.pub).

  - protocol: RSA

  - size: 4096 bits

TODO
====
* BUG: fix auto-killing of ssh command.

* BUG: sometimes ssh connection is refused. timing?

* Add support for command line configuration of any of the above options
  (but still running the default config when run without).

* Add support for alternate configuration in a config file.

* Auto-configure NetworkManager, Firefox, shell environments, git, where
  possible.

.. [1] If you would like to avoid storing the token in the clear, check out
   `pass <https://www.passwordstore.org>`_. Store the token in pass and put
   ``export DO_API_TOKEN=$(pass show digitalocean_token)`` in your shell rc
   file.


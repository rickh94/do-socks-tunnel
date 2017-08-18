"""Tests for dosockstunnel."""
import os
import stat
import unittest
from unittest import mock
import dosockstunnel
import digitalocean


class FakeKey(object):
    """A fake Digital Ocean Key object."""
    def __init__(self):
        self.name = 'testkey'
        self.id = '123456'


class TestKeys(unittest.TestCase):
    """Test all the ssh key related functions."""
    def setUp(self):
        self.key_dict_paths_only = {
            'name': 'testkey',
            'public key': '/tmp/testkey.pub',
            'private key': '/tmp/testkey.pem',
        }
        self.key_dict_with_id = self.key_dict_paths_only.copy()
        self.key_dict_with_id['id'] = '123456'

    @mock.patch('dosockstunnel.os.chmod')
    def test_make_keys(self, mock_chmod):
        """Test key creation and saving."""
        self.assertEqual(
            dosockstunnel.make_keys('testkey'),
            self.key_dict_paths_only
        )
        mock_chmod.assert_called_once_with('/tmp/testkey.pem', stat.S_IRUSR)
        with open('/tmp/testkey.pub', 'r') as pubfile:
            assert 'ssh-rsa' in pubfile.read()
        with open('/tmp/testkey.pem', 'r') as privfile:
            assert '-----BEGIN PRIVATE KEY-----' in privfile.read()
        os.remove('/tmp/testkey.pem')
        os.remove('/tmp/testkey.pub')

    @mock.patch('builtins.open')
    @mock.patch('dosockstunnel.digitalocean')
    def test_upload_key(self, mock_do, mock_open):
        """Test uploading the key to do an returning the id."""
        mock_open.return_value = mock.MagicMock()
        mock_do.SSHKey.return_value = mock.MagicMock(spec=digitalocean.SSHKey)
        mock_manager = mock.MagicMock()
        mock_manager.get_all_sshkeys.return_value = [FakeKey()]
        self.assertEqual(
            dosockstunnel.upload_key(self.key_dict_paths_only,
                                     'faketoken',
                                     mock_manager
                                     ),
            '123456'
        )
        mock_do.SSHKey.assert_called_once_with(
            token='faketoken',
            name=self.key_dict_paths_only['name'],
            public_key=mock.ANY,
        )

    @mock.patch('dosockstunnel.digitalocean')
    def test_destroy_key(self, mock_do):
        """Test removing the key from DO."""
        instance = mock_do.SSHKey.return_value
        dosockstunnel.destroy_key(self.key_dict_with_id['id'], 'faketoken')
        mock_do.SSHKey.assert_called_once_with(token='faketoken',
                                               id=self.key_dict_with_id['id']
                                               )
        instance.destroy.assert_called_once_with()

    @mock.patch('dosockstunnel.os.remove')
    def test_rm_key(self, mock_remove):
        """Test deletion of keys from the client disk."""
        dosockstunnel.rm_key(self.key_dict_with_id)
        mock_remove.assert_any_call('/tmp/testkey.pub')
        mock_remove.assert_any_call('/tmp/testkey.pem')


class FakeDroplet(object):
    """A fake droplet."""
    def __init__(self):
        self.name = 'testdroplet'
        self.id = '999999'
        self.networks = {'v4': [{}]}
        self.networks['v4'][0]['ip_address'] = '192.168.1.100'


@mock.patch('dosockstunnel.digitalocean')
class TestDroplet(unittest.TestCase):
    """test droplet related functions."""
    def test_create_droplet(self, mock_do):
        """Test droplet creation."""
        mock_manager = mock.MagicMock()
        droplet_instance = mock_do.Droplet.return_value
        mock_manager.get_all_droplets.return_value = [FakeDroplet()]
        self.assertEqual(
            dosockstunnel.create_droplet('testdroplet',
                                         '123456',
                                         'faketoken',
                                         mock_manager
                                         ),
            {
                'ipaddr': '192.168.1.100',
                'id': '999999'
            }
        )
        mock_do.Droplet.assert_called_once_with(
            token='faketoken',
            name='testdroplet',
            region='nyc3',
            image='ubuntu-16-04-x64',
            size_slug='512mb',
            ssh_keys=['123456'],
            backups=False,
        )
        droplet_instance.create.assert_called_once_with()

    def test_destroy_droplet(self, mock_do):
        """Test droplet destruction."""
        droplet_instance = mock_do.Droplet.return_value
        dosockstunnel.destroy_droplet('999999', 'faketoken')
        mock_do.Droplet.assert_called_once_with(
            token='faketoken',
            id='999999'
        )
        droplet_instance.destroy.assert_called_once_with()

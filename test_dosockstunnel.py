"""Tests for dosockstunnel."""
import os
import stat
import unittest
from unittest import mock
import dosockstunnel


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

    # def test_upload_key(self, mock_do, mock_manager):

# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""This module contains tests for bodhi.client.bindings."""
from datetime import datetime, timedelta
import copy
import unittest

import fedora.client
import mock

from bodhi.client import bindings
from bodhi.tests import client as client_test_data


class TestBodhiClient___init__(unittest.TestCase):
    """
    This class contains tests for the BodhiClient.__init__() method.
    """
    def test_base_url_not_ends_in_slash(self):
        """
        If the base_url doesn't end in a slash, __init__() should append one.
        """
        client = bindings.BodhiClient(base_url='http://localhost:6543')

        self.assertEqual(client.base_url, 'http://localhost:6543/')

    def test_staging_false(self):
        """
        Test with staging set to False.
        """
        client = bindings.BodhiClient(base_url='http://example.com/bodhi/', username='some_user',
                                      password='s3kr3t', staging=False, timeout=60)

        self.assertEqual(client.base_url, 'http://example.com/bodhi/')
        self.assertEqual(client.login_url, 'http://example.com/bodhi/login')
        self.assertEqual(client.username, 'some_user')
        self.assertEqual(client.timeout, 60)
        self.assertEqual(client._password, 's3kr3t')
        self.assertEqual(client.csrf_token, None)

    def test_staging_true(self):
        """
        Test with staging set to True.
        """
        client = bindings.BodhiClient(base_url='http://example.com/bodhi/', username='some_user',
                                      password='s3kr3t', staging=True, retries=5)

        self.assertEqual(client.base_url, bindings.STG_BASE_URL)
        self.assertEqual(client.login_url, bindings.STG_BASE_URL + 'login')
        self.assertEqual(client.username, 'some_user')
        self.assertEqual(client.timeout, None)
        self.assertEqual(client.retries, 5)
        self.assertEqual(client._password, 's3kr3t')
        self.assertEqual(client.csrf_token, None)


class TestBodhiClient_comment(unittest.TestCase):
    """
    Test the BodhiClient.comment() method.
    """
    def test_comment(self):
        """
        Test the comment() method.
        """
        client = bindings.BodhiClient()
        client.csrf_token = 'a token'
        client.send_request = mock.MagicMock(return_value='response')

        response = client.comment('bodhi-2.4.0-1.fc25', 'It ate my cat!', karma=-1, email=True)

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with(
            'comments/', verb='POST', auth=True,
            data={'update': 'bodhi-2.4.0-1.fc25', 'text': 'It ate my cat!', 'karma': -1,
                  'email': True, 'csrf_token': 'a token'})


class TestBodhiClient_init_username(unittest.TestCase):
    """Test the BodhiClient.init_username() method."""
    TEST_EMPTY_OBJECT_SESSION_CACHE = '{}'
    TEST_FAILED_SESSION_CACHE = '{"https://bodhi.fedoraproject.org/:bowlofeggs": []}'
    TEST_HOT_SESSION_CACHE = '{"https://bodhi.fedoraproject.org/:bowlofeggs": [["stuff", "login"]]}'
    TEST_OTHER_SESSION_CACHE = '{"https://other_domain/:bowlofeggs": [["stuff", "login"]]}'

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_empty(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        is 0 bytes.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(read_data='')
        mock_raw_input.return_value = 'pongou'
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 1)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'pongou')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_empty_object(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        is an empty object.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(read_data=self.TEST_EMPTY_OBJECT_SESSION_CACHE)
        mock_raw_input.return_value = 'pongou'
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 1)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'pongou')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_failed(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        is missing the cookies.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(read_data=self.TEST_FAILED_SESSION_CACHE)
        mock_raw_input.return_value = 'pongou'
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 1)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'pongou')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_hot(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        has cookies.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(read_data=self.TEST_HOT_SESSION_CACHE)
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 0)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'bowlofeggs')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.json.loads')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_loop(self, exists, loads, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        has cookies but iteration is needed to find them.
        """
        def fake_keys():
            return [
                'http://wrong_host:wrong', 'also:wrong',
                'https://bodhi.fedoraproject.org/:correct',
                'https://bodhi.fedoraproject.org/:shouldntgethere']

        exists.return_value = True
        loads.return_value.keys.side_effect = fake_keys
        mock_open.side_effect = mock.mock_open(read_data=self.TEST_HOT_SESSION_CACHE)
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        loads.assert_called_once_with(self.TEST_HOT_SESSION_CACHE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 0)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'correct')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_missing(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username and the session cache doesn't exist.
        """
        exists.return_value = False
        mock_raw_input.return_value = 'pongou'
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 1)
        self.assertEqual(mock_open.call_count, 0)
        self.assertEqual(client.username, 'pongou')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_auth_cache_other_domain(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when there is no username, the session cache exists, and the session cache
        has cookies but they are for a different domain.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(read_data=self.TEST_OTHER_SESSION_CACHE)
        mock_raw_input.return_value = 'pongou'
        client = bindings.BodhiClient()

        client.init_username()

        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 1)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'pongou')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_username_set(self, exists, _load_cookies, mock_raw_input, mock_open):
        """
        Test the method when the username is set.
        """
        client = bindings.BodhiClient(username='coolbeans')

        client.init_username()

        self.assertEqual(exists.call_count, 0)
        self.assertEqual(_load_cookies.mock_calls, [mock.call()])
        self.assertEqual(mock_raw_input.call_count, 0)
        self.assertEqual(mock_open.call_count, 0)
        self.assertEqual(client.username, 'coolbeans')


class TestBodhiClient_csrf(unittest.TestCase):
    """
    Test the BodhiClient.csrf() method.
    """
    @mock.patch('bodhi.client.bindings.BodhiClient.init_username')
    def test_with_csrf_token(self, init_username):
        """
        Test the method when csrf_token is set.
        """
        client = bindings.BodhiClient()
        client.csrf_token = 'a token'
        client.send_request = mock.MagicMock(return_value='response')

        csrf = client.csrf()

        self.assertEqual(csrf, 'a token')
        self.assertEqual(client.send_request.call_count, 0)
        # No need to init the username since we already have a token.
        self.assertEqual(init_username.call_count, 0)

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_without_csrf_token_with_cookies(self, exists, _load_cookies, mock_raw_input,
                                             mock_open):
        """
        Test the method when csrf_token is not set and has_cookies() returns True.
        """
        exists.return_value = True
        mock_open.side_effect = mock.mock_open(
            read_data=TestBodhiClient_init_username.TEST_HOT_SESSION_CACHE)
        client = bindings.BodhiClient()
        client.has_cookies = mock.MagicMock(return_value=True)
        client.login = mock.MagicMock(return_value='login successful')
        client.send_request = mock.MagicMock(return_value={'csrf_token': 'a great token'})

        csrf = client.csrf()

        self.assertEqual(csrf, 'a great token')
        self.assertEqual(client.csrf_token, 'a great token')
        client.has_cookies.assert_called_once_with()
        self.assertEqual(client.login.call_count, 0)
        client.send_request.assert_called_once_with('csrf', verb='GET', auth=True)
        # Ensure that init_username() was called and did its thing.
        exists.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(_load_cookies.mock_calls, [mock.call(), mock.call()])
        self.assertEqual(mock_raw_input.call_count, 0)
        mock_open.assert_called_once_with(fedora.client.openidbaseclient.b_SESSION_FILE)
        self.assertEqual(client.username, 'bowlofeggs')

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('__builtin__.raw_input', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_without_csrf_token_without_cookies(self, exists, _load_cookies, mock_raw_input,
                                                mock_open):
        """
        Test the method when csrf_token is not set and has_cookies() returns False.
        """
        client = bindings.BodhiClient(username='pongou', password='illnevertell')
        client.has_cookies = mock.MagicMock(return_value=False)
        client.login = mock.MagicMock(return_value='login successful')
        client.send_request = mock.MagicMock(return_value={'csrf_token': 'a great token'})

        csrf = client.csrf()

        self.assertEqual(csrf, 'a great token')
        self.assertEqual(client.csrf_token, 'a great token')
        client.has_cookies.assert_called_once_with()
        client.login.assert_called_once_with('pongou', 'illnevertell')
        client.send_request.assert_called_once_with('csrf', verb='GET', auth=True)
        # Ensure that init_username() didn't do anything since a username was given.
        self.assertEqual(exists.call_count, 0)
        self.assertEqual(_load_cookies.mock_calls, [mock.call()])
        self.assertEqual(mock_raw_input.call_count, 0)
        self.assertEqual(mock_open.call_count, 0)
        self.assertEqual(client.username, 'pongou')


class TestBodhiClient_latest_builds(unittest.TestCase):
    """
    Test the BodhiClient.latest_builds() method.
    """
    def test_latest_builds(self):
        """
        Test latest_builds().
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='bodhi-2.4.0-1.fc25')

        latest_builds = client.latest_builds('bodhi')

        self.assertEqual(latest_builds, 'bodhi-2.4.0-1.fc25')
        client.send_request.assert_called_once_with('latest_builds', params={'package': 'bodhi'})


class TestBodhiClient_list_overrides(unittest.TestCase):
    """
    Test the BodhiClient.list_overrides() method.
    """
    def test_with_user(self):
        """
        Test with the user parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(user='bowlofeggs')

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'user': 'bowlofeggs'})

    def test_without_parameters(self):
        """
        Test without the parameters.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides()

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET', params={})

    def test_with_package(self):
        """
        Test with the package parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(packages='bodhi')

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'packages': 'bodhi'})

    def test_with_expired(self):
        """
        Test --expired with the expired/active click boolean parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(expired=True)

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'expired': True})

    def test_with_active(self):
        """
        Test --active with the expired/active click boolean parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(expired=False)

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'expired': False})

    def test_with_releases(self):
        """
        Test with the releases parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(releases='F24')

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'releases': 'F24'})

    def test_with_builds(self):
        """
        Test with the builds parameter.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='response')

        response = client.list_overrides(builds='python-1.5.6-3.fc26')

        self.assertEqual(response, 'response')
        client.send_request.assert_called_once_with('overrides/', verb='GET',
                                                    params={'builds': 'python-1.5.6-3.fc26'})


class TestBodhiClient_override_str(unittest.TestCase):
    """
    Test the BodhiClient.override_str() method.
    """
    def test_with_min_dict(self):
        """
        Test override_str() with a dict argument and minimal set to true.
        """
        override = {
            'submitter': {'name': 'bowlofeggs'}, 'build': {'nvr': 'python-pyramid-1.5.6-3.el7'},
            'expiration_date': '2017-02-24'}

        override = bindings.BodhiClient.override_str(override)

        self.assertEqual(override,
                         "bowlofeggs's python-pyramid-1.5.6-3.el7 override (expires 2017-02-24)")

    def test_with_dict(self):
        """
        Test override_str() with a dict argument.
        """
        override = {
            'submitter': {'name': 'bowlofeggs'}, 'build': {'nvr': 'js-tag-it-2.0-1.fc25'},
            'expiration_date': '2017-03-07 23:05:31', 'notes': 'No explanation given...',
            'expired_date': None}

        override = bindings.BodhiClient.override_str(override, minimal=False)

        self.assertEqual(override, client_test_data.EXPECTED_OVERRIDES_OUTPUT.rstrip())

    def test_with_str(self):
        """
        Test override_str() with a str argument.
        """
        override = bindings.BodhiClient.override_str('this is an override')

        self.assertEqual(override, 'this is an override')


class TestBodhiClient_password(unittest.TestCase):
    """
    This class contains tests for the BodhiClient.password property.
    """
    @mock.patch('bodhi.client.bindings.getpass.getpass', return_value='typed password')
    def test_password_not_set(self, getpass):
        """
        Assert correct behavior when the _password attribute is not set.
        """
        client = bindings.BodhiClient()

        self.assertEqual(client.password, 'typed password')

        getpass.assert_called_once_with()

    @mock.patch('bodhi.client.bindings.getpass.getpass', return_value='typed password')
    def test_password_set(self, getpass):
        """
        Assert correct behavior when the _password attribute is set.
        """
        client = bindings.BodhiClient(password='arg password')

        self.assertEqual(client.password, 'arg password')

        self.assertEqual(getpass.call_count, 0)


class TestBodhiClient_query(unittest.TestCase):
    """
    Test BodhiClient.query().
    """
    def test_with_bugs_empty_string(self):
        """
        Test with the bugs kwargs set to an empty string.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(builds='bodhi-2.4.0-1.fc26', bugs='')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'builds': 'bodhi-2.4.0-1.fc26', 'bugs': None})

    def test_with_limit(self):
        """
        Assert that the limit kwargs gets translated to rows_per_page correctly.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(builds='bodhi-2.4.0-1.fc26', limit=50)

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'builds': 'bodhi-2.4.0-1.fc26', 'rows_per_page': 50})

    def test_with_mine_false(self):
        """
        Assert correct behavior when the mine kwargs is False.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(builds='bodhi-2.4.0-1.fc26', mine=False)

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'builds': 'bodhi-2.4.0-1.fc26', 'mine': False})

    def test_with_mine_true(self):
        """
        Assert correct behavior when the mine kwargs is True.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')
        client.username = 'bowlofeggs'

        result = client.query(builds='bodhi-2.4.0-1.fc26', mine=True)

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET',
            params={'builds': 'bodhi-2.4.0-1.fc26', 'mine': True, 'user': 'bowlofeggs'})

    def test_with_package_el_build(self):
        """
        Test with the package arg expressed as an el7 build.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(package='bodhi-2.4.0-1.el7')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'builds': 'bodhi-2.4.0-1.el7'})

    def test_with_package_epel_id(self):
        """
        Test with the package arg expressed as a EPEL update id.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(package='FEDORA-EPEL-2017-c3b112eb9e')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'updateid': 'FEDORA-EPEL-2017-c3b112eb9e'})

    def test_with_package_fc_build(self):
        """
        Test with the package arg expressed as a fc26 build.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(package='bodhi-2.4.0-1.fc26')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'builds': 'bodhi-2.4.0-1.fc26'})

    def test_with_package_fedora_id(self):
        """
        Test with the package arg expressed as a Fedora update id.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(package='FEDORA-2017-52506b30d4')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'updateid': 'FEDORA-2017-52506b30d4'})

    def test_with_package_name(self):
        """
        Test with the package arg expressed as a package name.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(package='bodhi')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'packages': 'bodhi'})

    def test_with_release_list(self):
        """
        Test with a 'release' kwarg set to a list.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(packages='bodhi', release=['f27'])

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'packages': 'bodhi', 'releases': ['f27']})

    def test_with_release_str(self):
        """
        Test with a 'release' kwarg set to a str.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(packages='bodhi', release='f26')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'packages': 'bodhi', 'releases': ['f26']})

    def test_with_type_(self):
        """
        Test with the type_ kwarg.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')

        result = client.query(packages='bodhi', type_='security')

        self.assertEqual(result, 'return_value')
        client.send_request.assert_called_once_with(
            'updates/', verb='GET', params={'packages': 'bodhi', 'type': 'security'})


class TestBodhiClient_save(unittest.TestCase):
    """
    This class contains tests for BodhiClient.save().
    """
    def test_with_type_(self):
        """
        Assert that save() handles type_ as a kwargs for backwards compatibility.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')
        client.csrf_token = 'a token'
        kwargs = {
            'builds': ['bodhi-2.4.0-1.fc26'], 'type_': 'enhancement', 'notes': 'This is a test',
            'request': 'testing', 'autokarma': True, 'stable_karma': 3, 'unstable_karma': -3,
            'severity': 'low'}

        response = client.save(**kwargs)

        self.assertEqual(response, 'return_value')
        kwargs['type'] = kwargs['type_']
        kwargs['csrf_token'] = 'a token'
        client.send_request.assert_called_once_with('updates/', verb='POST', auth=True, data=kwargs)

    def test_without_type_(self):
        """
        Assert correct operation when type_ isn't given.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')
        client.csrf_token = 'a token'
        kwargs = {
            'builds': ['bodhi-2.4.0-1.fc26'], 'type': 'enhancement', 'notes': 'This is a test',
            'request': 'testing', 'autokarma': True, 'stable_karma': 3, 'unstable_karma': -3,
            'severity': 'low'}

        response = client.save(**kwargs)

        self.assertEqual(response, 'return_value')
        kwargs['csrf_token'] = 'a token'
        client.send_request.assert_called_once_with('updates/', verb='POST', auth=True, data=kwargs)


class TestBodhiClient_save_override(unittest.TestCase):
    """
    This class contains tests for BodhiClient.save_override().
    """
    def test_save_override(self):
        """
        Test the save_override() method.
        """
        client = bindings.BodhiClient()
        client.send_request = mock.MagicMock(return_value='return_value')
        client.csrf_token = 'a token'
        now = datetime.utcnow()
        response = client.save_override(nvr='python-pyramid-1.5.6-3.el7',
                                        duration=2,
                                        notes='This is needed to build bodhi-2.4.0.')

        self.assertEqual(response, 'return_value')
        actual_expiration = client.send_request.mock_calls[0][2]['data']['expiration_date']
        client.send_request.assert_called_once_with(
            'overrides/', verb='POST', auth=True,
            data={'nvr': 'python-pyramid-1.5.6-3.el7',
                  'expiration_date': actual_expiration,
                  'csrf_token': 'a token', 'notes': 'This is needed to build bodhi-2.4.0.'})
        # Since we can't mock utcnow() since it's a C extension, let's just make sure the expiration
        # date sent is within 5 minutes of the now variable. It would be surprising if it took more
        # than 5 minutes to start the function and execute its first instruction!
        expected_expiration = now + timedelta(days=2)
        self.assertTrue((actual_expiration - expected_expiration) < timedelta(minutes=5))


class TestBodhiClient_request(unittest.TestCase):
    """
    This class contains tests for BodhiClient.request().
    """
    @mock.patch('bodhi.client.bindings.BodhiClient.__init__', return_value=None)
    @mock.patch.object(bindings.BodhiClient, 'base_url', 'http://example.com/tests/',
                       create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient.csrf',
                mock.MagicMock(return_value='a_csrf_token'))
    @mock.patch('bodhi.client.bindings.BodhiClient.send_request',
                side_effect=fedora.client.ServerError(
                    url='http://example.com/tests/updates/bodhi-2.2.4-99.el7/request', status=404,
                    msg='update not found'))
    def test_404_error(self, send_request, __init__):
        """
        Test for the case when the server returns a 404 error code.
        """
        client = bindings.BodhiClient(username='some_user', password='s3kr3t', staging=False)

        with self.assertRaises(bindings.UpdateNotFound) as exc:
            client.request('bodhi-2.2.4-1.el7', 'revoke')

            self.assertEqual(exc.update, 'bodhi-2.2.4-1.el7')

        send_request.assert_called_once_with(
            'updates/bodhi-2.2.4-1.el7/request', verb='POST', auth=True,
            data={'csrf_token': 'a_csrf_token', 'request': u'revoke',
                  'update': u'bodhi-2.2.4-1.el7'})
        __init__.assert_called_once_with(username='some_user', password='s3kr3t', staging=False)

    @mock.patch('bodhi.client.bindings.BodhiClient.__init__', return_value=None)
    @mock.patch.object(bindings.BodhiClient, 'base_url', 'http://example.com/tests/',
                       create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient.csrf',
                mock.MagicMock(return_value='a_csrf_token'))
    @mock.patch('bodhi.client.bindings.BodhiClient.send_request',
                return_value=client_test_data.EXAMPLE_UPDATE_MUNCH)
    def test_successful_request(self, send_request, __init__):
        """
        Test with a successful request.
        """
        client = bindings.BodhiClient(username='some_user', password='s3kr3t', staging=False)

        response = client.request('bodhi-2.2.4-1.el7', 'revoke')

        self.assertEqual(response, client_test_data.EXAMPLE_UPDATE_MUNCH)
        send_request.assert_called_once_with(
            'updates/bodhi-2.2.4-1.el7/request', verb='POST', auth=True,
            data={'csrf_token': 'a_csrf_token', 'request': u'revoke',
                  'update': u'bodhi-2.2.4-1.el7'})
        __init__.assert_called_once_with(username='some_user', password='s3kr3t', staging=False)

    @mock.patch('bodhi.client.bindings.BodhiClient.__init__', return_value=None)
    @mock.patch.object(bindings.BodhiClient, 'base_url', 'http://example.com/tests/',
                       create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient.csrf',
                mock.MagicMock(return_value='a_csrf_token'))
    @mock.patch('bodhi.client.bindings.BodhiClient.send_request')
    def test_other_ServerError(self, send_request, __init__):
        """
        Test for the case when a non-404 ServerError is raised.
        """
        server_error = fedora.client.ServerError(
            url='http://example.com/tests/updates/bodhi-2.2.4-99.el7/request', status=500,
            msg='Internal server error')
        send_request.side_effect = server_error
        client = bindings.BodhiClient(username='some_user', password='s3kr3t', staging=False)

        with self.assertRaises(fedora.client.ServerError) as exc:
            client.request('bodhi-2.2.4-1.el7', 'revoke')

            self.assertTrue(exc is server_error)

        send_request.assert_called_once_with(
            'updates/bodhi-2.2.4-1.el7/request', verb='POST', auth=True,
            data={'csrf_token': 'a_csrf_token', 'request': u'revoke',
                  'update': u'bodhi-2.2.4-1.el7'})
        __init__.assert_called_once_with(username='some_user', password='s3kr3t', staging=False)


class TestBodhiClient_update_str(unittest.TestCase):
    """This test contains tests for BodhiClient.update_str."""
    @mock.patch.dict(
        client_test_data.EXAMPLE_UPDATE_MUNCH,
        {'bugs': [{'bug_id': 1234, 'title': 'it broke'}, {'bug_id': 1235, 'title': 'halp'}]})
    def test_bugs(self):
        """Ensure correct output when there are bugs on the update."""
        client = bindings.BodhiClient()
        client.base_url = 'http://example.com/tests/'

        text = client.update_str(client_test_data.EXAMPLE_UPDATE_MUNCH)

        self.assertEqual(
            text,
            client_test_data.EXPECTED_UPDATE_OUTPUT.replace(
                '[-3, 3]', '[-3, 3]\n        Bugs: 1234 - it broke\n            : 1235 - halp'))

    def test_minimal(self):
        """Ensure correct output when minimal is True."""
        client = bindings.BodhiClient()

        text = client.update_str(client_test_data.EXAMPLE_UPDATE_MUNCH, minimal=True)

        expected_output = (' bodhi-2.2.4-1.el7                     rpm    bugfix       stable    '
                           '2016-10-21')
        self.assertEqual(text, expected_output)

    @mock.patch.dict(client_test_data.EXAMPLE_UPDATE_MUNCH, {'request': 'stable'})
    def test_request_stable(self):
        """Ensure correct output when the update is request stable."""
        client = bindings.BodhiClient()
        client.base_url = 'http://example.com/tests/'

        text = client.update_str(client_test_data.EXAMPLE_UPDATE_MUNCH)

        self.assertEqual(
            text,
            client_test_data.EXPECTED_UPDATE_OUTPUT.replace(
                '[-3, 3]', '[-3, 3]\n     Request: stable'))

    def test_with_autokarma_set(self):
        """
        Ensure correct operation when autokarma is True, and stable/unstable karmas are set.
        """
        client = bindings.BodhiClient(username='some_user', password='s3kr3t')
        client.base_url = 'http://example.com/tests/'

        text = client.update_str(client_test_data.EXAMPLE_UPDATE_MUNCH)

        self.assertEqual(text, client_test_data.EXPECTED_UPDATE_OUTPUT)

    def test_with_autokarma_unset(self):
        """
        Ensure correct operation when autokarma is Fale, and stable/unstable karmas are None.
        """
        client = bindings.BodhiClient(username='some_user', password='s3kr3t')
        client.base_url = 'http://example.com/tests/'
        update = copy.deepcopy(client_test_data.EXAMPLE_UPDATE_MUNCH)
        # Set the update's autokarma and thresholds to False/None.
        update.autokarma = False
        update.unstable_karma = None
        update.stable_karma = None

        text = client.update_str(update)

        self.maxDiff = None
        expected_output = client_test_data.EXPECTED_UPDATE_OUTPUT.replace(
            'Autokarma: True  [-3, 3]', 'Autokarma: False  [None, None]')
        self.assertEqual(text, expected_output)


class TestErrorhandled(unittest.TestCase):
    """
    This class tests the errorhandled decorator.
    """
    def test_failure_with_given_errors(self):
        """
        Test the failure case for when errors were given in the response.
        """
        @bindings.errorhandled
        def im_gonna_fail_but_ill_be_cool_about_it(x, y, z=None):
            self.assertEqual(x, 1)
            self.assertEqual(y, 2)
            self.assertEqual(z, 3)

            return {'errors': [{'description': 'insert'}, {'description': 'coin(s)'}]}

        with self.assertRaises(bindings.BodhiClientException) as exc:
            im_gonna_fail_but_ill_be_cool_about_it(1, y=2, z=3)

        self.assertEqual(str(exc.exception), 'insert\ncoin(s)')

    def test_retry_on_auth_failure_failure(self):
        """
        Test the decorator when the wrapped method raises an AuthError the second time it is run.

        This test ensures that the decorator will give up after one retry if the wrapped method
        raises a fedora.client.AuthError, raising the AuthError in question.

        This test was written to assert the fix for
        https://github.com/fedora-infra/bodhi/issues/1474
        """
        a_fake_self = mock.MagicMock()
        a_fake_self.csrf_token = 'some_token'
        a_fake_self.call_count = 0

        @bindings.errorhandled
        def wrong_password_lol(a_fake_self):
            a_fake_self.call_count = a_fake_self.call_count + 1
            raise fedora.client.AuthError('wrong password lol')

        with self.assertRaises(fedora.client.AuthError) as exc:
            # Wrong password always fails, so the second call should allow the Exception to be
            # raised.
            wrong_password_lol(a_fake_self)

        self.assertEqual(str(exc.exception), 'wrong password lol')
        a_fake_self._session.cookies.clear.assert_called_once_with()
        self.assertTrue(a_fake_self.csrf_token is None)
        self.assertEqual(a_fake_self.call_count, 2)

    def test_retry_on_auth_failure_success(self):
        """
        Test the decorator when the wrapped method raises an AuthError the first time it is run.

        This test ensures that the decorator will retry the wrapped method if it raises a
        fedora.client.AuthError, after clearing cookies and the csrf token.

        This test was written to assert the fix for
        https://github.com/fedora-infra/bodhi/issues/1474
        """
        a_fake_self = mock.MagicMock()
        a_fake_self.csrf_token = 'some_token'
        a_fake_self.call_count = 0

        @bindings.errorhandled
        def wrong_password_lol(a_fake_self):
            a_fake_self.call_count = a_fake_self.call_count + 1

            # Fail on the first call with an AuthError to simulate bad session cookies.
            if a_fake_self.call_count == 1:
                raise fedora.client.AuthError('wrong password lol')

            return 'here you go'

        # No Exception should be raised.
        wrong_password_lol(a_fake_self)

        a_fake_self._session.cookies.clear.assert_called_once_with()
        self.assertTrue(a_fake_self.csrf_token is None)
        self.assertEqual(a_fake_self.call_count, 2)

    def test_success(self):
        """
        Test the decorator for the success case.
        """
        @bindings.errorhandled
        def im_gonna_be_cool(x, y, z=None):
            self.assertEqual(x, 1)
            self.assertEqual(y, 2)
            self.assertEqual(z, 3)

            return 'here you go'

        self.assertEqual(im_gonna_be_cool(1, 2, 3), 'here you go')

    def test_unexpected_error(self):
        """
        Test the failure case when errors are not given in the response.
        """
        @bindings.errorhandled
        def im_gonna_fail_and_i_wont_be_cool_about_it(x, y, z=None):
            self.assertEqual(x, 1)
            self.assertEqual(y, 2)
            self.assertEqual(z, 3)

            return {'errors': ['MEAN ERROR']}

        with self.assertRaises(bindings.BodhiClientException) as exc:
            im_gonna_fail_and_i_wont_be_cool_about_it(1, 2, z=3)

        self.assertEqual(str(exc.exception), 'An unhandled error occurred in the BodhiClient')


class TestUpdateNotFound(unittest.TestCase):
    """
    This class tests the UpdateNotFound class.
    """
    def test___init__(self):
        """
        Assert that __init__() works properly.
        """
        exc = bindings.UpdateNotFound('bodhi-2.2.4-1.el7')

        self.assertEqual(exc.update, u'bodhi-2.2.4-1.el7')
        self.assertEqual(type(exc.update), unicode)

    def test___unicode__(self):
        """
        Assert that __unicode__() works properly.
        """
        exc = bindings.UpdateNotFound('bodhi-2.2.4-1.el7')

        self.assertEqual(unicode(exc.update), u'bodhi-2.2.4-1.el7')
        self.assertEqual(type(unicode(exc.update)), unicode)
        self.assertEqual(unicode(exc), 'Update not found: bodhi-2.2.4-1.el7')


class TestBodhiClient_parse_file(unittest.TestCase):
    """
    Test the BodhiClient.parse_file() method.
    """
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('bodhi.client.bindings.BodhiClient._load_cookies')
    @mock.patch('bodhi.client.bindings.os.path.exists')
    def test_parsing_valid_file(self, exists, _load_cookies, mock_open):
        """
        Test parsing a valid update template file
        """
        s = [
            "[fedora-workstation-backgrounds-1.1-1.fc26]\n",
            "# bugfix, security, enhancement, newpackage (required)\n",
            "type=bugfix\n",
            "\n",
            "# testing, stable\n",
            "request=testing\n",
            "\n",
            "# Bug numbers: 1234,9876\n",
            "bugs=123456,43212\n",
            "\n",
            "# Here is where you give an explanation of your update.\n",
            "notes=Initial Release\n",
            "\n",
            "# Enable request automation based on the stable/unstable karma thresholds\n",
            "autokarma=True\n",
            "stable_karma=3\n",
            "unstable_karma=-3\n",
            "\n",
            "# Automatically close bugs when this marked as stable\n",
            "close_bugs=True\n",
            "\n",
            "# Suggest that users restart after update\n",
            "suggest_reboot=False\n",
            ""]
        exists.return_value = True
        mock_open.return_value.readline.side_effect = s

        client = bindings.BodhiClient()
        updates = client.parse_file("sad")

        self.assertEqual(len(updates), 1)
        self.assertEqual(len(updates[0]), 12)
        self.assertEqual(updates[0]['close_bugs'], True)
        self.assertEqual(updates[0]['unstable_karma'], '-3')
        self.assertEqual(updates[0]['severity'], 'unspecified')
        self.assertEqual(updates[0]['stable_karma'], '3')
        self.assertEqual(updates[0]['builds'], 'fedora-workstation-backgrounds-1.1-1.fc26')
        self.assertEqual(updates[0]['autokarma'], 'True')
        self.assertEqual(updates[0]['suggest'], 'unspecified')
        self.assertEqual(updates[0]['notes'], 'Initial Release')
        self.assertEqual(updates[0]['request'], 'testing')
        self.assertEqual(updates[0]['bugs'], '123456,43212')
        self.assertEqual(updates[0]['type_'], 'bugfix')
        self.assertEqual(updates[0]['type'], 'bugfix')

    def test_parsing_nonexistant_file(self):
        """
        Test trying to parse a file that doesnt exist
        """
        client = bindings.BodhiClient()

        with self.assertRaises(ValueError) as exc:
            client.parse_file("/tmp/bodhi-test-parsefile2")

        self.assertEqual(unicode(exc.exception),
                         'No such file or directory: /tmp/bodhi-test-parsefile2')

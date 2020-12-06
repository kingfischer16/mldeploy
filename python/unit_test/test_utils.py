# =============================================================================
# TEST_UTILS.PY
# -----------------------------------------------------------------------------
# Unit tests for the 'utils.py' file.
# 
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import os
import pathlib
from unittest import mock, TestCase

import sys
mld_path = str(os.path.realpath(__file__)).rsplit('/', 2)[0]
sys.path.insert(0, mld_path+'/mldeploy/')
import utils


# =============================================================================
# Unit tests.
# -----------------------------------------------------------------------------
class TestGetAppDataFolder(TestCase):
    """
    Test cases for the 'mldeploy.utils._get_appdata_folder' function.
    """
    @mock.patch('utils.pathlib.Path.home')
    def test_get_appdata_folder_linux(self, mock_homepath):
        """
        Test the APPDATA path when the detected platform is 'linux'.
        """
        home_path_value = pathlib.PosixPath('/home/path')
        mock_homepath.return_value = home_path_value
        utils.PLATFORM = 'linux'
        app_folder = utils._get_appdata_folder()
        self.assertEqual(
            app_folder, str(home_path_value / '.local/share/mldeploy')
        )

    @mock.patch('utils.pathlib.Path.home')
    def test_get_appdata_folder_win32(self, mock_homepath):
        """
        Test the APPDATA path when the detected platform is 'win32'.
        """
        home_path_value = pathlib.PosixPath('/home/path')
        mock_homepath.return_value = home_path_value
        utils.PLATFORM = 'win32'
        app_folder = utils._get_appdata_folder()
        self.assertEqual(
            app_folder, str(home_path_value / 'AppData/Roaming/mldeploy')
        )
    
    @mock.patch('utils.pathlib.Path.home')
    def test_get_appdata_folder_other_error(self, mock_homepath):
        """
        Test the APPDATA path when the detected platform is not recognized.
        """
        home_path_value = pathlib.PosixPath('/home/path')
        mock_homepath.return_value = home_path_value
        utils.PLATFORM = 'something unknown'
        self.assertRaises(ValueError, utils._get_appdata_folder())


class TestGetRegistryPath(TestCase):
    """
    Test case for the 'mldeploy.utils._get_registry_path' function.
    """
    @mock.patch('utils._get_appdata_folder')
    def test_get_registry_path(self, mock_folder):
        """
        Tests the returned value.
        """
        test_folder = '/appdata'
        mock_folder.return_value = test_folder
        reg_path = utils._get_registry_path()
        self.assertEqual(reg_path, test_folder+'/'+utils.REG_FILE_NAME)


class TestGetRegistryData(TestCase):
    """
    Test case for 'mldeploy.utils._get_registry_data' function.
    """
    @mock.patch('utils._get_registry_path', return_value='test_file.json')
    @mock.patch('utils.json.load')
    def test_get_registry_data_open_success(self, mock_load, mock_path):
        """
        Tests the returned data when the registry file exists.
        """
        mock_load.return_value = {'test_project': 'test_value'}
        print("Registry data: ", utils._get_registry_data())
    
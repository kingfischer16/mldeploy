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
import io
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
        with self.assertRaises(ValueError) as cm:
            utils._get_appdata_folder()
        exc = cm.exception
        self.assertEqual(exc.__class__, ValueError)


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
    @mock.patch('utils.open', new_callable=mock.mock_open)
    @mock.patch('utils._get_registry_path', return_value='test_file.json')
    @mock.patch('utils.json.load')
    def test_get_registry_data_open_success(self, mock_load, mock_path, m_open):
        """
        Tests the returned data when the registry file exists.
        """
        sample_reg_data = {'test_project': 'test_value'}
        mock_load.return_value = sample_reg_data
        m_open.read_data = iter(['test1\n', 'test2\n', 'test3\n'])
        self.assertEqual(utils._get_registry_data(), sample_reg_data)
    
    @mock.patch('utils._get_registry_path', return_value='/my/missing/file.json')
    @mock.patch('utils.json.load')
    def test_get_registry_data_open_fail(self, mock_load, mock_path):
        """
        Tests the returned data when the registry file does not exist.
        """
        sample_reg_data = {'test_project': 'test_value'}
        mock_load.return_value = sample_reg_data
        self.assertEqual(utils._get_registry_data(), {})
    

class TestAddFieldToRegistry(TestCase):
    """
    Test case for 'mldeploy.utils._add_field_to_registry' function.
    """
    @mock.patch('utils.open', new_callable=mock.mock_open)
    @mock.patch('utils._get_registry_data', return_value={'proj': {}})
    @mock.patch('utils.json.dump')
    def test_add_field_to_registry_name_found(self, mock_dump, mock_data, m_open):
        """
        Tests the returned data when the registry file exists.
        """
        mock_dump.side_effect = TypeError() # error when successful, just to track
        with self.assertRaises(TypeError) as cm:
            utils._add_field_to_registry('proj', 'f', 'contents')
        exc = cm.exception
        self.assertEqual(exc.__class__, TypeError)
    
    @mock.patch('utils._get_registry_data', return_value={'proj': {}})
    def test_add_field_to_registry_name_missing(self, mock_data):
        """
        Tests the returned data when the registry file exists.
        """
        with self.assertRaises(ValueError) as cm:
            utils._add_field_to_registry('no_proj', 'f', 'contents')
        exc = cm.exception
        self.assertEqual(exc.__class__, ValueError)


class TestGetProjectFolder(TestCase):
    """
    Test case for 'mldeploy.utils._get_project_folder' function.
    """
    @mock.patch('utils._get_registry_data', return_value={'proj': {}})
    def test_get_project_folder(self, mock_data):
        """
        Tests the returned data when the registry file exists.
        """
        proj_name = 'proj'
        test_location = '/my/test/loc'
        mock_data.return_value = {proj_name: {'location': test_location}}
        self.assertEqual(utils._get_project_folder(proj_name), test_location)
    

class TestGetConfigData(TestCase):
    """
    Test case for 'mldeploy.utils._get_config_data' function.
    """
    @mock.patch('utils.open', new_callable=mock.mock_open)
    @mock.patch('utils._get_project_folder', return_value='/my/test/loc')
    @mock.patch('utils.ryml.YAML.load')
    def test_add_field_to_registry_name_found(self, mock_load, mock_data, m_open):
        """
        Tests the returned data when the registry file exists.
        """
        test_result = 'Success'
        mock_load.return_value = test_result
        self.assertEqual(utils._get_config_data('proj'), test_result)


class TestDeleteDockerImage(TestCase):
    """
    Test case for 'mldeploy.utils._delete_docker_image' function.
    """
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_no_reg_image(self, mock_reg, mock_conf):
        """
        Test:
            No registered image is found. None is returned.
        """
        proj_name = 'proj'
        reg_data = {proj_name: {'location': '/my/folder/proj'}}
        conf_data = {}
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        self.assertEqual(
            utils._delete_docker_image(proj_name),
            None
        )
    
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_2(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            - custom image found
            + delete_project=False
            - replace on rebuild
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'base-image': 'base_image'}
        # Delete project.
        del_proj = False
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        mock_client.images.list.return_value = [('reg_image', 1)]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.MSG_PREFIX}Project image '{reg_im}' was not deleted.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_3(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            - custom image found
            + delete_project=False
            + replace on rebuild = True
            - image in list
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'base-image': 'base_image',
            'replace-image-on-rebuild': True}
        # Delete project.
        del_proj = False
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        class ImTags:
            def __init__(self):
                self.tags = ('no_reg_image', 1)
        mock_client.images.list.return_value = [ImTags()]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.FAIL_PREFIX}Project image '{reg_im}' not found.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)
    
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_4(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            - custom image found
            + delete_project=False
            + replace on rebuild = True
            + image in list
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'base-image': 'base_image',
            'replace-image-on-rebuild': True}
        # Delete project.
        del_proj = False
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        mock_client.images.remove.return_value = None
        class ImTags:
            def __init__(self):
                self.tags = ('reg_image', 1)
        mock_client.images.list.return_value = [ImTags()]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.MSG_PREFIX}Deleting existing project image: {reg_im}\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)
    
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_5(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            + custom image found, different from reg image
            + delete_project=False
            + replace on rebuild = False
            - image in list
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'docker-image': 'diff_image',
            'base-image': 'base_image',
            'replace-image-on-rebuild': False}
        # Delete project.
        del_proj = False
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        class ImTags:
            def __init__(self):
                self.tags = ('no_reg_image', 1)
        mock_client.images.list.return_value = [ImTags()]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.MSG_PREFIX}Project image '{reg_im}' was not deleted.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)
    
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_6(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            + custom image found, different from reg image
            + delete_project=True
            + replace on rebuild = False
            - image in list
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'docker-image': 'diff_image',
            'base-image': 'base_image',
            'replace-image-on-rebuild': False}
        # Delete project.
        del_proj = True
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        class ImTags:
            def __init__(self):
                self.tags = ('reg_image', 1)
        mock_client.images.list.return_value = [ImTags()]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.MSG_PREFIX}Deleting existing project image: {reg_im}\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)
    
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('utils.docker.from_env')
    @mock.patch('utils._get_config_data')
    @mock.patch('utils._get_registry_data')
    def test_delete_docker_image_test_7(self,
        mock_reg, mock_conf, mock_env, mock_stdout):
        """
        Test config:
            + registered image found
            + custom image found, same as reg image
            + delete_project=True
            + replace on rebuild = False
            - image in list
        """
        proj_name = 'proj'
        # Registered image.
        reg_im = 'reg_image'
        reg_data = {proj_name: {'docker-image': reg_im}}
        # No custom image.
        conf_data = {
            'docker-image': reg_im,
            'base-image': 'base_image',
            'replace-image-on-rebuild': False}
        # Delete project.
        del_proj = True
        mock_reg.return_value = reg_data
        mock_conf.return_value = conf_data
        # Image in list.
        mock_client = mock_env.return_value
        class ImTags:
            def __init__(self):
                self.tags = ('reg_image', 1)
        mock_client.images.list.return_value = [ImTags()]
        utils._delete_docker_image(proj_name, deleting_project=del_proj)
        expected_output = f"{utils.MSG_PREFIX}Project image '{reg_im}' was not deleted.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)
    
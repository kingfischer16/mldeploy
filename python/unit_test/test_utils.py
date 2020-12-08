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
from collections import OrderedDict
import io
import os
import pathlib
from unittest import mock, TestCase

import sys
mld_path = str(os.path.realpath(__file__)).rsplit('/', 2)[0]
sys.path.insert(0, mld_path+'/mldeploy/')
import utils


# =============================================================================
# Unit tests for Registry utilities.
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


# =============================================================================
# Unit tests for Project folder utilities.
# -----------------------------------------------------------------------------
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
    

# =============================================================================
# Unit tests for Configuration file utilities.
# -----------------------------------------------------------------------------
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


# =============================================================================
# Unit tests for Docker image handling utilities.
# -----------------------------------------------------------------------------
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


# =============================================================================
# Unit tests for File handling utilities.
# -----------------------------------------------------------------------------
class TestTempCopyLocalFiles(TestCase):
    """
    Test case for 'mldeploy.utils._temp_copy_local_files' function.
    """
    @mock.patch('utils._get_project_folder')
    @mock.patch('utils._get_config_data', return_value={})
    def test_temp_copy_local_files_test_1(self, mock_conf, mock_folder):
        """
        Test config:
            - 'add-files' not in 'conf_data'
        """
        result = utils._temp_copy_local_files('proj')
        self.assertEqual(result, None)
        self.assertFalse(mock_folder.called)
    
    @mock.patch('utils._get_project_folder')
    @mock.patch('utils._get_config_data', return_value={'add-files': None})
    def test_temp_copy_local_files_test_2(self, mock_conf, mock_folder):
        """
        Test config:
            - 'add-files' in 'conf_data'
            - 'add_files' value is None
        """
        result = utils._temp_copy_local_files('proj')
        self.assertEqual(result, None)
        self.assertFalse(mock_folder.called)
    
    @mock.patch('utils.os.mkdir')
    @mock.patch('utils.shutil.copytree')
    @mock.patch('utils.os.path.isdir', return_value=True)
    @mock.patch('utils.os.path.exists', return_value=False)
    @mock.patch('utils._get_project_folder', return_value='/my/proj')
    @mock.patch('utils._get_config_data')
    def test_temp_copy_local_files_test_3(self, mock_conf, mock_folder,
        mock_exists, mock_isdir, mock_copytree, mock_mkdir):
        """
        Test config:
            - 'add-files' in 'conf_data'
            - 'add-files' has list of files
            - 'dst' path does not exist
            - source path is directory
        """
        mock_conf.return_value = {'add-files': ['hello.py']}
        utils._temp_copy_local_files('proj')
        self.assertTrue(mock_mkdir.called)
        self.assertTrue(mock_folder.called)
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_copytree.called)
    
    @mock.patch('utils.shutil.copy')
    @mock.patch('utils.os.path.isfile', return_value=True)
    @mock.patch('utils.os.mkdir')
    @mock.patch('utils.shutil.copytree')
    @mock.patch('utils.os.path.isdir', return_value=False)
    @mock.patch('utils.os.path.exists', return_value=True)
    @mock.patch('utils._get_project_folder', return_value='/my/proj')
    @mock.patch('utils._get_config_data')
    def test_temp_copy_local_files_test_4(self, mock_conf, mock_folder,
        mock_exists, mock_isdir, mock_copytree, mock_mkdir, mock_isfile,
        mock_copy):
        """
        Test config:
            - 'add-files' in 'conf_data'
            - 'add-files' has list of files
            - 'dst' path exists
            - source path is file
        """
        mock_conf.return_value = {'add-files': ['hello.py']}
        utils._temp_copy_local_files('proj')
        self.assertFalse(mock_mkdir.called)
        self.assertTrue(mock_folder.called)
        self.assertTrue(mock_isdir.called)
        self.assertFalse(mock_copytree.called)
        self.assertTrue(mock_copy.called)
    
    @mock.patch('utils.shutil.copy')
    @mock.patch('utils.os.path.isfile', return_value=False)
    @mock.patch('utils.os.mkdir')
    @mock.patch('utils.shutil.copytree')
    @mock.patch('utils.os.path.isdir', return_value=False)
    @mock.patch('utils.os.path.exists', return_value=True)
    @mock.patch('utils._get_project_folder', return_value='/my/proj')
    @mock.patch('utils._get_config_data')
    def test_temp_copy_local_files_test_5(self, mock_conf, mock_folder,
        mock_exists, mock_isdir, mock_copytree, mock_mkdir, mock_isfile,
        mock_copy):
        """
        Test config:
            - 'add-files' in 'conf_data'
            - 'add-files' has list of files
            - 'dst' path exists
            - source path is file
        """
        mock_conf.return_value = {'add-files': ['hello.py']}
        with self.assertRaises(ValueError) as cm:
            utils._temp_copy_local_files('proj')
        exc = cm.exception
        self.assertEqual(exc.__class__, ValueError)
        self.assertFalse(mock_mkdir.called)
        self.assertTrue(mock_folder.called)
        self.assertTrue(mock_isdir.called)
        self.assertFalse(mock_copytree.called)
        self.assertFalse(mock_copy.called)
        

class TestRemoveTempFiles(TestCase):
    """
    Test case for 'mldeploy.utils._remove_temp_files' function.
    """
    @mock.patch('utils._get_project_folder', return_value='/my/proj')
    @mock.patch('utils.os.path.exists', return_value=False)
    @mock.patch('utils.shutil.rmtree')
    def test_remove_temp_files_exists(self, mock_rmtree,
        mock_exists, mock_folder):
        """
        Test config:
            - path exists
        """
        utils._remove_temp_files('proj')
        self.assertFalse(mock_rmtree.called)
    
    @mock.patch('utils._get_project_folder', return_value='/my/proj')
    @mock.patch('utils.os.path.exists', return_value=True)
    @mock.patch('utils.shutil.rmtree')
    def test_remove_temp_files_does_not_exist(self, mock_rmtree,
        mock_exists, mock_folder):
        """
        Test config:
            - path exists
        """
        utils._remove_temp_files('proj')
        self.assertTrue(mock_rmtree.called)
    

# =============================================================================
# Unit tests for Display utilities.
# -----------------------------------------------------------------------------
class TestGetFieldIfExists(TestCase):
    """
    Test case for 'mldeploy.utils._get_field_if_exists' function.
    """
    @mock.patch('utils._get_registry_data', return_value={'proj': {}})
    def test_get_field_if_exists_does_not_exists(self, mock_data):
        """
        Tests that ValueError returned if poject name is not found.
        """
        with self.assertRaises(ValueError) as cm:
            utils._get_field_if_exists('no_proj', 'field')
        exc = cm.exception
        self.assertEqual(exc.__class__, ValueError)
    
    @mock.patch('utils._get_registry_data',
                return_value={'proj': {'field': 'contents'}})
    def test_get_field_if_exists_no_field(self, mock_data):
        """
        Tests that ValueError returned if poject name is found but
        the field is not found.
        """
        test_contents = utils._get_field_if_exists('proj', 'no_field')
        self.assertEqual(test_contents, '(None)')
    
    @mock.patch('utils._get_registry_data',
                return_value={'proj': {'field': 'contents'}})
    def test_get_field_if_exists_success(self, mock_data):
        """
        Tests that ValueError returned if project name and field
        exist.
        """
        test_contents = utils._get_field_if_exists('proj', 'field')
        self.assertEqual(test_contents, 'contents')


class TestGetRegistryLists(TestCase):
    """
    Test case for 'mldeploy.utils._get_registry_lists' function.
    """
    @mock.patch('utils._get_registry_data',
                return_value={'proj1': {}, 'proj2': {}})
    @mock.patch('utils._get_field_if_exists', return_value='example')
    def test_get_registry_lists(self, mock_field, mock_data):
        """
        Tests that the registry contents is output in the
        expected format.
        """
        correct_result = OrderedDict()
        proj_field = 'Project Name   '
        folder_field = 'Project Folder   '
        docker_field = 'Docker Image   '
        proj_len = len(proj_field)
        folder_len = len(folder_field)
        docker_len = len(docker_field)
        correct_result[proj_field] = [
            'proj1'.ljust(proj_len), 'proj2'.ljust(proj_len)
        ]
        correct_result[folder_field] = [
            'example'.ljust(folder_len), 'example'.ljust(folder_len)
        ]
        correct_result[docker_field] = [
            'example'.ljust(docker_len), 'example'.ljust(docker_len)
        ]
        test_result = utils._get_registry_lists()
        self.assertEqual(test_result, correct_result)

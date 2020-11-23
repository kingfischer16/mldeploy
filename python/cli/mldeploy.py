# =============================================================================
# MLDEPLOY_APP.PY
# -----------------------------------------------------------------------------
# The main code file for the CLI.
# 
#  
# The CLI is built using the following packages:
#   - fire: Google-supported, turns functions into CLI
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

import os
import shutil
import json
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pprint import pformat
from typing import NoReturn
import yaml
import fire


def test() -> str:
    return "This is a test. MLDeploy has installed successfully."

def cwd() -> str:
    return f"Current directory: {os.getcwd()}"

def walk() -> NoReturn:
    print(f"Folders found in '{os.getcwd()}':")
    for dir in list(os.walk(os.getcwd()))[0][1]:
        print(f"\t{dir}")
    print(highlight(pformat("--- (End of list) ---"), PythonLexer(), Terminal256Formatter()))

def create(name: str = 'mldeploy_project') -> NoReturn:
    curr_dir = os.getcwd()
    if name in list(os.walk(curr_dir))[0][1]:
        print(f"Project with name '{name}' already exists. Choose a different name of move to a different directory.")
    else:
        project_path = curr_dir + '/' + name
        os.mkdir(project_path)
        config_file = project_path+'/config.yml'
        shutil.copy(src=curr_dir+'/default_config.yml', dst=config_file)
        with open(config_file, 'r') as f:
            doc = yaml.load(f)
        doc.update({'project-name': name})
        with open(config_file, 'w') as f:
            yaml.dump(doc, f)
        print(f"Successfully created project '{name}' in '{curr_dir}'")

def delete(name: str) -> NoReturn:
    curr_dir = os.getcwd()
    if name not in list(os.walk(curr_dir))[0][1]:
        print(f"The current directory '{os.getcwd()}' does not contain a project named '{name}'.")
    

if __name__ == '__main__':
    fire.Fire({
        'test': test,
        'cwd': cwd,
        'create': create,
        'walk': walk
    })

# INDIRECT EMISSIONS MODELLER
# Supporting functions

import streamlit as st
import os
import yaml

def fn_LoadFile(filename: str) -> dict:
    fn_name = 'common_functions.py fn_LoadFile'
    acceptable_filetypes = ['md', 'yml']
    assert os.path.exists(filename), f"ERROR: {fn_name}: filename does not exist: {filename}"
    assert '.' in filename, f"ERROR: {fn_name}: filename does not have an extension: {filename}"
    file_ext = filename.lower().split('.')[-1]
    assert file_ext in acceptable_filetypes, f"ERROR: {fn_name}: file extension not in permitted list: {filename}"
    load_object = None
    if file_ext == 'md':
        with open(filename, 'r') as f: 
            load_object = f.read()
    if file_ext == 'yml':
        with open(filename, 'rb') as f: 
            load_object = yaml.load(f, Loader=yaml.SafeLoader)
    return load_object

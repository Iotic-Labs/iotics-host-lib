import os

"""The hack in the pre_gen_project script does not work for the project dir, which is created and made cwd before the
context is updated, so we have to move it after"""
os.rename(os.getcwd(), '../{{ cookiecutter.publisher_dir }}')

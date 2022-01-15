import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='opencontest-server',
    version='2.3.0',
    author='Anthony Wang',
    author_email='ta180m@pm.me',
    description='An OpenContest server written in Python ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/LadueCS/OpenContest-Server',
    py_modules=[ 'main' ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent'
    ],
    entry_points={
        'console_scripts': [
            'ocs = main:__main__',
        ],
    }
)

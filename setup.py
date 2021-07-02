import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lgp-grader",
    version="0.1.0",
    author="Anthony Wang",
    author_email="ta180m@gmail.com",
    description="Reference backend implementation for the LGP protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LadueCS/grader",
    py_modules=[ "grader" ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent"
    ],
    entry_points={
        'console_scripts': [
            'lgp-client = grader:__main__',
        ],
    }
)

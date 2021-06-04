import io
import os
import re
from setuptools import setup, find_packages

SOURCE_CODE_URL = "https://github.com/bedapub/metadata-registration-lib"

module_path = os.path.dirname(__file__)

with io.open(
    os.path.join(module_path, "metadata_registration_lib/__init__.py"),
    "rt",
    encoding="utf8",
) as f:
    version = re.search(r"__version__ = \"(.*?)\"", f.read()).group(1)

with io.open(os.path.join(module_path, "./README.md"), "rt", encoding="utf8") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="metadata_registration_lib",
    version=version,
    url=SOURCE_CODE_URL,
    project_urls={
        "Code": SOURCE_CODE_URL,
    },
    author="Cyril Lopez",
    author_email="cyrlop06@hotmail.com",
    description="A library for the Study metadata registration tool",
    packages=find_packages(),
    long_description=LONG_DESCRIPTION,
    install_requires=["requests", "dynamic-form", "xlsxwriter", "openpyxl", "xlrd"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
    ],
    extra_require={
        "dev": ["unittest"],
    },
)

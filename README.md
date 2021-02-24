# Metadata Registration LIB
A library for the Study metadata registration tool.

## Purpose
This app is being developed as part of the Study Registration Tool prototype for the BiOmics team. It is used by the API, UI and directly by users.

## Main functionalities
- **API utils:** Helper code to simplify calls to the [Metadata Registration API](https://github.com/bedapub/metadata-registration-api) and convert formats.
- **Data and file utils:** Data format conversion and helper to write denormalized files.
- **ES utils:** Elastic Search helper functions to index/delete studies and more.

## Installation

### Method 1: install as a package
The package is not on the official PyPi. You can install it running this command for example:
```bash
pip install -e git+https://github.com/bedapub/metadata-registration-lib.git@master#egg=metadata_registration_lib
```

### Method 2: clone repository
You can directly clone this repository and manually install the requirements using for example:
```bash
pip -f requirements.txt
```
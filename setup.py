import os

import setuptools

CUR_DIR = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(CUR_DIR, "data_spec_validator", "__version__.py"), "r") as f:
    exec(f.read(), about)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="data-spec-validator",
    version=about['__version__'],
    author="GoFreight",
    author_email="pypi@hardcoretech.co",
    description="Validation tool for API/Function parameters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hardcoretech/data-spec-validator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django :: 3",
        "Framework :: Django :: 4",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"data_spec_validator": "data_spec_validator"},
    packages=setuptools.find_packages(),
    install_requires=[
        "python-dateutil",
    ],
    extras_require={
        'decorator': ['Django>=3.0', 'djangorestframework'],
        'decorator-dj': ['Django>=3.0'],
    },
    python_requires=">=3.6",
    project_urls={"Changelog": "https://github.com/hardcoretech/data-spec-validator/blob/develop/CHANGELOG.md"},
)

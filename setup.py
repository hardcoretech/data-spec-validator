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
    author="CJHwong, falldog, HardCoreLewis, kilikkuo, xeonchen",
    author_email="pypi@hardcoretech.co, pypi@hardcoretech.co, pypi@hardcoretech.co, kilik.kuo@gmail.com, pypi@hardcoretech.co",
    description="Simple validation tool for API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hardcoretech/data-spec-validator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"data_spec_validator": "data_spec_validator"},
    packages=setuptools.find_packages(),
    install_requires=[
        "python-dateutil",
    ],
    extras_require={
        'decorator': ['Django', 'djangorestframework'],
    },
    python_requires=">=3.6",
)

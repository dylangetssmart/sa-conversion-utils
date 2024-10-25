from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="sa-conversion-utils",
    version="0.0.10",
    description="SmartAdvocate conversion utilities.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # include_package_data=True,
    # package_data={':': ['sql/*']},   # Include SQL scripts
    url="https://github.com/dylangetssmart/sa-conversion-utils",
    author="Dylan Smith",
    author_email="dylanjbsmith@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Database"
    ],
    install_requires=[
        "bson >= 0.5.10", 
        "pandas",
        "sqlalchemy",
        "rich",
        "python-dotenv",
        "pyodbc",
        "openpyxl",
        "chardet"
        # "tkinter"
    ],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    python_requires=">=3.10",
    entry_points={"console_scripts": ["samt = sa_conversion_utils.conv:main"]}
)
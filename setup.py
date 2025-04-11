from setuptools import setup, find_packages

setup(
    name="backuptool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tabulate",
    ],
    entry_points={
        "console_scripts": [
            "backuptool=backuptool.cli:main",
        ],
    },
    author="Mark Santos",
    author_email="mark.santos.1147@gmail.com",
    description="A command line file backup tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rocky074111/Backup_Tool",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

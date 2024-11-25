from setuptools import setup, find_packages

with open("version.txt") as f:
    version = f.read().strip()

setup(
    name="filepilot",
    version=version,
    description="AI-powered tool for creating, analyzing, and modifying files using natural language",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="João Pinto",
    url="https://github.com/joaompinto/filepilot",  # Add project URL
    project_urls={
        "Source": "https://github.com/joaompinto/filepilot",
        "Bug Tracker": "https://github.com/joaompinto/filepilot/issues",
    },
    packages=find_packages(),
    package_data={
        'filepilot': [
            'py.typed',
            '*.py',
            'cli/*.py',
            '../version.txt'  # Add version.txt
        ]
    },
    install_requires=[
        "anthropic",
        "rich",
        "typer[all]"  # Added typer dependency with all extras
    ],
    entry_points={
        "console_scripts": [
            "filepilot=filepilot.__main__:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
    ],
)
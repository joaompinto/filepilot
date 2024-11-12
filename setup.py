from setuptools import setup, find_packages

setup(
    name="filepilot",
    version="0.1.0",
    description="AI-powered tool for creating, analyzing, and modifying files using Natural Language Processing",
    author="João Pinto",
    packages=find_packages(include=['filepilot', 'filepilot.*']),
    package_data={'filepilot': ['py.typed']},
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "anthropic>=0.5.0",
    ],
    entry_points={
        "console_scripts": [
            "filepilot=filepilot.filepilot:app",
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
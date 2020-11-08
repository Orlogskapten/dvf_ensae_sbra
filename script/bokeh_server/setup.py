from setuptools import setup

setup(
    name = "my_package",
    entry_points={
        "console_scripts": ["my_script = my_package.local_server:main"],
    },
)
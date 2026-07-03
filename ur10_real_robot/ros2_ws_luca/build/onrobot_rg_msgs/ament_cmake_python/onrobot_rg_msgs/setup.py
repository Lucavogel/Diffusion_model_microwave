from setuptools import find_packages
from setuptools import setup

setup(
    name='onrobot_rg_msgs',
    version='1.0.0',
    packages=find_packages(
        include=('onrobot_rg_msgs', 'onrobot_rg_msgs.*')),
)

from setuptools import find_packages, setup

setup(
    name='black_bean',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask', 'pyaes', 'pyfunctional', 'apscheduler'
    ],
)

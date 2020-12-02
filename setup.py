import setuptools

setuptools.setup(
    name='bot',
    version='0.0.1',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'bot = bot.main:main',
        ],
    },
    install_requires=[
        'click>=7.1.2',
    ],
)

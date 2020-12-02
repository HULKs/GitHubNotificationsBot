import setuptools

setuptools.setup(
    name='bot',
    version='0.0.1',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'bot = bot.main:main',
            'bot-login = bot.login:main',
        ],
    },
    install_requires=[
        'click>=7.1.2',
        'matrix-nio[e2e]>=0.15.2',
    ],
)

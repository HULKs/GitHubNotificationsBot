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
        'aiogram>=2.11.2',
        'aiohttp>=3.7.3',
        'click>=7.1.2',
        'matrix-nio[e2e]>=0.15.2',
    ],
)

import setuptools

setuptools.setup(
    name="bot",
    version="0.0.1",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "bot = bot.main:main",
            "bot-login = bot.login:main",
        ],
    },
    install_requires=[
        "aiogram==3.1.1",
        "aiohttp==3.8.6",
        "click==8.1.7",
        "links-from-link-header==0.1.0",
        "matrix-nio[e2e]==0.22.2",
    ],
)

# discordbot

A discordbot I made for playing music in mine and my friends servers. It also has some other useful/fun commands. 

# Prerequesites

- Java 17 or later
- Python 3.10 or later

# Dependencies

- Lavalink in root directory, download found [here](https://github.com/lavalink-devs/Lavalink/releases)
- LavaSrc in plugins folder, download found [here](https://github.com/topi314/LavaSrc/releases)
- .env file referencing passwords and tokens needed. [Keys needed found here](#env-keys)
- application.yml file in root, can be copied from [here](https://github.com/topi314/LavaSrc/blob/master/application.example.yml) with updated values. 

## ENV keys

### Needed for discord bot

- DISCORD_TOKEN

### Whatever prefix you want your bot to have

- PREFIX

### Lavalink credentials (referenced in application.yml)

- LAVALINK_PASS
- LAVALINK_ADDRESS

### Spotify credentials

- SPOTIFY_CLIENT_ID
- SPOTIFY_CLIENT_SECRET

# How to use

After all prerequesites and dependencies are solved the first thing to do it start the lavalink server. This is done through `java -jar <name of your lavalink>.jar`, or if your lavalink file is named Lavalink.jar, just double click the `start_lavalink.bat` file. Same thing applies for starting the actual bot after this, either start it through `python3 main.py` or double click the `start_pythonbot.bat` file. 
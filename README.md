# Pixel Starships Discord Bot

This is a Discord Bot for Pixel Starships

## 1. Setup

1. Log in to the server (this is optional if you are running from
   a local computer).  For example, if you are running on an
   Amazon AWS AMI, this would be:

```bash
ssh -i ~/.ssh/my_key_file.pem ec2-user@hostname
```

where your Amazon AWS instance key file is `my_key_file.pem`
and the username and address above should be changed to that
of your instance running on AWS.

2. Install Python 3.6, Git, followed by `discord.py`.
   On an Amazon AMI, this would be:

```bash
sudo yum install python36 python36-pip git
pip-3.6 install discord.py --user
```

3. Clone this Github repository

```bash
git clone https://github.com/jzx3/pss.git
```

4. Create a Discord Bot.  A good guide is Sebi's bot tutorial.
   The link to the tutorial is [here](https://discord.gg/GWdhBSp).

   Get the invite link for the Discord bot and add the bot to the
   Discord chat.

   Add the bot token to `~/.bash_profile` as follows:

```bash
export DISCORD_BOT_TOKEN="insert_bot_token_here"
```

## 2. Running the Bot

Inside the server, create a `screen` session to run the job
in the background. Note that it is not necessary to use
`screen`--the job can be run in the background in other ways,
for example using the `nohup` command.

```bash
screen -S pss    # Create a screen session named "pss"
cd pss/prestige
./run.sh         # Run the bot
```

Press Ctrl-A, Ctrl-D to exit screen.  To get back to the screen
session (e.g. for stopping the bot), restore the session with:

```
screen -r pss
```

To stop the bot, press Ctrl-C twice.

## 3. Bot Usage on Discord

Inside Discord chat, get the list of commands using:

```
/help
```

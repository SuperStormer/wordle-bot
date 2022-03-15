import asyncio
import json
import os
import random
import re
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .helpers import wordle_message
from .wordle import Wordle

# setup
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  # pylint: disable=assigning-non-slot
bot = commands.Bot(command_prefix=["w.", "w!"], intents=intents)

current_wordles: dict[int, Wordle] = {}
VALID_GUESS = re.compile(r"[A-Z]{5}")

# word list stuff
with open("words.json", encoding="utf-8") as f:
	words = json.load(f)
	actual_words = words["actual"]
	valid_words = words["valid"] + words["actual"]

def get_word() -> str:
	return random.choice(actual_words)

# abstract commands

async def handle_guess(guess, send_message, channel_id):
	if channel_id not in current_wordles:
		await send_message("There are no wordles currently running in this channel.")
		return
	
	if len(guess) != 5:
		await send_message(f"{guess!r} is {len(guess)} characters long.")
		return
	
	guess = guess.lower()
	if guess not in valid_words:
		await send_message(f"{guess!r} is not a valid word.")
		return
	
	wordle = current_wordles[channel_id]
	wordle.guesses.append(guess)
	
	message, ended = wordle_message(wordle)
	await send_message(message)
	if ended:
		del current_wordles[channel_id]

async def start_wordle(send_message, channel_id):
	if channel_id in current_wordles:
		await send_message("This channel already has a wordle running.")
		return
	
	wordle = Wordle(get_word())
	current_wordles[channel_id] = wordle
	await send_message("Wordle started!")

async def quit_wordle(send_message, channel_id):
	if channel_id not in current_wordles:
		await send_message("There are no wordles currently running in this channel.")
		return
	wordle = current_wordles[channel_id]
	await send_message(f"You lost!\nThe word was {wordle.actual!r}")
	del current_wordles[channel_id]

# starting

@bot.command(name="wordle", aliases=["w", "start", "s"])
async def start_cmd(ctx: commands.Context):
	await start_wordle(ctx.send, ctx.channel.id)

@bot.tree.command(name="wordle")
async def start_slash(interaction: discord.Interaction):
	await start_wordle(interaction.response.send_message, interaction.channel_id)

# guessing

@bot.command(name="guess", aliases=["g"])
async def guess_cmd(ctx: commands.Context, guess: str):
	await handle_guess(guess, ctx.send, ctx.channel.id)

@bot.tree.command(name="guess")
@app_commands.describe(guess="the guessed word")
async def guess_slash(interaction: discord.Interaction, guess: str):
	await handle_guess(guess, interaction.response.send_message, interaction.channel_id)

@bot.event
async def on_message(message: discord.Message):
	if message.author == bot.user:
		return
	
	if message.channel.id in current_wordles and VALID_GUESS.fullmatch(message.content):
		await handle_guess(message.content, message.channel.send, message.channel.id)
	else:
		await bot.process_commands(message)

# give up
@bot.command(name="quit", aliases=["end", "q"])
async def quit_cmd(ctx: commands.Context):
	await quit_wordle(ctx.send, ctx.channel.id)

@bot.tree.command(name="quit")
async def quit_slash(interaction: discord.Interaction):
	await quit_wordle(interaction.response.send_message, interaction.channel_id)

# debug

@bot.command(name="debug", alias="cheat")
@commands.is_owner()
async def cheat(ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
	if channel is None:
		assert isinstance(ctx.channel, discord.TextChannel)
		channel = ctx.channel
	
	await ctx.send(current_wordles[channel.id].actual)

@bot.command(name="set_wordle")
@commands.is_owner()
async def set_wordle(
	ctx: commands.Context, word: str, channel: Optional[discord.TextChannel] = None
):
	if channel is None:
		assert isinstance(ctx.channel, discord.TextChannel)
		channel = ctx.channel
	
	if len(word) != 5:
		await ctx.send(f"{word!r} is {len(word)} characters long.")
		return
	
	wordle = Wordle(word)
	current_wordles[channel.id] = wordle
	await ctx.send(f"Set {channel.mention}'s word to {word}")

@bot.command(name="set_word")
@commands.is_owner()
async def set_word(ctx: commands.Context, word: str, channel: Optional[discord.TextChannel] = None):
	if channel is None:
		assert isinstance(ctx.channel, discord.TextChannel)
		channel = ctx.channel
	
	if channel.id not in current_wordles:
		await ctx.send("There are no wordles currently running in this channel.")
		return
	
	if len(word) != 5:
		await ctx.send(f"{word!r} is {len(word)} characters long.")
		return
	
	current_wordles[channel.id].actual = word
	await ctx.send(f"Set {channel.mention}'s word to {word}")

@bot.command(name="eval")
@commands.is_owner()
async def eval_cmd(ctx: commands.Context, *, arg):
	await ctx.send(eval(arg))

# error handling
@bot.event
async def on_command_error(ctx: commands.Context, error):
	if isinstance(
		error, (
		commands.ArgumentParsingError, commands.BadArgument, commands.BotMissingPermissions,
		commands.CommandNotFound, commands.MissingRequiredArgument, commands.NoPrivateMessage,
		commands.NotOwner
		)
	):
		await ctx.send(str(error))

# too lazy to implement DMS lol
@bot.check
async def globally_block_dms(ctx):
	return ctx.guild is not None

# sync
@bot.event
async def on_ready():
	print("syncing")
	await bot.tree.sync()

# run bot
async def start_bot():
	print("running bot")
	token = os.environ["TOKEN"]
	await bot.start(token=token)

#client.run(token=os.environ["TOKEN"])

asyncio.run(start_bot())

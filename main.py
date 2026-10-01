import json
import discord
from discord.ext import commands


class UserHelp(commands.DefaultHelpCommand):
    def get_ending_note(self):
        return "Question Box Bot"


class QuestionBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cog")


def main():
    with open("./info.json", "r", encoding="utf-8") as f:
        json_load = json.load(f)

    token = json_load["token"]

    intents = discord.Intents.default()
    intents.message_content = True

    bot = QuestionBot(
        command_prefix="~",
        help_command=UserHelp(),
        activity=discord.Game(name="Anonymous Question Box"),
        intents=intents
    )

    bot.run(token)


if __name__ == "__main__":
    main()

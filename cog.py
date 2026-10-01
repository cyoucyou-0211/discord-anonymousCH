import csv
import io
import json
import traceback
from pathlib import Path
from collections import OrderedDict

import discord
from discord.ext import commands


def anonymous_name(number):
    return f"【名無しの{number}さん】"


class AnonymousModal(discord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="Anonymous Post")
        self.cog = cog

        self.text = discord.ui.TextInput(
            label="Message",
            placeholder="??????????????????",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )

        self.add_item(self.text)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        channel = self.cog.bot.get_channel(self.cog.channel_id)

        if channel is None:
            await interaction.edit_original_response(
                content="?????????????????"
            )
            return

        number = self.cog.get_next_anonymous_number()
        name = anonymous_name(number)
        content = str(self.text.value)

        with open("./store.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "modal",
                str(interaction.user),
                content
            ])

        try:
            webhook = await self.cog.get_webhook(channel, number)

            await webhook.send(
                content=content,
                username=name,
                wait=True,
                silent=True
            )

            await self.cog.move_post_button(channel)

            await interaction.delete_original_response()

        except discord.Forbidden:
            await interaction.response.send_message(
                "???????????????",
                ephemeral=True
            )


class AnonymousThreadModal(discord.ui.Modal):
    def __init__(self, cog):
        super().__init__(title="Anonymous Thread")
        self.cog = cog

        self.thread_name = discord.ui.TextInput(
            label="Thread name",
            placeholder="?????????",
            required=True,
            max_length=100
        )

        self.first_message = discord.ui.TextInput(
            label="First message",
            placeholder="???????",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )

        self.add_item(self.thread_name)
        self.add_item(self.first_message)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        channel = self.cog.bot.get_channel(self.cog.channel_id)

        if channel is None:
            await interaction.edit_original_response(
                content="?????????????????"
            )
            return

        if not isinstance(channel, discord.TextChannel):
            await interaction.edit_original_response(
                content="?????????????????????????"
            )
            return

        try:
            thread = await channel.create_thread(
                name=str(self.thread_name.value),
                type=discord.ChannelType.public_thread
            )
        except discord.Forbidden:
            await interaction.edit_original_response(
                content="????????????????????"
            )
            return

        number = self.cog.get_next_anonymous_number()
        name = anonymous_name(number)
        content = str(self.first_message.value)

        with open("./store.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "thread",
                str(interaction.user),
                content
            ])

        try:
            webhook = await self.cog.get_webhook(channel, number)

            await webhook.send(
                content=content,
                username=name,
                thread=thread,
                wait=True,
                silent=True
            )

            await self.cog.move_reply_button(thread)

            await interaction.delete_original_response()

        except discord.Forbidden:
            await interaction.edit_original_response(
                content="???????????????????????"
            )


class AnonymousButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Anonymous Post",
        style=discord.ButtonStyle.primary,
        custom_id="anonymous_post_button"
    )
    async def anonymous_post(self, interaction, button):
        await interaction.response.send_modal(
            AnonymousModal(self.cog)
        )

    @discord.ui.button(
        label="Anonymous Thread",
        style=discord.ButtonStyle.secondary,
        custom_id="anonymous_thread_button"
    )
    async def anonymous_thread(self, interaction, button):
        await interaction.response.send_modal(
            AnonymousThreadModal(self.cog)
        )


class AnonymousPostButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Anonymous Post",
        style=discord.ButtonStyle.primary,
        custom_id="anonymous_post_button_only"
    )
    async def anonymous_post(self, interaction, button):
        print(
            f"[BUTTON] Anonymous Post clicked "
            f"user={interaction.user.id} "
            f"interaction={interaction.id}",
            flush=True
        )

        try:
            await interaction.response.send_modal(
                AnonymousModal(self.cog)
            )
            print(
                f"[BUTTON] Anonymous Post modal opened "
                f"interaction={interaction.id}",
                flush=True
            )
        except Exception as e:
            print(
                f"[BUTTON ERROR] Anonymous Post "
                f"type={type(e).__name__} "
                f"interaction={interaction.id} "
                f"error={e}",
                flush=True
            )
            traceback.print_exc()

class AnonymousThreadButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Anonymous Thread",
        style=discord.ButtonStyle.secondary,
        custom_id="anonymous_thread_button_only"
    )
    async def anonymous_thread(self, interaction, button):
        await interaction.response.send_modal(
            AnonymousThreadModal(self.cog)
        )


class AnonymousReplyModal(discord.ui.Modal):
    def __init__(self, cog, thread):
        super().__init__(title="Anonymous Reply")
        self.cog = cog
        self.thread = thread

        self.text = discord.ui.TextInput(
            label="Reply",
            placeholder="返信内容を入力してください",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )

        self.add_item(self.text)

    async def on_submit(self, interaction):
        # Discordにすぐ応答してタイムアウトを防ぐ
        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        try:
            content = str(self.text.value)

            await self.cog.send_anonymous_reply(
                thread=self.thread,
                user=interaction.user,
                content=content
            )

            await interaction.delete_original_response()

        except Exception as e:
            print(
                f"[REPLY ERROR] modal submit failed: "
                f"type={type(e).__name__} "
                f"thread_id={self.thread.id} "
                f"error={e}",
                flush=True
            )

            try:
                await interaction.edit_original_response(
                    content="匿名返信の送信に失敗しました。"
                )
            except Exception:
                pass


class AnonymousReplyButton(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="匿名で返信",
        style=discord.ButtonStyle.primary,
        custom_id="anonymous_reply_button"
    )
    async def anonymous_reply(self, interaction, button):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message(
                "このボタンはスレッド内でのみ使用できます。",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            AnonymousReplyModal(
                self.cog,
                interaction.channel
            )
        )


class QuestionBotCog(commands.Cog, name="QuestionBox"):
    def __init__(self, bot):
        self.bot = bot

        with open("./info.json", "r", encoding="utf-8") as f:
            self.json_load = json.load(f)

        self.channel_id = self.json_load["channel_id"]

        self.counter_file = Path("./anonymous_counter.json")

        if self.counter_file.exists():
            with open(
                self.counter_file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)
                self.next_number = int(
                    data.get("next_number", 1)
                )
        else:
            self.next_number = 1

    async def move_reply_button(self, thread):
        """
        スレッド内の匿名返信ボタンを一番下へ移動する。
        古いボタンメッセージを削除して、新しいものを投稿する。
        """
        try:
            # Bot自身が過去に置いた返信ボタンを探す
            async for old_message in thread.history(limit=100):
                if (
                    old_message.author.id == self.bot.user.id
                    and old_message.content == "匿名で返信できます"
                ):
                    try:
                        await old_message.delete()
                    except Exception as e:
                        print(
                            f"[REPLY BUTTON] old button delete failed: "
                            f"type={type(e).__name__} "
                            f"message_id={old_message.id} "
                            f"error={e}",
                            flush=True
                        )

            # 一番下に新しいボタンを置く
            await thread.send(
                "匿名で返信できます",
                view=AnonymousReplyButton(self),
                silent=True
            )

        except Exception as e:
            print(
                f"[REPLY BUTTON ERROR] "
                f"type={type(e).__name__} "
                f"thread_id={thread.id} "
                f"error={e}",
                flush=True
            )

    async def move_post_button(self, channel):
        """
        匿名投稿チャンネルの投稿ボタンを一番下へ移動する。
        古いボタンメッセージを削除して、新しいものを投稿する。
        """
        try:
            async for old_message in channel.history(limit=100):
                if (
                    old_message.content == "Anonymous Post"
                    and old_message.components
                ):
                    try:
                        await old_message.delete()
                    except Exception as e:
                        print(
                            f"[POST BUTTON] old button delete failed: "
                            f"type={type(e).__name__} "
                            f"message_id={old_message.id} "
                            f"error={e}",
                            flush=True
                        )

            await channel.send(
                "Anonymous Post",
                view=AnonymousPostButton(self),
                silent=True
            )

        except Exception as e:
            print(
                f"[POST BUTTON ERROR] "
                f"type={type(e).__name__} "
                f"channel_id={getattr(channel, 'id', None)} "
                f"error={e}",
                flush=True
            )

    async def send_anonymous_reply(self, thread, user, content):
        """
        匿名返信ボタンから送信された内容をWebhookで匿名投稿する。
        """
        number = self.get_next_anonymous_number()
        name = anonymous_name(number)

        with open(
            "./store.csv",
            "a",
            newline="",
            encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow([
                "reply",
                str(user),
                content
            ])

        parent_channel = self.bot.get_channel(self.channel_id)

        if parent_channel is None:
            raise RuntimeError("Parent channel not found")

        webhook = await self.get_webhook(
            parent_channel,
            number
        )

        await webhook.send(
            content=content,
            username=name,
            thread=thread,
            wait=True,
            silent=True
        )

        await self.move_reply_button(thread)


    def get_next_anonymous_number(self):
        number = self.next_number

        if self.next_number >= 1000:
            self.next_number = 1
        else:
            self.next_number += 1

        with open(
            self.counter_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                {"next_number": self.next_number},
                f,
                indent=4,
                ensure_ascii=False
            )

        return number

    async def get_webhook(self, channel, number):
        webhooks = await channel.webhooks()

        if number % 2 == 1:
            webhook_name = "AnonymousQuestionBoxA"
        else:
            webhook_name = "AnonymousQuestionBoxB"

        for webhook in webhooks:
            if webhook.name == webhook_name:
                return webhook

        return await channel.create_webhook(
            name=webhook_name
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Commands
        if message.content.startswith("~"):
            await self.bot.process_commands(message)
            return

        # Normal channel or a thread under the target channel
        if isinstance(message.channel, discord.Thread):
            if message.channel.parent_id != self.channel_id:
                return
            parent_channel = self.bot.get_channel(self.channel_id)
            target_thread = message.channel
        else:
            if message.channel.id != self.channel_id:
                return
            parent_channel = message.channel
            target_thread = None

        number = self.get_next_anonymous_number()
        name = anonymous_name(number)

        with open(
            "./store.csv",
            "a",
            newline="",
            encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow([
                message.id,
                str(message.author),
                message.content
            ])

        files = []

        for attachment in message.attachments:
            data = await attachment.read()

            files.append(
                discord.File(
                    io.BytesIO(data),
                    filename=attachment.filename
                )
            )

        try:
            await message.delete()
        except Exception as e:
            print(
                f"[ANON ERROR] message.delete failed: "
                f"type={type(e).__name__} "
                f"message_id={message.id} "
                f"channel_id={message.channel.id} "
                f"error={e}",
                flush=True
            )
            return

        try:
            webhook = await self.get_webhook(
                parent_channel,
                number
            )

            print("[DEBUG] before webhook.send", flush=True)

            if target_thread is not None:
                await webhook.send(
                    content=message.content or None,
                    username=name,
                    files=files,
                    thread=target_thread,
                    wait=True,
                    silent=True
            )

            else:
                await webhook.send(
                    content=message.content or None,
                    username=name,
                    files=files,
                    wait=True,
                    silent=True
                )

            print("[DEBUG] after webhook.send", flush=True)

            if target_thread is not None:
                print("[DEBUG] moving reply button", flush=True)
                await self.move_reply_button(target_thread)
            else:
                print("[DEBUG] moving post button", flush=True)
                await self.move_post_button(parent_channel)

            print("[DEBUG] button move finished", flush=True)

        except Exception as e:
            print(
                f"[ANON ERROR] webhook.send failed: "
                f"type={type(e).__name__} "
                f"message_id={message.id} "
                f"channel_id={message.channel.id} "
                f"thread={target_thread is not None} "
                f"error={e}",
                flush=True
            )
            traceback.print_exc()
            return

    @commands.command(name="post")
    async def post(self, ctx):
        await ctx.send(
            "Anonymous Post",
            view=AnonymousPostButton(self)
        )

    @commands.command(name="thread")
    async def thread(self, ctx):
        await ctx.send(
            "Anonymous Thread",
            view=AnonymousThreadButton(self)
        )

    @commands.command(name="panel")
    async def panel(self, ctx):
        await ctx.send(
            "Anonymous Question Box",
            view=AnonymousButton(self)
        )

    @commands.command(name="set")
    async def _set(self, ctx):
        channel_id = ctx.channel.id
        self.channel_id = channel_id

        with open("./info.json", "r+") as f:
            updated = json.load(
                f,
                object_pairs_hook=OrderedDict
            )

            updated["channel_id"] = channel_id

            f.seek(0)

            json.dump(
                updated,
                f,
                indent=4,
                ensure_ascii=False
            )

            f.truncate()

        await ctx.send("Channel updated")


async def setup(bot):
    cog = QuestionBotCog(bot)
    await bot.add_cog(cog)
    bot.add_view(AnonymousButton(cog))
    bot.add_view(AnonymousPostButton(cog))
    bot.add_view(AnonymousThreadButton(cog))
    bot.add_view(AnonymousReplyButton(cog))

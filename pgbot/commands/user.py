from __future__ import annotations

import os
import random
import re
import time

import discord
import pygame
from discord.errors import HTTPException

from pgbot import clock, common, docs, embed_utils, emotion, sandbox, utils
from pgbot.commands.base import BaseCommand, CodeBlock


class UserCommand(BaseCommand):
    """ Base class to handle user commands. """

    async def cmd_version(self):
        """
        ->type Other commands
        ->signature pg!version
        ->description Get the version of <@&822580851241123860>
        -----
        Implement pg!version, to report bot version
        """
        await embed_utils.replace(
            self.response_msg, "Current bot's version", f"`{common.VERSION}`"
        )

    async def cmd_clock(self):
        """
        ->type Get help
        ->signature pg!clock
        ->description 24 Hour Clock showing <@&778205389942030377> 's who are available to help
        -----
        Implement pg!clock, to display a clock of helpfulies/mods/wizards
        """
        t = time.time()
        pygame.image.save(clock.user_clock(t), f"temp{t}.png")
        common.cmd_logs[self.invoke_msg.id] = await self.response_msg.channel.send(
            file=discord.File(f"temp{t}.png")
        )
        await self.response_msg.delete()
        os.remove(f"temp{t}.png")

    async def _cmd_doc(self, modname, page=0, msg=None):
        """
        Helper function for doc, handle pg!refresh stuff
        """
        if not msg:
            msg = self.response_msg

        await docs.put_doc(modname, msg, self.invoke_msg.author, page)

    async def cmd_doc(self, name: str):
        """
        ->type Get help
        ->signature pg!doc [module.Class.method]
        ->description Look up the docstring of a Python/Pygame object, e.g str or pygame.Rect
        -----
        Implement pg!doc, to view documentation
        """
        await self._cmd_doc(name)

    async def cmd_exec(self, code: CodeBlock):
        """
        ->type Run code
        ->signature pg!exec [python code block]
        ->description Run python code in an isolated environment.
        ->extended description
        Import is not available. Various methods of builtin objects have been disabled for security reasons.
        The available preimported modules are:
        `math, cmath, random, re, time, string, itertools, pygame`
        To show an image, overwrite `output.img` to a surface (see example command).
        To make it easier to read and write code use code blocks (see [HERE](https://discord.com/channels/772505616680878080/774217896971730974/785510505728311306)).
        ->example command pg!exec \\`\\`\\`py ```py
        # Draw a red rectangle on a transparent surface
        output.img = pygame.Surface((200, 200)).convert_alpha()
        output.img.fill((0, 0, 0, 0))
        pygame.draw.rect(output.img, (200, 0, 0), (50, 50, 100, 100))```
        \\`\\`\\`
        -----
        Implement pg!exec, for execution of python code
        """
        tstamp = time.perf_counter_ns()
        returned = await sandbox.exec_sandbox(
            code.code, tstamp, 10 if self.is_priv else 5
        )
        dur = returned.duration  # the execution time of the script alone

        if returned.exc is None:
            if returned.img:
                if os.path.getsize(f"temp{tstamp}.png") < 2 ** 22:
                    await self.response_msg.channel.send(
                        file=discord.File(f"temp{tstamp}.png")
                    )
                else:
                    await embed_utils.replace(
                        self.response_msg,
                        "Image cannot be sent:",
                        "The image file size is above 4MiB",
                    )
                os.remove(f"temp{tstamp}.png")

            await embed_utils.replace(
                self.response_msg,
                f"Returned text (code executed in {utils.format_time(dur)}):",
                utils.code_block(returned.text)
            )

        else:
            await embed_utils.replace(
                self.response_msg,
                common.EXC_TITLES[1],
                utils.code_block(", ".join(map(str, returned.exc.args)))
            )

    async def _cmd_help(self, argname, page=0, msg=None):
        """
        Helper function for pg!help, handle pg!refresh stuff
        """
        if not msg:
            msg = self.response_msg

        if argname is None:
            await utils.send_help_message(
                msg,
                self.invoke_msg.author,
                self.cmds_and_funcs,
                page=page
            )
        else:
            await utils.send_help_message(
                msg,
                self.invoke_msg.author,
                self.cmds_and_funcs,
                argname
            )

    async def cmd_help(self, name: str = None):
        """
        ->type Get help
        ->signature pg!help [command]
        ->description Ask me for help
        ->example command pg!help help
        -----
        Implement pg!help, to display a help message
        """
        await self._cmd_help(name)

    async def cmd_pet(self):
        """
        ->type Play With Me :snake:
        ->signature pg!pet
        ->description Pet me :3 . Don't pet me too much or I will get mad.
        -----
        Implement pg!pet, to pet the bot
        """
        emotion.pet_anger -= (time.time() - emotion.last_pet - common.PET_INTERVAL) * (
            emotion.pet_anger / common.JUMPSCARE_THRESHOLD
        ) - common.PET_COST

        if emotion.pet_anger < common.PET_COST:
            emotion.pet_anger = common.PET_COST
        emotion.last_pet = time.time()

        fname = "die.gif" if emotion.pet_anger > common.JUMPSCARE_THRESHOLD else "pet.gif"
        await embed_utils.replace(
            self.response_msg,
            "",
            "",
            0xFFFFAA,
            "https://raw.githubusercontent.com/PygameCommunityDiscord/"
            + f"PygameCommunityBot/main/assets/images/{fname}"
        )

    async def cmd_vibecheck(self):
        """
        ->type Play With Me :snake:
        ->signature pg!vibecheck
        ->description Check my mood.
        -----
        Implement pg!vibecheck, to check if the bot is angry
        """
        await embed_utils.replace(
            self.response_msg,
            "Vibe Check, snek?",
            f"Previous petting anger: {emotion.pet_anger:.2f}/{common.JUMPSCARE_THRESHOLD:.2f}"
            + f"\nIt was last pet {utils.format_long_time(round(time.time() - emotion.last_pet))} ago",
        )

    async def cmd_sorry(self):
        """
        ->type Play With Me :snake:
        ->signature pg!sorry
        ->description You were hitting me <:pg_bonk:780423317718302781> and you're now trying to apologize?
        Let's see what I'll say :unamused:
        -----
        Implement pg!sorry, to ask forgiveness from the bot after bonccing it
        """
        if not emotion.boncc_count:
            await embed_utils.replace(
                self.response_msg,
                "Ask forgiveness from snek?",
                "Snek is happy. Awww, don't be sorry."
            )
            return

        num = random.randint(0, 3)
        if num:
            emotion.boncc_count -= num
            if emotion.boncc_count < 0:
                emotion.boncc_count = 0
            await embed_utils.replace(
                self.response_msg,
                "Ask forgiveness from snek?",
                "Your pythonic lord accepts your apology.\n"
                + f"Now go to code again.\nThe boncc count is {emotion.boncc_count}"
            )
        else:
            await embed_utils.replace(
                self.response_msg,
                "Ask forgiveness from snek?",
                "How did you dare to boncc a snake?\nBold of you to assume "
                + "I would apologize to you, two-feet-standing being!\nThe "
                + f"boncc count is {emotion.boncc_count}"
            )

    async def cmd_bonkcheck(self):
        """
        ->type Play With Me :snake:
        ->signature pg!bonkcheck
        ->description Check how many times you have done me harm.
        -----
        Implement pg!bonkcheck, to check how much the snek has been boncced
        """
        if emotion.boncc_count:
            await embed_utils.replace(
                self.response_msg,
                "The snek is hurt and angry:",
                f"The boncc count is {emotion.boncc_count}"
            )
        else:
            await embed_utils.replace(
                self.response_msg,
                "The snek is right",
                "Please, don't hit the snek"
            )

    async def cmd_refresh(self, msg_id: int):
        """
        ->type Other commands
        ->signature pg!refresh [message_id]
        ->description Refresh a message which support pages.
        -----
        Implement pg!refresh, to refresh a message which supports pages
        """
        try:
            msg = await self.invoke_msg.channel.fetch_message(msg_id)
        except (discord.errors.NotFound, discord.errors.HTTPException):
            await embed_utils.replace(
                self.response_msg,
                "Message not found",
                "Message was not found. Make sure that the id is correct and that "
                "you are in the same channel as the message."
            )
            return

        if not msg.embeds or not msg.embeds[0].footer or not msg.embeds[0].footer.text:
            await embed_utils.replace(
                self.response_msg,
                "Message does not support pages",
                "The message specified does not support pages. Make sure "
                "the id of the message is correct."
            )
            return

        data = msg.embeds[0].footer.text.split("\n")

        page = re.search(r'\d+', data[0]).group()
        command = data[2].replace("Command: ", "").split()

        if not page or not command or not self.cmds_and_funcs.get(command[0]):
            await embed_utils.replace(
                self.response_msg,
                "Message does not support pages",
                "The message specified does not support pages. Make sure "
                "the id of the message is correct."
            )
            return

        await self.response_msg.delete()
        await self.invoke_msg.delete()

        if command[0] == "help":
            if len(command) == 1:
                command.append(None)

            await self._cmd_help(
                command[1], page=int(page) - 1, msg=msg
            )
        elif command[0] == "doc":
            await self._cmd_doc(
                command[1], page=int(page) - 1, msg=msg
            )

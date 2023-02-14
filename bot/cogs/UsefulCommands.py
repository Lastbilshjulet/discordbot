from discord.ext import commands
import discord
import typing as t


class NoVoiceChannel(commands.CommandError):
    pass


class UsefulCommands(commands.Cog):

    # --------------------
    #
    #       Commands
    #
    # --------------------

    # Purge

    @commands.command(name="purge", help="Purge messages from the channel by the value provided. ")
    @commands.has_any_role("Supreme leader", "COMP")
    async def purge_command(self, ctx, arg):
        if arg.isdigit() == False:
            await ctx.message.reply("You must declare a value. :slight_smile:", delete_after=300)
        else:
            if int(arg) >= 100:
                await ctx.message.reply("Value must be under 100.", delete_after=300)
            elif int(arg) < 1:
                await ctx.message.reply("Value must be over 0.", delete_after=300)
            else:
                await ctx.message.channel.purge(limit=int(arg)+1)

    @purge_command.error
    async def purge_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.message.reply("You do not have the correct role for this command.", delete_after=300)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.reply("You need to provide a value for the number of messages to be deleted. ", delete_after=300)
        await ctx.message.delete()

    # Icon

    @commands.command(name="icon", help="Links your icon. ")
    async def icon_command(self, ctx, mention: t.Optional[str]):
        if mention is not None and len(ctx.message.mentions) > 0:
            await ctx.send(ctx.message.mentions[0].display_avatar)
        else:
            await ctx.send(ctx.author.display_avatar)
        await ctx.message.delete()

    # Invite

    @commands.command(name="invite", help="Sends a private message with an invite link to the bot. ")
    async def invite_command(self, ctx):
        invite_link = "https://discord.com/api/oauth2/authorize?client_id=880345602741899264&permissions=8&scope=bot"

        await ctx.send(content=invite_link, ephemeral=True)

        await ctx.message.delete()

    # Bonkmonk

    @commands.command(name="bonkmonk", help="Bonks the Monks. ")
    @commands.has_role("bonkers")
    async def bonkmonk_command(self, ctx, mention: t.Optional[str]):
        mention_id = 183521952210616320
        if len(ctx.message.mentions) == 1:
            mention_id = ctx.message.mentions[0].id

        if ctx.author.voice is None:
            raise NoVoiceChannel

        ch = None
        for channel in ctx.author.guild.voice_channels:
            if channel.id == 419111668803698699:
                ch = channel

        message = None
        for member in ctx.author.voice.channel.members:
            if member.id == mention_id:
                await member.move_to(channel=ch, reason="Bonk")
                print(ctx.author, " tried to bonk ", member, ". ")
                message = await ctx.send(content=f"You just got bonked, <@{mention_id}>")
                await ctx.send(content="https://tenor.com/view/bonk-gif-18805247")

        if message is None:
            await ctx.send(f"Psst <@{mention_id}>, <@{ctx.author.id}> tried to bonk you. ")
            print(ctx.author, " tried to bonk ", mention, ". ")

        await ctx.message.delete()

    @bonkmonk_command.error
    async def bonkmonk_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.message.reply("You do not have the correct role for this command.", delete_after=300)
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.message.reply("You do not have the permission to use bonkmonk.", delete_after=300)
        if isinstance(error, NoVoiceChannel):
            await ctx.message.reply("You need to be in a voice channel to bonk the monk. ", delete_after=300)
        print(ctx.author, " tried to bonk the monk. ")
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(UsefulCommands(bot))

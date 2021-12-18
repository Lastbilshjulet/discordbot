from discord.ext import commands
import discord
import typing as t


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
            await ctx.message.reply("You must declare a value. :slight_smile:")
        else:
            if int(arg) >= 100:
                await ctx.message.reply("Value must be under 100.")
            elif int(arg) < 1:
                await ctx.message.reply("Value must be over 0.")
            else:
                await ctx.message.channel.purge(limit=int(arg)+1)

    @purge_command.error
    async def purge_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.message.reply("You do not have the correct role for this command.")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.reply("You need to provide a value for the number of messages to be deleted. ")
        await ctx.message.delete()

    # Icon

    @commands.command(name="icon", help="Links your icon. ")
    async def icon_command(self, ctx, mention: t.Optional[str]):
        if mention is not None and len(ctx.message.mentions) > 0:
            await ctx.send(ctx.message.mentions[0].avatar_url)
        else:
            await ctx.send(ctx.author.avatar_url)
        await ctx.message.delete()

    # Bonkmonk

    @commands.command(name="bonkmonk", help="Bonks the Monks. ")
    @commands.has_role("bonkers")
    async def bonkmonk_command(self, ctx):
        if ctx.author.voice.channel is None:
            await ctx.message.reply("You need to be in a voice channel to use this command")

        ch = None
        for channel in ctx.author.guild.voice_channels:
            if channel.id == 419111668803698699:
                ch = channel

        for member in ctx.author.voice.channel.members:
            if member.id == 183521952210616320:
                await member.move_to(channel=ch, reason="Bonk")
                await ctx.send(content=f"You just got bonked, <@{183521952210616320}>")
                await ctx.send(content="https://tenor.com/view/bonk-gif-18805247")

        await ctx.message.delete()

    @bonkmonk_command.error
    async def bonkmonk_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.message.reply("You do not have the correct role for this command.")
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.message.reply("You do not have the permission to use bonkmonk.")
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(UsefulCommands(bot))


from discord.ext import commands


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

    # Icon

    @commands.command(name="icon", help="Links your icon. ")
    async def icon_command(self, ctx):
        await ctx.message.reply(ctx.author.avatar_url)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(UsefulCommands(bot))

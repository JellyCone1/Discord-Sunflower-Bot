# Discord Sunflower Bot v0.1.1
The repository for Hamsteria's Discord Server Custom Personal Bot for Moderation and Management.

## SAY HELLO TO SUNFLOWER! 🌻
Sunflower is a Custom Bot
Currently it has minimal functionalities like 
- deleting certain messages 
- give you an image's Pixel Count(Non Transparent)
- say hello to you

The command for Sunflower is `s!`
when sunflower is online, it means it is currently running on my pc in the terminal
i am looking into transitioning this script to run in a raspberry pi 5 to increase its uptime

here are some of the commands you can try:
- `s!hello`
- `s!reply <your-message>`
- `s!pc` along with an image attachment or an image URL
- `s!cf` -> CoinFlip
- `s!random <lower bound[int]> <upper bound[int]>` -> Outputs a random number between <Lower bound> and <Upper Bound> both incl.
- `s!purge <# of messages you want to delete> -> Deletes # number of messages` 

It also supports `{/}` commands!
Below are all the `{/}` commands which are available to use in this version.
- `/play <search_query or url>` -> only supports YT: To stream any yt video's Audio 
- `/pause` : Pause the current song
- `/skip` : Skip the current playing song
- `/resume`: Resume the paused song
- `/clear`: Clear the queue and stop the currently playing media
- `/disconnect`: Disconnect bot from same voice channel as the invoker

### ChangeLog:
**v0.1.1** 
- Added {/}`disconnect` which disconnects the bot from the Voice Channel.
- Renamed {/}`stop` to {/}`clear`, it does'nt disconnects from the channel anymore, instead just clears the queue and stops the current playing media.

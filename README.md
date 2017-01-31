# Little Server That Can
LSTC is designed for the use of a server for Scratch (http://scratch.mit.edu/ ). It's also designed in a way that you can
connect to different "plugins" allowing one person to play chat and another to play a multiplayer game without either of the
projects interfering with the other.

With a little modification (of the parsing and sending messages), you can use it with raw sockets for other projects made
outside of Scratch.

# Plugins
LSTC
- Chat.PY V3 (https://scratch.mit.edu/projects/2760607/)
- Bit Art (https://scratch.mit.edu/projects/2760603/)
- Virtual Space

LSTC Green
- Chat.PY V4

# History and Context
This was developed as part of a project I made on Scratch. Chat.PY specifically. It was the first, and only, of it's kind when
Scratch 1.3 and 1.4 was released. It was a project that allowed users to connect to a server through Scratch to chat with
other Scratch members. This was unusual because the were very few projects that used Scratch's Remote Sensor Connections
feature that enabled Scratch to communicate with external devices (the Scratch Board). After experimenting with the Python
code that they had available on their Wiki for Remote Sensor Connecitons I managed to send messages back and forth in a
server-client like manner.

About a year later I learned a lot about Python and built numerous things in it (IRC bots). After gaining experience there I
went back
to Scratch and wondered what I could do that was never done before. Networking and multiplayer was the top of my list and
since I wasn't super great at making games (art at least) I decided that I could make a simple chat program. The biggest
challenge that I had to overcome was making it easy for people to join in. No one would want to install Python and then run
the script I had created to proxy data from Scratch to my server. So I looked for a Py2Exe converter and created an EXE for it
which I then released as part of my project in December when I knew everyone would be on Christmas break. It was a hit and
made the front page on Scratch (https://scratch.mit.edu/projects/2234885/).

From there I created the plugin system. The chat was actually meant to be a demonstration of what you could do and the server
I had set up. I had created an API to save information and broadcast information to all connected users if they were subscribed.
As a demonstration of what it could do, I created Chat.PY. From there when Chat.PY became a hit I created new versions that
simulated an IRC environment. Because Scratch is a community for children (~8 to ~14) I decided to implement a profanity filter.
As part of that I also implemented spam protection because people would do a denial of service attack in the chat rooms which
at first crashed the server, but then after some optimizations and fixes on the server side it only crashed the clients that
were connected. At that point I prevented sending more than 5 messages in a second (or some other related number) which fixed
that issue.

Eventually to showcase the abilities of the server again I created a separate project where multiple users could draw
collaboratively (https://scratch.mit.edu/projects/2760603/). The backend server actually ran on the same server as Chat.PY which demonstrated how the server could be used
for multiple projects at once that all run independtly from each other, but still run on the same port that it was hosted on.

To further display the server's abilities I began working on a simple space dogfight simulator and was hoping to turn it into the first
Scratch MMORPG game, however I ran into performance issues on Scratch's side due to its inability to receive a large number
of packets (which would eventually crash Scratch). I was able to get a spaceship to fly around (maybe even two), but it
wasn't enough to spend further development on. The project that I used to test it is located here: https://scratch.mit.edu/projects/2272860/

While running this server I learned to manage a small community, handle trolls, bullies, hackers, Denial of Service attacks,
and other issues that arise from running a public chat server. I also learned marketing and timing in order to advertise the project
to help it reach front page in the most likely times since I only had one change to make it reach front page.
The project was taken down at one point because it broke
the Community Policies on Scratch, however I talked with the Scratch Team and explained why it followed the rules was able
to bring it back. A couple years later when Scratch 2.0 was released it was taken down again by a new moderator and at that
point I had moved on to other projects and decided that it was time to let it rest in peace. The server was also stable enough
to last numerous months without ever being monitored and only ever disconnected due to the VPS I was hosting it on having its
own troubles (as I was borrowing it to host the project on).

In the end this was probably my greatest learning experience in programming outside of my current MMORPG project. I gained
friends and it has led me to greater opportunities for which I am grateful for. I am impressed if you read this to the end.
Thank you!

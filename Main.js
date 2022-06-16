const Discord = require("discord.js");
const MessageHandling = require("./MessageHandling.js");
const CommandParser = require("./CommandParser");
const { stringify } = require("querystring");

const config = MessageHandling.getConfig();
const oauth = config["token"];

var client = new Discord.Client(config);

client.on('ready', () => {
    console.log('Connected');
});

client.on('message', (msg) => {
    if (msg.author.bot) {
        console.log("bot detected " + msg.content);
        return;
    }

    console.log(msg.content);
    CommandParser.checkCommands(msg, client);
    if (msg.content[0] !== "!") {
        MessageHandling.HandleMessage(msg, client);
    }

});

client.on('error', (err) =>{
    let me = client.users.cache.get("163041163408965632");
    let guilds = client.guilds.array();
    let dm = `Bot that is in: \n \`\`\`\n ${guilds} \n\`\`\` \n received error: \n \`\`\`\n ${err.message} \n\`\`\``;
    me.send(dm);
});

client.on('warn', (warning) => {
    let me = client.users.cache.get("163041163408965632");
    let guilds = client.guilds.array();
    let dm = `Bot that is in: \n \`\`\`\n ${guilds} \n\`\`\` \n received warning: \n \`\`\`\n ${warn.message} \n\`\`\``;
    me.send(dm);
});

client.login(oauth);



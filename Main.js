const MessageHandling = require("./MessageHandling.js");
const MarkovChain = require("./MarkovChain.js");
const fs = require("fs");

function correctChannel(channel, client) {
    commandChannels = MessageHandling.getConfig().commandChannel;
    if (commandChannels) {
        return (commandChannels.includes(channel.id));
    } else {
        return true;
    }
}

module.exports = {
    checkCommands : async function (msg, client) {
        const blacklist = MessageHandling.getBlacklist();
        const config = MessageHandling.getConfig();
        var text = msg.content;
        const noCommands = config["noCommands"];

        if (text[0] !== "!") {
            return;
        }
        try {
            if (config.blacklisted_users.includes(msg.author.id)) {
                return;
            }
        } catch (err) {}

        //If the command is !chain
        if (text.startsWith(`!chain`) && !noCommands && correctChannel(msg.channel, client)) {
            //Otherwise, make a chain based on the regular dataset
            let data = MessageHandling.getData();
            let markovData = data[0];
            let chunks = data[1];
            let startingWords = data[2];
            MessageHandling.send(MarkovChain.makeChain(markovData, chunks, startingWords,
                config.minChainLength, config.maxChainLength), msg.channel, client);

        //If the command is blacklist
        } else if (text.startsWith(`!blacklist`) && config.admins.indexOf(msg.author.id) > -1 && correctChannel(msg.channel, client)) {
            var command = msg.content.split(" ");
            //For adding to the blacklist
            if (command[1] == "add") {
                if (command[2] == "word") {
                    let word = command[3];
                    blacklist.singleWords.push(word);
                    MessageHandling.send(`Added the word "${word}" to the blacklist`, msg.channel, client);

                } else if (command[2] == "phrase") {
                    let phrase = command.slice(3).join(" ");
                    blacklist.fullPhrases.push(phrase);
                    MessageHandling.send(`Added the phrase "${phrase}" to the blacklist`, msg.channel, client);

                } else if (command [2] == "regex") {
                    let regex = command[3];
                    blacklist.regex.push(regex);
                    MessageHandling.send(`Added the regular expression "${regex}" to the blacklist`, msg.channel, client);
                }
            //For removing from the blacklist
            } else if (command[1] == "remove") {
                if (command[2] == "word") {
                    let word = command[3];
                    let index = blacklist.singleWords.indexOf(command[3]);
                    if (index > -1) {
                        blacklist.singleWords.splice(index);
                        MessageHandling.send(`Removed the word "${word}" from the blacklist`, msg.channel, client);
                    } else {
                        MessageHandling.send(`${word} is not a word in the blacklist!`, msg.channel, client);
                    }

                } else if (command[2] == "phrase") {
                    let phrase = command.slice(3).join(" ");
                    let index = blacklist.fullPhrases.indexOf(command[3]);
                    if (index > -1) {
                        blacklist.fullPhrases.splice(index);
                        MessageHandling.send(`Removed the phrase "${phrase}" from the blacklist`, msg.channel, client);
                    } else {
                        MessageHandling.send(`${phrase} is not a phrase in the blacklist!`, msg.channel, client);
                    }

                } else if (command [2] == "regex") {
                    let regex = command[3];
                    let index = blacklist.regex.indexOf(command[3]);
                    if (index > -1) {
                        blacklist.regex.splice(index);
                        MessageHandling.send(`Removed the regular expression "${regex}" from the blacklist`, msg.channel, client);
                    } else {
                        MessageHandling.send(`${regex} is not a regular expression in the blacklist!`, msg.channel, client);
                    }
                }
                } else {
                    MessageHandling.send(`That is not the correct syntax for that command. Please refer to the !help command for help`, msg.channel, client);
                }
                MessageHandling.clearCache();
                MessageHandling.setBlacklist(blacklist);
                fs.writeFile("blacklist.json", JSON.stringify(blacklist), (err) => {
                    if (err) {
                        throw err;
                     }
                    // success case, the file was saved
                    MessageHandling.send("Blacklist updated", msg.channel, client);
                });
            } else if (text.startsWith(`!clear`) && config.admins.indexOf(msg.author.id) > -1 && correctChannel(msg.channel, client)) {
                msg.channel.startTyping()
                MessageHandling.clearCache();
                MessageHandling.send("Cache cleared", msg.channel, client);
            } else if (text.startsWith(`!help`) && !noCommands && correctChannel(msg.channel, client)) {
                var helpText = fs.readFileSync("HelpFile.txt", "utf8");
                MessageHandling.send(helpText, msg.channel, client);
        }
    }
}

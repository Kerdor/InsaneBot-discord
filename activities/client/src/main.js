import { DiscordSDK } from "@discord/embedded-app-sdk";

const clientId = import.meta.env.VITE_DISCORD_CLIENT_ID;

if (!clientId) {
    throw new Error("VITE_DISCORD_CLIENT_ID is not configured");
}

const discordSdk = new DiscordSDK(clientId);

async function authenticate() {
    await discordSdk.ready();

    const { code } = await discordSdk.commands.authorize({
        client_id: clientId,
        response_type: "code",
        state: "insanebot",
        prompt: "none",
        scope: ["identify"],
    });

    const response = await fetch("/api/discord/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
    });

    if (!response.ok) {
        throw new Error(`Discord authentication failed: ${response.status}`);
    }

    const { access_token: accessToken } = await response.json();

    await discordSdk.commands.authenticate({
        access_token: accessToken,
    });
}

async function start() {
    await authenticate();
    document.body.textContent = "InsaneBot Activity connected";
}

start().catch((error) => {
    console.error(error);
    document.body.textContent = `Activity connection failed: ${error.message}`;
});

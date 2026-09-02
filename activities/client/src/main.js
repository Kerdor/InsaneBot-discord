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
        credentials: "include",
        body: JSON.stringify({ code }),
    });

    if (!response.ok) {
        throw new Error(`Discord authentication failed: ${response.status}`);
    }

    const { access_token: accessToken } = await response.json();
    const authentication = await discordSdk.commands.authenticate({
        access_token: accessToken,
    });

    return authentication.user;
}

async function loadSession() {
    const response = await fetch("/api/discord/session", {
        method: "GET",
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(`Activity session failed: ${response.status}`);
    }

    return response.json();
}

async function start() {
    const user = await authenticate();
    const session = await loadSession();

    if (session.user_id !== String(user.id)) {
        throw new Error("Activity session identity mismatch");
    }

    document.body.textContent = `InsaneBot Activity connected as ${user.username}`;
}

start().catch((error) => {
    console.error(error);
    document.body.textContent = `Activity connection failed: ${error.message}`;
});

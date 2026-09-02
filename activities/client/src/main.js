import { DiscordSDK } from "@discord/embedded-app-sdk";
import { SnakeGame, bindSnakeControls } from "./snake.js";
import "./style.css";

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
    return discordSdk.commands.authenticate({
        access_token: accessToken,
    });
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

function renderGame(user) {
    document.body.innerHTML = `
        <main class="activity-shell">
            <section class="game-card">
                <header class="game-header">
                    <div>
                        <p class="eyebrow">INSANEBOT ACTIVITY</p>
                        <h1>🐍 Snake</h1>
                        <p class="status" id="status">Нажми «Старт» или стрелку</p>
                    </div>
                    <div class="score-box">
                        <span>Счёт</span>
                        <strong id="score">0</strong>
                    </div>
                </header>

                <canvas id="snake-canvas" width="600" height="600" aria-label="Snake game"></canvas>

                <div class="controls">
                    <button id="start-button" type="button">Старт</button>
                    <button id="restart-button" type="button">Новая игра</button>
                </div>

                <p class="player">Игрок: <strong>${escapeHtml(user.username)}</strong></p>
            </section>
        </main>
    `;

    const canvas = document.querySelector("#snake-canvas");
    const score = document.querySelector("#score");
    const status = document.querySelector("#status");
    const game = new SnakeGame(canvas, score, status);

    bindSnakeControls(game);
    document.querySelector("#start-button").addEventListener("click", () => game.start());
    document.querySelector("#restart-button").addEventListener("click", () => {
        game.stop();
        game.reset();
    });
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function start() {
    const authentication = await authenticate();
    const session = await loadSession();

    if (session.user_id !== String(authentication.user.id)) {
        throw new Error("Activity session identity mismatch");
    }

    renderGame(authentication.user);
}

start().catch((error) => {
    console.error(error);
    document.body.innerHTML = `<main class="error-screen"><h1>Activity connection failed</h1><p>${escapeHtml(error.message)}</p></main>`;
});

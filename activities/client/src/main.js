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
        body: JSON.stringify({
            code,
            instance_id: discordSdk.instanceId,
            guild_id: discordSdk.guildId,
            channel_id: discordSdk.channelId,
        }),
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

async function startSnakeGame() {
    const response = await fetch("/api/activities/snake/start", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            instance_id: discordSdk.instanceId,
            guild_id: discordSdk.guildId,
            channel_id: discordSdk.channelId,
        }),
    });

    if (!response.ok) {
        throw new Error(`Snake game start failed: ${response.status}`);
    }

    return response.json();
}

async function submitSnakeResult(result) {
    const response = await fetch("/api/activities/snake/result", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            game_id: result.game_id,
            result_id: result.result_id,
            activity_key: "snake",
            score: result.score,
            reason: result.reason,
            tick_count: result.tick_count,
            seed: result.seed,
            inputs: result.inputs,
            instance_id: discordSdk.instanceId,
            guild_id: discordSdk.guildId,
            channel_id: discordSdk.channelId,
        }),
    });

    if (!response.ok) {
        throw new Error(`Snake result submission failed: ${response.status}`);
    }

    return response.json();
}

function renderGame(user, initialGame) {
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
    const game = new SnakeGame(canvas, score, status, async (result) => {
        try {
            status.textContent = "Результат отправляется...";
            await submitSnakeResult(result);
            status.textContent = result.reason === "win"
                ? "Победа! Результат принят"
                : "Игра окончена — результат принят";
        } catch (error) {
            console.error(error);
            status.textContent = "Результат не принят сервером";
        }
    });

    game.reset(initialGame.seed, initialGame.game_id);
    game.resultId = initialGame.result_id;

    bindSnakeControls(game);
    document.querySelector("#start-button").addEventListener("click", () => game.start());
    document.querySelector("#restart-button").addEventListener("click", async () => {
        try {
            status.textContent = "Создание новой игры...";
            const nextGame = await startSnakeGame();
            game.reset(nextGame.seed, nextGame.game_id);
            game.resultId = nextGame.result_id;
        } catch (error) {
            console.error(error);
            status.textContent = "Не удалось создать новую игру";
        }
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
    if (session.instance_id !== discordSdk.instanceId) {
        throw new Error("Activity instance identity mismatch");
    }
    if (session.guild_id !== discordSdk.guildId) {
        throw new Error("Activity guild identity mismatch");
    }
    if (session.channel_id !== discordSdk.channelId) {
        throw new Error("Activity channel identity mismatch");
    }

    const initialGame = await startSnakeGame();
    renderGame(authentication.user, initialGame);
}

start().catch((error) => {
    console.error(error);
    document.body.innerHTML = `<main class="error-screen"><h1>Activity connection failed</h1><p>${escapeHtml(error.message)}</p></main>`;
});

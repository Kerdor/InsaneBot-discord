import { DiscordSDK } from "@discord/embedded-app-sdk";
import { SnakeGame, bindSnakeControls } from "./snake.js";
import "./style.css";

const clientId = import.meta.env.VITE_DISCORD_CLIENT_ID;

function activityLog(message, data = null) {
    const entry = {
        time: new Date().toISOString(),
        message,
        ...(data === null ? {} : { data }),
    };
    console.log("[ACTIVITY]", JSON.stringify(entry));
    fetch("/api/activity/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(entry),
        keepalive: true,
    }).catch(() => {});
}

window.addEventListener("error", (event) => {
    activityLog("window.error", {
        message: event.message,
        source: event.filename,
        line: event.lineno,
        column: event.colno,
    });
});

window.addEventListener("unhandledrejection", (event) => {
    activityLog("unhandledrejection", {
        message: event.reason instanceof Error ? event.reason.message : String(event.reason),
    });
});

if (!clientId) {
    activityLog("VITE_DISCORD_CLIENT_ID is not configured");
    throw new Error("VITE_DISCORD_CLIENT_ID is not configured");
}

const discordSdk = new DiscordSDK(clientId);
activityLog("SDK created", { clientId });

const ACTIVITIES = [
    {
        key: "snake",
        name: "Snake",
        icon: "🐍",
        description: "Классическая змейка с серверной проверкой результата.",
        status: "available",
    },
    {
        key: "sudoku",
        name: "Sudoku",
        icon: "🔢",
        description: "Логическая головоломка.",
        status: "coming_soon",
    },
    {
        key: "wordle",
        name: "Wordle",
        icon: "🟩",
        description: "Угадай слово за ограниченное число попыток.",
        status: "coming_soon",
    },
    {
        key: "2048",
        name: "2048",
        icon: "🔲",
        description: "Объединяй плитки и набирай очки.",
        status: "future",
    },
    {
        key: "minesweeper",
        name: "Minesweeper",
        icon: "💣",
        description: "Найди безопасные клетки.",
        status: "future",
    },
    {
        key: "tetris",
        name: "Tetris",
        icon: "🧱",
        description: "Собирай линии из падающих фигур.",
        status: "future",
    },
];

async function authenticate() {
    activityLog("authenticate: waiting for SDK ready");
    await discordSdk.ready();
    activityLog("authenticate: SDK ready", {
        instanceId: discordSdk.instanceId,
        guildId: discordSdk.guildId,
        channelId: discordSdk.channelId,
    });

    activityLog("authenticate: requesting authorize");
    const { code } = await discordSdk.commands.authorize({
        client_id: clientId,
        response_type: "code",
        state: "insanebot",
        prompt: "none",
        scope: ["identify"],
    });
    activityLog("authenticate: authorize completed", { hasCode: Boolean(code) });

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
    activityLog("authenticate: token endpoint response", { status: response.status });

    if (!response.ok) {
        throw new Error(`Discord authentication failed: ${response.status}`);
    }

    const { access_token: accessToken } = await response.json();
    activityLog("authenticate: token received", { hasAccessToken: Boolean(accessToken) });
    const authentication = await discordSdk.commands.authenticate({
        access_token: accessToken,
    });
    activityLog("authenticate: SDK authentication completed", {
        userId: authentication.user?.id,
        username: authentication.user?.username,
    });
    return authentication;
}

async function loadSession() {
    activityLog("session: requesting backend session");
    const response = await fetch("/api/discord/session", {
        method: "GET",
        credentials: "include",
    });
    activityLog("session: backend response", { status: response.status });

    if (!response.ok) {
        throw new Error(`Activity session failed: ${response.status}`);
    }

    const session = await response.json();
    activityLog("session: loaded", {
        userId: session.user_id,
        instanceId: session.instance_id,
        guildId: session.guild_id,
        channelId: session.channel_id,
    });
    return session;
}

async function startSnakeGame() {
    activityLog("snake: requesting new game");
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
    activityLog("snake: start endpoint response", { status: response.status });

    if (!response.ok) {
        throw new Error(`Snake game start failed: ${response.status}`);
    }

    const game = await response.json();
    activityLog("snake: game created", {
        gameId: game.game_id,
        resultId: game.result_id,
    });
    return game;
}

async function submitSnakeResult(result) {
    activityLog("snake: submitting result", {
        gameId: result.game_id,
        resultId: result.result_id,
        score: result.score,
        reason: result.reason,
        tickCount: result.tick_count,
    });
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
    activityLog("snake: result endpoint response", { status: response.status });

    if (!response.ok) {
        throw new Error(`Snake result submission failed: ${response.status}`);
    }

    const submitted = await response.json();
    activityLog("snake: result accepted", submitted);
    return submitted;
}

function renderLauncher(user) {
    activityLog("ui: rendering launcher", { username: user.username });
    document.body.innerHTML = `
        <main class="activity-shell">
            <section class="launcher-card">
                <header class="launcher-header">
                    <div>
                        <p class="eyebrow">INSANEBOT ACTIVITY</p>
                        <h1>Игры</h1>
                        <p class="launcher-subtitle">Выбери игру и играй прямо в Discord.</p>
                    </div>
                    <div class="player-badge">${escapeHtml(user.username)}</div>
                </header>

                <div class="activity-grid">
                    ${ACTIVITIES.map(renderActivityCard).join("")}
                </div>
            </section>
        </main>
    `;

    document.querySelectorAll("[data-activity-key]").forEach((card) => {
        if (card.dataset.status !== "available") {
            return;
        }
        card.addEventListener("click", () => {
            const activityKey = card.dataset.activityKey;
            activityLog("ui: activity selected", { activityKey });
            if (activityKey === "snake") {
                openSnake(user).catch(showError);
            }
        });
    });
}

function renderActivityCard(activity) {
    const statusLabel = activity.status === "available"
        ? "Играть"
        : activity.status === "coming_soon"
            ? "Скоро"
            : "В планах";
    const disabledClass = activity.status === "available" ? "" : " activity-card-disabled";

    return `
        <button
            class="activity-card${disabledClass}"
            type="button"
            data-activity-key="${activity.key}"
            data-status="${activity.status}"
            ${activity.status === "available" ? "" : "disabled"}
        >
            <span class="activity-icon">${activity.icon}</span>
            <span class="activity-card-content">
                <strong>${escapeHtml(activity.name)}</strong>
                <span>${escapeHtml(activity.description)}</span>
            </span>
            <span class="activity-status activity-status-${activity.status}">${statusLabel}</span>
        </button>
    `;
}

async function openSnake(user) {
    const initialGame = await startSnakeGame();
    renderGame(user, initialGame);
}

function renderGame(user, initialGame) {
    activityLog("ui: rendering Snake", { gameId: initialGame.game_id });
    document.body.innerHTML = `
        <main class="activity-shell">
            <section class="game-card">
                <div class="game-topbar">
                    <button id="back-button" class="back-button" type="button">← Игры</button>
                </div>

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
            activityLog("snake: result submission failed", { message: error.message });
            status.textContent = "Результат не принят сервером";
        }
    });

    game.reset(initialGame.seed, initialGame.game_id, initialGame.result_id);

    bindSnakeControls(game);
    document.querySelector("#start-button").addEventListener("click", () => game.start());
    document.querySelector("#restart-button").addEventListener("click", async () => {
        try {
            status.textContent = "Создание новой игры...";
            const nextGame = await startSnakeGame();
            game.reset(nextGame.seed, nextGame.game_id, nextGame.result_id);
        } catch (error) {
            console.error(error);
            activityLog("snake: restart failed", { message: error.message });
            status.textContent = "Не удалось создать новую игру";
        }
    });
    document.querySelector("#back-button").addEventListener("click", () => {
        activityLog("ui: returning to launcher");
        renderLauncher(user);
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

function showError(error) {
    console.error(error);
    activityLog("ui: fatal error", { name: error.name, message: error.message, stack: error.stack });
    document.body.innerHTML = `<main class="error-screen"><h1>Activity error</h1><p>${escapeHtml(error.message)}</p></main>`;
}

async function start() {
    activityLog("startup: begin");
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

    activityLog("startup: identity checks passed");
    renderLauncher(authentication.user);
    activityLog("startup: launcher rendered");
}

start().catch((error) => {
    console.error(error);
    activityLog("startup: fatal error", { name: error.name, message: error.message, stack: error.stack });
    document.body.innerHTML = `<main class="error-screen"><h1>Activity connection failed</h1><p>${escapeHtml(error.message)}</p></main>`;
});

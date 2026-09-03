import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");
    const clientId = env.VITE_DISCORD_CLIENT_ID || env.DISCORD_ACTIVITY_CLIENT_ID || "";

    return {
        define: {
            "import.meta.env.VITE_DISCORD_CLIENT_ID": JSON.stringify(clientId),
        },
        server: {
            allowedHosts: true,
            proxy: {
                "/api": "http://127.0.0.1:8080",
            },
        },
    };
});

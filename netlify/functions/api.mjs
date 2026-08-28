import { processChat } from "../lib/chat.mjs";
import { getSettings } from "../lib/gigachat.mjs";

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}

function routePath(req) {
  const path = new URL(req.url).pathname.replace(/\/$/, "") || "/";
  return path.replace(/^\/\.netlify\/functions\/[^/]+/, "") || path;
}

function isRoute(path, suffix) {
  return path === suffix || path.endsWith(suffix);
}

export default async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("", { status: 204, headers: JSON_HEADERS });
  }

  const path = routePath(req);

  try {
    if (isRoute(path, "/health") && req.method === "GET") {
      const settings = getSettings();
      return json({
        status: "ok",
        service: "resume-designer",
        version: "0.1.0",
        gigachat_stub: settings.useStub,
        gigachat_configured: settings.configured,
      });
    }

    if (isRoute(path, "/api/v1/chat") && req.method === "POST") {
      const body = await req.json();
      return json(await processChat(body));
    }

    if (isRoute(path, "/api/v1/interview") && req.method === "POST") {
      const payload = await req.json();
      const answersText = Object.entries(payload.answers || {})
        .map(([question, answer]) => `Q: ${question}\nA: ${answer}`)
        .join("\n");
      return json(
        await processChat({
          session_id: payload.session_id,
          message: { text: `Интервью — ответы пользователя:\n${answersText}` },
          resume: payload.resume,
          intent_hint: "create_resume",
        }),
      );
    }

    if (isRoute(path, "/session/reset") && req.method === "POST") {
      return json({ ok: true });
    }

    return json({ detail: `Нет обработчика для ${req.method} ${path}` }, 404);
  } catch (error) {
    return json({ detail: error.message || "Internal error" }, error.status || 500);
  }
};

export const config = {
  path: ["/api/v1/chat", "/api/v1/interview", "/session/reset", "/health"],
};

import https from "node:https";
import { randomUUID } from "node:crypto";

function envFlag(name, fallback) {
  const value = process.env[name];
  if (value == null || value === "") return fallback;
  return !["false", "0", "no", "off"].includes(String(value).toLowerCase());
}

export function getSettings() {
  const apiKey = process.env.GIGACHAT_API_KEY || "";
  const authKey = process.env.GIGACHAT_AUTH_KEY || process.env.GIGACHAT_AUTH_BASIC || "";
  const clientId = process.env.GIGACHAT_CLIENT_ID || "";
  const clientSecret = process.env.GIGACHAT_CLIENT_SECRET || "";
  const configured = Boolean(apiKey || authKey || (clientId && clientSecret));
  const useStub = envFlag("GIGACHAT_USE_STUB", true);
  const active = configured && (apiKey ? true : !useStub);

  return {
    apiKey,
    authKey,
    clientId,
    clientSecret,
    configured,
    useStub,
    active,
    verifySsl: envFlag("GIGACHAT_VERIFY_SSL", false),
    scope: process.env.GIGACHAT_SCOPE || "GIGACHAT_API_PERS",
    authUrl: process.env.GIGACHAT_AUTH_URL || "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    apiUrl: process.env.GIGACHAT_API_URL || "https://gigachat.devices.sberbank.ru/api/v1",
    model: process.env.GIGACHAT_MODEL || "GigaChat",
    modelLight: process.env.GIGACHAT_MODEL_LIGHT || "GigaChat-2",
    modelHeavy: process.env.GIGACHAT_MODEL_HEAVY || "GigaChat-2-Pro",
  };
}

function requestHttps({ url, method, headers, body, rejectUnauthorized, timeoutMs }) {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const payload = body ? Buffer.from(body) : null;
    const req = https.request(
      {
        hostname: target.hostname,
        port: target.port || 443,
        path: `${target.pathname}${target.search}`,
        method,
        headers: {
          ...headers,
          ...(payload ? { "Content-Length": String(payload.length) } : {}),
        },
        rejectUnauthorized,
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          resolve({
            status: res.statusCode || 500,
            text: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );
    req.on("error", reject);
    req.setTimeout(timeoutMs || 25000, () => {
      req.destroy(new Error("GigaChat timeout"));
    });
    if (payload) req.write(payload);
    req.end();
  });
}

let cachedToken = null;
let cachedTokenExpires = 0;

async function getAccessToken(settings) {
  if (settings.apiKey) return settings.apiKey;

  if (cachedToken && Date.now() + 30_000 < cachedTokenExpires) {
    return cachedToken;
  }

  let basic = settings.authKey;
  if (!basic && settings.clientId && settings.clientSecret) {
    basic = Buffer.from(`${settings.clientId}:${settings.clientSecret}`).toString("base64");
  }
  if (basic && basic.toLowerCase().startsWith("basic ")) {
    basic = basic.slice(6).trim();
  }
  if (!basic) {
    throw new Error("Не заданы GIGACHAT_AUTH_KEY / GIGACHAT_CLIENT_ID+SECRET");
  }

  const response = await requestHttps({
    url: settings.authUrl.replace(/\/$/, ""),
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
      RqUID: randomUUID(),
      Authorization: `Basic ${basic}`,
    },
    body: new URLSearchParams({ scope: settings.scope }).toString(),
    rejectUnauthorized: settings.verifySsl,
    timeoutMs: 15000,
  });

  if (response.status >= 400) {
    throw new Error(`OAuth GigaChat ${response.status}: ${response.text.slice(0, 400)}`);
  }

  const payload = JSON.parse(response.text);
  const token = payload.access_token || payload.accessToken || payload.token;
  if (!token) throw new Error("OAuth не вернул access_token");

  cachedToken = token;
  cachedTokenExpires = Date.now() + Number(payload.expires_in || payload.expiresIn || 1800) * 1000;
  return token;
}

export async function completeChat({ messages, model }) {
  const settings = getSettings();
  if (!settings.active) {
    const userText = [...messages].reverse().find((item) => item.role === "user")?.content || "";
    const preview = userText.length > 200 ? `${userText.slice(0, 200)}…` : userText;
    return {
      content:
        "[STUB] Ответ GigaChat будет здесь после подключения API.\n\n" +
        `Ваш запрос: «${preview}»\n\n` +
        "Рекомендации (демо):\n" +
        "• Добавьте количественные результаты в блок «Опыт»\n" +
        "• Уточните целевую должность в начале резюме\n" +
        "• Проверьте орфографию и единый стиль формулировок",
      model: "GigaChat-stub",
      stub: true,
    };
  }

  const token = await getAccessToken(settings);
  const url = `${settings.apiUrl.replace(/\/$/, "")}/chat/completions`;
  const response = await requestHttps({
    url,
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      model: model || settings.model,
      messages,
      temperature: 0.3,
      max_tokens: 2048,
    }),
    rejectUnauthorized: settings.verifySsl,
    timeoutMs: 24000,
  });

  if (response.status >= 400) {
    throw new Error(`GigaChat ${response.status}: ${response.text.slice(0, 500)}`);
  }

  const data = JSON.parse(response.text);
  return {
    content: data.choices[0].message.content,
    model: data.model || model || settings.model,
    stub: false,
  };
}

import { randomUUID } from "node:crypto";

import { completeChat, getSettings } from "./gigachat.mjs";
import { SYSTEM_PROMPT, buildUserPrompt } from "./prompts.mjs";

const COMPLEX_INTENTS = new Set(["analyze_resume", "create_resume", "improve_section"]);
const COMPLEX_KEYWORDS = [
  "исправь",
  "перепиши",
  "составь",
  "полностью",
  "детально",
  "улучши",
  "структуриру",
  "интервью",
  "метрик",
  "результат",
];

function detectIntent(body) {
  if (body.intent_hint) return body.intent_hint;
  const text = String(body.message?.text || "").toLowerCase();
  if (["анализ", "оцени", "проверь", "разбор"].some((word) => text.includes(word))) {
    return "analyze_resume";
  }
  if (["создай", "составь", "напиши", "резюме"].some((word) => text.includes(word))) {
    return "create_resume";
  }
  return "general_question";
}

function buildResumeContext(resume) {
  if (!resume) return "";
  const parts = [];
  if (resume.target_role) parts.push(`Цель: ${resume.target_role}`);
  if (resume.raw_text) parts.push(resume.raw_text);
  const labels = {
    personal_info: "Личная информация",
    location: "Город",
    citizenship: "Гражданство",
    target_position: "Желаемая должность и зарплата",
    work_experience: "Опыт работы",
    education: "Образование",
    about_me: "Обо мне",
    languages: "Иностранные языки",
  };
  for (const [key, value] of Object.entries(resume.sections || {})) {
    if (value) parts.push(`${labels[key] || key}: ${value}`);
  }
  return parts.join("\n");
}

function selectModel(intent, userMessage, resumeText) {
  const settings = getSettings();
  const complex =
    COMPLEX_INTENTS.has(intent) ||
    COMPLEX_KEYWORDS.some((word) => userMessage.toLowerCase().includes(word)) ||
    (resumeText && (resumeText.length > 400 || resumeText.split("\n").length >= 8));
  return complex
    ? { model: settings.modelHeavy, tier: "heavy" }
    : { model: settings.modelLight, tier: "light" };
}

function parseRecommendations(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^[•\-*]\s+/.test(line))
    .slice(0, 5)
    .map((line) => ({
      section: "summary",
      priority: "medium",
      suggestion: line.replace(/^[•\-*]\s+/, ""),
    }));
}

export async function processChat(body) {
  const sessionId = body.session_id || randomUUID();
  const userMessage = String(body.message?.text || "").trim();
  if (!userMessage) {
    const error = new Error("Пустое сообщение");
    error.status = 400;
    throw error;
  }

  const intent = detectIntent(body);
  const resumeContext = buildResumeContext(body.resume);
  const resumeText = body.resume?.raw_text || null;
  const { model, tier } = selectModel(intent, userMessage, resumeText);
  const userPrompt = buildUserPrompt(intent, {
    userMessage,
    resumeText,
    targetRole: body.resume?.target_role,
    resumeContext,
  });

  let completion;
  try {
    completion = await completeChat({
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      model,
    });
  } catch (error) {
    return {
      session_id: sessionId,
      status: "upstream_error",
      reply: {
        text: `Ошибка при обращении к GigaChat: ${error.message}`,
        intent,
        recommendations: [],
        resume_draft: body.resume || null,
        followup_questions: [],
      },
      model: "n/a",
      stub: false,
      processed_at: new Date().toISOString(),
      debug: { error: error.message },
    };
  }

  const followup = completion.content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.endsWith("?") && line.length > 3);

  return {
    session_id: sessionId,
    status: completion.stub ? "stub_response" : "success",
    reply: {
      text: completion.content,
      intent,
      recommendations: parseRecommendations(completion.content),
      resume_draft: body.resume || null,
      followup_questions: followup,
    },
    model: completion.model,
    stub: completion.stub,
    processed_at: new Date().toISOString(),
    debug: {
      prompt_name: intent,
      model_tier: tier,
      model_requested: model,
    },
  };
}

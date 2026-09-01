import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SECTION_LABELS = {
  personal_info: "Личные данные",
  location: "Город и гражданство",
  citizenship: "Гражданство",
  target_position: "Желаемая должность",
  work_experience: "Опыт работы",
  education: "Образование",
  about_me: "Обо мне",
  languages: "Языки и права",
  skills: "Навыки",
};

const LOOKALIKES = {
  ё: "е",
  x: "х",
  y: "у",
};

function loadRules() {
  const here = dirname(fileURLToPath(import.meta.url));
  const raw = readFileSync(join(here, "moderation-rules.json"), "utf8");
  return JSON.parse(raw);
}

const RULES = loadRules();
const COMPILED = RULES.patterns.map((item) => ({
  category: item.category,
  pattern: new RegExp(item.pattern, "iu"),
}));

function normalizeWithMap(text) {
  const lowered = String(text)
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[xy]/g, (char) => LOOKALIKES[char] || char);
  const chars = [];
  const mapping = [];
  for (let i = 0; i < lowered.length; i += 1) {
    const ch = lowered[i];
    if (
      chars.length &&
      i + 1 < lowered.length &&
      ".-*_".includes(ch) &&
      /[а-яa-z]/.test(chars[chars.length - 1]) &&
      /[а-яa-z]/.test(lowered[i + 1])
    ) {
      continue;
    }
    chars.push(ch);
    mapping.push(i);
  }
  return { normalized: chars.join(""), mapping };
}

function excerpt(original, start, end) {
  const masked = `${original.slice(0, start)}***${original.slice(end)}`;
  const left = Math.max(0, start - 28);
  const right = Math.min(masked.length, start + 32);
  let snippet = masked.slice(left, right).replace(/\n/g, " ").trim();
  if (left > 0) snippet = `…${snippet}`;
  if (right < masked.length) snippet = `${snippet}…`;
  return snippet;
}

export function scanText(text, location) {
  if (!text || !String(text).trim()) return [];
  const original = String(text);
  const { normalized, mapping } = normalizeWithMap(original);
  const hits = [];
  const seen = new Set();
  for (const item of COMPILED) {
    const match = normalized.match(item.pattern);
    if (!match || match.index == null) continue;
    const key = `${item.category}:${location}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const start = mapping[match.index] ?? 0;
    const endIndex = match.index + match[0].length - 1;
    const end = (mapping[endIndex] ?? start) + 1;
    hits.push({
      category: item.category,
      location,
      excerpt: excerpt(original, start, end),
    });
  }
  return hits;
}

function collectParts(body) {
  const parts = [];
  const resume = body?.resume || {};
  if (resume.target_role) parts.push(["желаемая должность", resume.target_role]);
  for (const [key, value] of Object.entries(resume.sections || {})) {
    if (value) parts.push([SECTION_LABELS[key] || key, value]);
  }
  if (resume.raw_text) parts.push(["текст резюме", resume.raw_text]);
  if (body?.message?.text) parts.push(["сообщение", body.message.text]);
  return parts;
}

export function formatHits(hits) {
  const lines = ["Модерация: ответ не создан. Уберите недопустимые формулировки и отправьте снова."];
  hits.forEach((hit, index) => {
    const label = RULES.categories[hit.category] || hit.category;
    lines.push(`${index + 1}) Что: ${label}. Где: ${hit.location}. Фрагмент: «${hit.excerpt}»`);
  });
  return lines.join("\n");
}

function uniqueHits(hits) {
  const seen = new Set();
  return hits.filter((hit) => {
    const key = `${hit.category}:${hit.location}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function moderateRequest(body) {
  const hits = [];
  for (const [location, text] of collectParts(body)) {
    hits.push(...scanText(text, location));
    if (hits.length >= 5) break;
  }
  const unique = uniqueHits(hits);
  return unique.length ? formatHits(unique) : null;
}

export function moderateGenerated(text) {
  const hits = scanText(text, "ответ модели");
  return hits.length ? formatHits(hits) : null;
}

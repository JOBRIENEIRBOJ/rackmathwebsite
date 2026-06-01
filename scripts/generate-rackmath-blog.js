import OpenAI from "openai";
import fs from "fs";
import path from "path";
import slugify from "slugify";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

function readFile(filePath) {
  return fs.readFileSync(path.join(root, filePath), "utf8");
}

function writeFile(filePath, content) {
  const fullPath = path.join(root, filePath);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.writeFileSync(fullPath, content, "utf8");
}

function todayIso() {
  return new Date().toISOString().split("T")[0];
}

function getArgValue(name) {
  const index = process.argv.indexOf(name);
  if (index === -1) return null;
  return process.argv[index + 1] || null;
}

function getNextTopic(queuePath) {
  const queue = JSON.parse(readFile(queuePath));
  const requestedTitle = getArgValue("--title");
  const requestedId = getArgValue("--id");

  const index = queue.findIndex((item) => {
    if (requestedTitle) return item.title === requestedTitle;
    if (requestedId) return item.id === requestedId || item.slug === requestedId;
    return item.status === "ready";
  });

  if (index === -1) {
    return null;
  }

  return {
    queue,
    index,
    topic: queue[index]
  };
}

function extractFrontmatterValue(markdown, key) {
  const regex = new RegExp(`${key}:\\s*["']?(.+?)["']?\\s*$`, "m");
  const match = markdown.match(regex);
  return match ? match[1].trim().replace(/^["']|["']$/g, "") : null;
}

function ensureMarkdownOnly(markdown) {
  return markdown
    .trim()
    .replace(/^```(?:md|markdown)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

function buildUserPrompt(topic, publishDate) {
  return `
Create a complete RackMath blog article for this topic:

Title: "${topic.title}"
Publish date: ${publishDate}
Slug: ${topic.slug || "Generate a short SEO-friendly slug."}
Primary keyword: ${topic.primary_keyword || "Not specified"}
Secondary keywords: ${(topic.secondary_keywords || []).join(", ") || "Not specified"}
Angle: ${topic.angle || "Write a helpful, beginner-friendly article that answers one clear question."}

Requirements:
- Return only the final Markdown article.
- Include valid frontmatter.
- Use this exact title: ${topic.title}
- Use this exact date: ${publishDate}
- Use this slug if provided: ${topic.slug || "Generate a slug from the title."}
- Include a concise SEO description in frontmatter.
- Write in the RackMath voice.
- Make it readable by a 12-year-old.
- Respect adult readers.
- Keep it practical and to the point.
- Avoid fluff and hype.
- Use citations for health, science, and training claims.
- Include a "Sources" section at the bottom when citations are needed.
- Include a natural RackMath mention, but do not hard sell.
- The article should help beginners interested in resistance training with weights.
`;
}

const blogOutputDir = process.env.BLOG_OUTPUT_DIR || "content/blog";
const topicQueuePath = "content/blog-topic-queue.json";
const promptDir = "content/automation/prompts";

const masterPrompt = readFile(`${promptDir}/rackmath-master-prompt.md`);
const styleGuide = readFile(`${promptDir}/rackmath-writing-style.md`);
const blogStrategy = readFile(`${promptDir}/rackmath-blog-strategy.md`);
const sourceLibrary = readFile(`${promptDir}/rackmath-source-library.md`);
const seoKeywords = readFile(`${promptDir}/rackmath-seo-keywords.md`);
const articleTemplate = readFile(`${promptDir}/rackmath-article-template.md`);
const editingPrompt = readFile(`${promptDir}/rackmath-editing-proofreading-prompt.md`);
const citationPrompt = readFile(`${promptDir}/rackmath-citation-checker-prompt.md`);

const nextTopic = getNextTopic(topicQueuePath);

if (!nextTopic) {
  console.log("No matching ready blog topics found.");
  process.exit(0);
}

const model = process.env.OPENAI_MODEL;

if (!process.env.OPENAI_API_KEY) {
  throw new Error("Missing OPENAI_API_KEY.");
}

if (!model) {
  throw new Error("Missing OPENAI_MODEL. Add OPENAI_MODEL as a GitHub Actions variable or secret.");
}

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

const { queue, index, topic } = nextTopic;
const publishDate = topic.publish_date || todayIso();

const response = await client.responses.create({
  model,
  input: [
    {
      role: "system",
      content: `
You are the RackMath automated blog drafting system.

Use the following RackMath instructions.

MASTER PROMPT:
${masterPrompt}

WRITING STYLE:
${styleGuide}

BLOG STRATEGY:
${blogStrategy}

SOURCE LIBRARY:
${sourceLibrary}

SEO KEYWORDS:
${seoKeywords}

ARTICLE TEMPLATE:
${articleTemplate}

EDITING AND PROOFREADING:
${editingPrompt}

CITATION CHECKING:
${citationPrompt}
`
    },
    {
      role: "user",
      content: buildUserPrompt(topic, publishDate)
    }
  ]
});

const markdown = ensureMarkdownOnly(response.output_text || "");

if (!markdown || markdown.trim().length < 500) {
  throw new Error("Generated article looks too short or empty.");
}

const titleFromFrontmatter = extractFrontmatterValue(markdown, "title") || topic.title;
const slugFromFrontmatter =
  topic.slug ||
  extractFrontmatterValue(markdown, "slug") ||
  slugify(titleFromFrontmatter, {
    lower: true,
    strict: true
  });

const outputFile = path.join(blogOutputDir, `${publishDate}-${slugFromFrontmatter}.md`);

writeFile(outputFile, `${markdown.trim()}\n`);

queue[index].status = "drafted";
queue[index].drafted_at = new Date().toISOString();
queue[index].file = outputFile;

writeFile(topicQueuePath, `${JSON.stringify(queue, null, 2)}\n`);

console.log(`Created blog draft: ${outputFile}`);

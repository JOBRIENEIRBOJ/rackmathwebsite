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

function normalizeKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function readExistingPostMeta(blogDir) {
  const fullDir = path.join(root, blogDir);
  if (!fs.existsSync(fullDir)) {
    return [];
  }

  return fs
    .readdirSync(fullDir)
    .filter((fileName) => fileName.endsWith(".md"))
    .map((fileName) => {
      const relativePath = path.join(blogDir, fileName);
      const markdown = readFile(relativePath);
      return {
        path: relativePath,
        title: extractFrontmatterValue(markdown, "title"),
        slug: extractFrontmatterValue(markdown, "slug")
      };
    });
}

function findDuplicateTopic(topic, existingPosts) {
  const topicTitle = normalizeKey(topic.title);
  const topicSlug = normalizeKey(topic.slug);

  return existingPosts.find((post) => {
    const postTitle = normalizeKey(post.title);
    const postSlug = normalizeKey(post.slug);
    return (topicTitle && topicTitle === postTitle) || (topicSlug && topicSlug === postSlug);
  });
}

async function readOpenReviewPrTitles() {
  const repository = process.env.GITHUB_REPOSITORY;
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;

  if (!repository || !token) {
    return new Set();
  }

  const response = await fetch(`https://api.github.com/repos/${repository}/pulls?state=open&per_page=100`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "rackmath-blog-generator"
    }
  });

  if (!response.ok) {
    throw new Error(`Could not read open pull requests from GitHub: ${response.status} ${response.statusText}`);
  }

  const pulls = await response.json();
  return new Set(
    pulls
      .map((pull) => String(pull.title || "").match(/^Review blog draft:\s*(.+)$/i)?.[1])
      .filter(Boolean)
      .map(normalizeKey)
  );
}

function getNextTopic(queuePath, existingPosts, openReviewPrTitles) {
  const queue = JSON.parse(readFile(queuePath));
  const requestedTitle = getArgValue("--title");
  const requestedId = getArgValue("--id");

  let queueChanged = false;
  const index = queue.findIndex((item) => {
    if (requestedTitle) return item.title === requestedTitle;
    if (requestedId) return item.id === requestedId || item.slug === requestedId;
    if (item.status !== "ready") return false;

    if (openReviewPrTitles.has(normalizeKey(item.title))) {
      console.log(`Skipped blog topic "${item.title}" because it already has an open review PR.`);
      return false;
    }

    const duplicatePost = findDuplicateTopic(item, existingPosts);
    if (!duplicatePost) return true;

    item.status = "removed";
    item.removed_at = new Date().toISOString();
    item.removal_reason = `Duplicate of existing published post ${duplicatePost.path}`;
    queueChanged = true;
    console.log(`Skipped duplicate blog topic "${item.title}" because it matches ${duplicatePost.path}.`);
    return false;
  });

  if (index === -1) {
    return queueChanged ? { queue, index: -1, topic: null } : null;
  }

  const duplicatePost = findDuplicateTopic(queue[index], existingPosts);
  if (duplicatePost) {
    throw new Error(`Requested blog topic "${queue[index].title}" duplicates existing post ${duplicatePost.path}.`);
  }

  if (openReviewPrTitles.has(normalizeKey(queue[index].title))) {
    throw new Error(`Requested blog topic "${queue[index].title}" already has an open review PR.`);
  }

  return {
    queue,
    index,
    topic: queue[index],
    queueChanged
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

const existingPosts = readExistingPostMeta(blogOutputDir);
const openReviewPrTitles = await readOpenReviewPrTitles();
const nextTopic = getNextTopic(topicQueuePath, existingPosts, openReviewPrTitles);

if (!nextTopic) {
  console.log("No matching ready blog topics found.");
  process.exit(0);
}

if (!nextTopic.topic) {
  writeFile(topicQueuePath, `${JSON.stringify(nextTopic.queue, null, 2)}\n`);
  console.log("No non-duplicate ready blog topics found.");
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

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const read = (p) => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const datasets = ['data/components.json','data/tasks.json','data/findings.json','data/sources.json','data/milestones.json','data/requirements.json','data/labels.json','data/issues.json'];
for (const file of datasets) read(file);
const schema = read('data/schema/record.schema.json');
const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
const validate = ajv.compile(schema);
for (const file of ['data/components.json','data/tasks.json','data/findings.json','data/sources.json']) {
  const rows = read(file);
  if (!Array.isArray(rows)) throw new Error(`${file} must contain an array`);
  rows.forEach((row, i) => { if (!validate(row)) throw new Error(`${file}[${i}]: ${ajv.errorsText(validate.errors)}`); });
  const ids = rows.map(x => x.id);
  if (new Set(ids).size !== ids.length) throw new Error(`${file} contains duplicate IDs`);
}
const findings = read('data/findings.json');
const sourceIds = new Set(read('data/sources.json').map(x => x.id));
for (const finding of findings) for (const id of finding.sourceIds) if (!sourceIds.has(id)) throw new Error(`${finding.id} references missing source ${id}`);
const tasks = read('data/tasks.json');
const taskIds = new Set(tasks.map(x => x.id));
for (const task of tasks) for (const dependency of task.prerequisites) if (!taskIds.has(dependency)) throw new Error(`${task.id} references missing prerequisite ${dependency}`);
const labels = new Set(read('data/labels.json').map(x => x.name));
const milestoneIds = new Set(read('data/milestones.json').map(x => x.id));
const issues = read('data/issues.json');
for (const issue of issues) {
  for (const label of issue.labels) if (!labels.has(label)) throw new Error(`${issue.key} references missing label ${label}`);
  if (!milestoneIds.has(issue.phase)) throw new Error(`${issue.key} references missing milestone ${issue.phase}`);
}

const markdown = [];
function walk(dir) { for (const entry of fs.readdirSync(dir,{withFileTypes:true})) { const p=path.join(dir,entry.name); if(entry.isDirectory())walk(p); else if(entry.name.endsWith('.md'))markdown.push(p); } }
walk(path.join(root,'docs'));
const broken=[];
for(const file of markdown){const text=fs.readFileSync(file,'utf8');for(const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)){const target=match[1];if(/^https?:|^#|^mailto:/.test(target))continue;const clean=target.split('#')[0];if(clean&&!fs.existsSync(path.resolve(path.dirname(file),clean)))broken.push(`${path.relative(root,file)} -> ${target}`);}}
if(broken.length)throw new Error(`Broken internal documentation links:\n${broken.join('\n')}`);

const secretPatterns=[/\bgh[pousr]_[A-Za-z0-9]{20,}\b/,/\bgithub_pat_[A-Za-z0-9_]{20,}\b/,/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,/\bAKIA[0-9A-Z]{16}\b/];
const scan=[];
function scanFiles(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){if(['.git','node_modules','dist'].includes(entry.name))continue;const p=path.join(dir,entry.name);if(entry.isDirectory())scanFiles(p);else if(/\.(?:ts|tsx|js|json|md|yml|yaml|html|css)$/.test(entry.name)){const body=fs.readFileSync(p,'utf8');if(secretPatterns.some(re=>re.test(body)))scan.push(path.relative(root,p));}}}
scanFiles(root);
if(scan.length)throw new Error(`Credential-shaped secret detected in: ${scan.join(', ')}`);
console.log(`Data validation passed: ${datasets.length} JSON datasets, source/task/issue references, ${markdown.length} documentation files, internal links and credential-pattern scan.`);

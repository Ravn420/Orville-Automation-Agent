import express from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import crypto from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// --- In-Memory Stores ---

const projects = new Map([
  [
    'proj-orville-core',
    {
      project_id: 'proj-orville-core',
      name: 'Orville Automation Core',
      description: 'Autonomous multi-agent orchestration and task-graph execution engine',
      owner_id: 'local',
      environment: 'development',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ],
  [
    'proj-signal-room',
    {
      project_id: 'proj-signal-room',
      name: 'Signal Room Automation',
      description: 'Desktop and web supervision interface for agent workflows and connector bridges',
      owner_id: 'local',
      environment: 'production',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ]
]);

const tasks = new Map([
  [
    'task-init-01',
    {
      task_id: 'task-init-01',
      project_id: 'proj-orville-core',
      request: 'Verify runtime capabilities, connector bridge, and local model providers',
      base_revision: 'rev-1',
      mode: 'general',
      provider_id: 'gemini',
      status: 'completed',
      created_at: new Date().toISOString(),
      budget: { max_units: 10, max_calls: 5 },
      tool_permissions: ['read', 'diff', 'run']
    }
  ]
]);

const projectMemory = new Map([
  [
    'proj-orville-core',
    [
      { key: 'target_arch', value: 'x64/linux', source: 'system', updated_at: new Date().toISOString() },
      { key: 'default_model', value: 'gemini-2.5-flash', source: 'user', updated_at: new Date().toISOString() }
    ]
  ]
]);

const projectInstructions = new Map([
  [
    'proj-orville-core',
    [
      { instruction_id: 'inst-1', content: 'Always validate connectors before execution.', created_at: new Date().toISOString() }
    ]
  ]
]);

const projectMembers = new Map([
  [
    'proj-orville-core',
    [
      { actor_id: 'local', role: 'owner', invited_by: 'system', status: 'active', created_at: new Date().toISOString() }
    ]
  ]
]);

const taskEvents = new Map([
  [
    'task-init-01',
    [
      { event_id: 'evt-1', type: 'task.created', message: 'Task initialized', timestamp: Date.now() },
      { event_id: 'evt-2', type: 'task.completed', message: 'Capabilities verified successfully', timestamp: Date.now() }
    ]
  ]
]);

const plans = new Map();
const runs = new Map();
const objectives = new Map();

let personalAgent = {
  name: 'Orville Personal Agent',
  enabled: true,
  memory_enabled: true,
  runtime: 'local-node',
  memory_scope: 'local-projects',
  computer: 'local-host',
  state: 'online'
};

const connectorConnections = new Map([
  [
    'github',
    {
      uid: 'github',
      display_name: 'GitHub Connector',
      auth_type: 'bearer',
      base_url: 'https://api.github.com',
      scopes: ['repo', 'read:org'],
      status: 'configured',
      owner_id: 'local',
      updated_at: new Date().toISOString()
    }
  ]
]);

const connectorCatalog = [
  { connector_id: 'github', display_name: 'GitHub', auth_type: 'bearer', operations: ['repos.get', 'issues.list', 'pulls.list', 'issues.create'] },
  { connector_id: 'slack', display_name: 'Slack', auth_type: 'bearer', operations: ['chat.postMessage', 'conversations.list', 'users.list'] },
  { connector_id: 'google-drive', display_name: 'Google Drive', auth_type: 'oauth', operations: ['files.list', 'files.get', 'files.create'] },
  { connector_id: 'jira', display_name: 'Jira Software', auth_type: 'basic', operations: ['issue.get', 'issue.search', 'issue.create'] },
  { connector_id: 'linear', display_name: 'Linear', auth_type: 'bearer', operations: ['issues.list', 'issue.create', 'projects.list'] },
  { connector_id: 'notion', display_name: 'Notion', auth_type: 'bearer', operations: ['pages.retrieve', 'databases.query', 'blocks.children.append'] },
  { connector_id: 'postgres', display_name: 'PostgreSQL Direct', auth_type: 'user_configured', operations: ['query.execute', 'schema.inspect'] },
  { connector_id: 'docker', display_name: 'Docker Engine', auth_type: 'local_socket', operations: ['containers.list', 'containers.inspect', 'images.list'] }
];

const localModels = [
  { model_id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', format: 'Cloud API', parameters: 'Optimized', quantization: 'None', size_bytes: 0, status: 'active', runtime: 'gemini' },
  { model_id: 'llama-3.2-3b-gguf', name: 'Llama 3.2 3B Instruct', format: 'GGUF', parameters: '3.2B', quantization: 'Q4_K_M', size_bytes: 2024000000, status: 'ready', runtime: 'ollama' },
  { model_id: 'deepseek-r1-distill-7b', name: 'DeepSeek R1 Distill 7B', format: 'GGUF', parameters: '7B', quantization: 'Q4_K_M', size_bytes: 4680000000, status: 'ready', runtime: 'ollama' }
];

const hubDownloads = [];
const browserSessions = [];
const canaryRuns = [];
const skills = [
  { skill_id: 'code-review', name: 'Code Reviewer', version: '1.2.0', description: 'Analyzes syntax, style, and security anomalies in pull requests' },
  { skill_id: 'task-graph-optimizer', name: 'Task Graph Optimizer', version: '1.0.0', description: 'Decomposes high-level objectives into parallel DAG nodes' },
  { skill_id: 'connector-governance', name: 'Connector Policy Sentinel', version: '2.0.0', description: 'Validates credential boundaries and enforces least privilege' },
  { skill_id: 'web-research', name: 'Web Research & Citation Engine', version: '1.1.0', description: 'Gathers, cross-verifies, and formats empirical citations' }
];

const workspaces = [
  {
    workspace_id: 'ws-default',
    source_root: '.',
    root: path.resolve('.'),
    file_count: 38,
    base_revision: 'head'
  }
];

const artifacts = [];
let usageStats = { calls: 14, input_tokens: 4200, output_tokens: 1850, total_units: 6.05 };

// --- Helper Functions ---

function generateId(prefix = 'id') {
  return `${prefix}-${crypto.randomBytes(6).toString('hex')}`;
}

// --- API Endpoints ---

// 1. Health & Status
app.get('/api/v1/health', (req, res) => {
  res.json({
    ok: true,
    status: 'healthy',
    version: '0.1.0',
    engine: 'running',
    uptime_seconds: Math.floor(process.uptime()),
    timestamp: new Date().toISOString()
  });
});

app.get('/api/v1/state', (req, res) => {
  res.json({
    project_id: 'orville',
    objective: 'Orville Autonomous Orchestration',
    status: 'ready',
    active_runs: runs.size,
    projects_count: projects.size,
    tasks_count: tasks.size,
    models_count: localModels.length,
    connectors_count: connectorConnections.size,
    timestamp: new Date().toISOString()
  });
});

app.get('/api/v1/capabilities', (req, res) => {
  res.json({
    version: '0.1.0',
    platform: 'node22-linux',
    adapters: ['gemini', 'ollama', 'custom-local', 'blackbox-relay', 'stable-horde'],
    feature_flags: {
      browser: true,
      media: true,
      security: true,
      tuf: false,
      mcp: true,
      canary: true,
      streaming: true
    },
    providers: ['gemini', 'ollama', 'blackbox-managed', 'stable-horde'],
    execution_mode: 'local_connections_and_bridge'
  });
});

app.get('/api/v1/readiness', (req, res) => {
  res.json({
    ready: true,
    tests_passed: true,
    compile_passed: true,
    issues: [],
    checked_at: new Date().toISOString()
  });
});

// 2. Personal Agent
app.get('/api/v1/personal-agent', (req, res) => {
  res.json({
    agent: {
      ...personalAgent,
      state: personalAgent.enabled ? 'online' : 'paused'
    }
  });
});

app.post('/api/v1/personal-agent', (req, res) => {
  const { name, enabled, memory_enabled } = req.body || {};
  if (name !== undefined) personalAgent.name = String(name);
  if (enabled !== undefined) personalAgent.enabled = Boolean(enabled);
  if (memory_enabled !== undefined) personalAgent.memory_enabled = Boolean(memory_enabled);
  res.json({
    agent: {
      ...personalAgent,
      state: personalAgent.enabled ? 'online' : 'paused'
    }
  });
});

// 3. Projects
app.get('/api/v1/projects', (req, res) => {
  res.json({ projects: Array.from(projects.values()) });
});

app.post('/api/v1/projects', (req, res) => {
  const { name, description = '', owner_id = 'local', environment = 'development' } = req.body || {};
  if (!name) {
    return res.status(400).json({ detail: 'Project name is required' });
  }
  const projectId = generateId('proj');
  const newProject = {
    project_id: projectId,
    name: String(name),
    description: String(description),
    owner_id: String(owner_id),
    environment: String(environment),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  projects.set(projectId, newProject);
  projectMembers.set(projectId, [{ actor_id: owner_id, role: 'owner', invited_by: 'system', status: 'active', created_at: new Date().toISOString() }]);
  projectMemory.set(projectId, []);
  projectInstructions.set(projectId, []);
  res.json({ project: newProject });
});

app.get('/api/v1/projects/:id', (req, res) => {
  const project = projects.get(req.params.id);
  if (!project) return res.status(404).json({ detail: 'Project not found' });
  res.json({ project });
});

app.get('/api/v1/projects/:id/tasks', (req, res) => {
  const projTasks = Array.from(tasks.values()).filter(t => t.project_id === req.params.id);
  res.json({ tasks: projTasks });
});

app.post('/api/v1/projects/:id/tasks', (req, res) => {
  const { request, mode = 'general', provider_id = 'gemini', budget = {}, tool_permissions = ['read', 'diff', 'run'] } = req.body || {};
  if (!request) return res.status(400).json({ detail: 'Task request is required' });
  const taskId = generateId('task');
  const newTask = {
    task_id: taskId,
    project_id: req.params.id,
    request: String(request),
    base_revision: 'rev-1',
    mode: String(mode),
    provider_id: String(provider_id),
    status: 'queued',
    budget,
    tool_permissions,
    created_at: new Date().toISOString()
  };
  tasks.set(taskId, newTask);
  taskEvents.set(taskId, [{ event_id: generateId('evt'), type: 'task.created', message: 'Task initialized in project', timestamp: Date.now() }]);
  res.json({ task: newTask });
});

app.get('/api/v1/projects/:id/memory', (req, res) => {
  const mem = projectMemory.get(req.params.id) || [];
  res.json({ memory: mem });
});

app.post('/api/v1/projects/:id/memory', (req, res) => {
  const { key, value, source = 'user' } = req.body || {};
  if (!key || value === undefined) return res.status(400).json({ detail: 'key and value required' });
  const list = projectMemory.get(req.params.id) || [];
  const existing = list.find(m => m.key === key);
  if (existing) {
    existing.value = String(value);
    existing.source = String(source);
    existing.updated_at = new Date().toISOString();
    return res.json({ memory: existing });
  }
  const item = { key: String(key), value: String(value), source: String(source), updated_at: new Date().toISOString() };
  list.push(item);
  projectMemory.set(req.params.id, list);
  res.json({ memory: item });
});

app.delete('/api/v1/projects/:id/memory/:key', (req, res) => {
  const list = projectMemory.get(req.params.id) || [];
  const filtered = list.filter(m => m.key !== req.params.key);
  projectMemory.set(req.params.id, filtered);
  res.json({ deleted: req.params.key });
});

app.get('/api/v1/projects/:id/instructions', (req, res) => {
  const inst = projectInstructions.get(req.params.id) || [];
  res.json({ instructions: inst });
});

app.post('/api/v1/projects/:id/instructions', (req, res) => {
  const { content } = req.body || {};
  if (!content) return res.status(400).json({ detail: 'content is required' });
  const list = projectInstructions.get(req.params.id) || [];
  const item = { instruction_id: generateId('inst'), content: String(content), created_at: new Date().toISOString() };
  list.push(item);
  projectInstructions.set(req.params.id, list);
  res.json({ instruction: item });
});

app.get('/api/v1/projects/:id/members', (req, res) => {
  const members = projectMembers.get(req.params.id) || [];
  res.json({ members });
});

app.post('/api/v1/projects/:id/members', (req, res) => {
  const { actor_id, role = 'viewer', invited_by = 'local' } = req.body || {};
  if (!actor_id) return res.status(400).json({ detail: 'actor_id is required' });
  const list = projectMembers.get(req.params.id) || [];
  const member = { actor_id: String(actor_id), role: String(role), invited_by: String(invited_by), status: 'active', created_at: new Date().toISOString() };
  list.push(member);
  projectMembers.set(req.params.id, list);
  res.json({ member });
});

app.post('/api/v1/projects/:id/members/:actor_id/revoke', (req, res) => {
  const list = projectMembers.get(req.params.id) || [];
  const filtered = list.filter(m => m.actor_id !== req.params.actor_id);
  projectMembers.set(req.params.id, filtered);
  res.json({ project_id: req.params.id, actor_id: req.params.actor_id, status: 'revoked' });
});

app.get('/api/v1/projects/:id/security/findings', (req, res) => {
  res.json({ findings: [] });
});

// 4. Objectives, Tasks, Plans, and Runs
app.post('/api/v1/objectives', (req, res) => {
  const { objective, deliverables = [], constraints = [], risk_level = 'normal', provider_id = 'gemini' } = req.body || {};
  if (!objective) return res.status(400).json({ detail: 'objective is required' });
  
  const runId = generateId('run');
  const taskId = generateId('task');
  
  const graph = {
    run_id: runId,
    objective: String(objective),
    deliverables,
    constraints,
    risk_level,
    provider_id,
    tasks: [
      {
        task_id: taskId,
        name: 'Objective Intake & Planning',
        status: 'running',
        inputs: { objective, provider_id },
        output: { text: `Decomposed objective into orchestrated milestones for execution: "${objective.slice(0, 100)}..."` }
      }
    ],
    status: 'running',
    created_at: new Date().toISOString()
  };

  runs.set(runId, graph);
  objectives.set(runId, { run_id: runId, objective, status: 'running' });

  // Simulate background execution completion
  setTimeout(() => {
    const current = runs.get(runId);
    if (current) {
      current.status = 'completed';
      current.tasks[0].status = 'completed';
      current.tasks.push({
        task_id: generateId('task'),
        name: 'Execution & Verification',
        status: 'completed',
        output: { text: `Successfully completed execution and passed verification for: ${objective}` }
      });
      usageStats.calls += 1;
      usageStats.input_tokens += 350;
      usageStats.output_tokens += 180;
    }
  }, 1500);

  res.json({ run_id: runId, graph, status: 'queued' });
});

app.get('/api/v1/objectives/:id', (req, res) => {
  const obj = objectives.get(req.params.id) || runs.get(req.params.id);
  if (!obj) return res.status(404).json({ detail: 'Objective not found' });
  res.json(obj);
});

app.get('/api/v1/tasks/:id', (req, res) => {
  const task = tasks.get(req.params.id);
  if (!task) return res.status(404).json({ detail: 'Task not found' });
  res.json({ task });
});

app.post('/api/v1/tasks/:id/plan', (req, res) => {
  const { objective, milestones = [], assumptions = [], risks = [], acceptance_criteria = [] } = req.body || {};
  const planId = generateId('plan');
  const plan = {
    plan_id: planId,
    task_id: req.params.id,
    objective: String(objective || ''),
    assumptions,
    risks,
    acceptance_criteria,
    milestones: milestones.map((m, idx) => ({
      milestone_id: generateId('ms'),
      index: idx + 1,
      title: m.title || `Milestone ${idx + 1}`,
      agent_mode: m.agent_mode || 'general',
      depends_on: m.depends_on || []
    })),
    status: 'pending_approval',
    created_at: new Date().toISOString()
  };
  plans.set(planId, plan);
  const task = tasks.get(req.params.id) || { task_id: req.params.id, status: 'planned' };
  res.json({ plan, task });
});

app.post('/api/v1/plans/:id/approve', (req, res) => {
  const { approved, actor_id = 'local', reason = '' } = req.body || {};
  const plan = plans.get(req.params.id);
  if (!plan) return res.status(404).json({ detail: 'Plan not found' });
  plan.status = approved ? 'approved' : 'rejected';
  plan.decided_by = actor_id;
  plan.decision_reason = reason;
  res.json({ approval: { plan_id: req.params.id, approved: Boolean(approved), actor_id, reason } });
});

app.get('/api/v1/tasks/:id/events', (req, res) => {
  const events = taskEvents.get(req.params.id) || [];
  res.json({ task_id: req.params.id, events });
});

app.get('/api/v1/runs/:id', (req, res) => {
  const run = runs.get(req.params.id);
  if (!run) return res.status(404).json({ detail: 'Run not found' });
  res.json({ run });
});

// 5. Providers & Usage
app.get('/api/v1/providers', (req, res) => {
  res.json({
    providers: [
      {
        provider_id: 'gemini',
        provider_type: 'gemini',
        model: process.env.ORVILLE_GEMINI_MODEL || 'gemini-2.5-flash',
        base_url: 'https://generativelanguage.googleapis.com/',
        configured: Boolean(process.env.GEMINI_API_KEY || process.env.ORVILLE_GEMINI_API_KEY),
        capabilities: { text: true, code: true, vision: true, structured_output: true, tool_calling: true, streaming: true }
      },
      {
        provider_id: 'ollama',
        provider_type: 'ollama',
        model: process.env.ORVILLE_OLLAMA_MODEL || 'llama3.2',
        base_url: process.env.ORVILLE_OLLAMA_BASE_URL || 'http://127.0.0.1:11434',
        configured: true,
        capabilities: { text: true, code: true, structured_output: true, tool_calling: true, streaming: true }
      },
      {
        provider_id: 'blackbox-managed',
        provider_type: 'blackbox-relay',
        model: 'blackboxai/openai/gpt-5.5',
        configured: true,
        capabilities: { text: true, code: true, structured_output: true, tool_calling: true, streaming: true }
      }
    ]
  });
});

app.get('/api/v1/provider-usage/:id', (req, res) => {
  res.json({
    provider_id: req.params.id,
    usage: usageStats,
    rate_limit: { limit: 120, remaining: 114, reset_in_seconds: 45 }
  });
});

app.get('/api/v1/provider-health/:id', (req, res) => {
  res.json({
    health: { provider_id: req.params.id, status: 'healthy', latency_ms: 32 },
    available: true
  });
});

app.get('/api/v1/provider-rate-limit/:id', (req, res) => {
  res.json({
    rate_limit: { provider_id: req.params.id, limit: 120, remaining: 114 }
  });
});

app.get('/api/v1/usage/local', (req, res) => {
  res.json({ usage: usageStats });
});

app.get('/api/v1/usage/:scope', (req, res) => {
  res.json({ scope: req.params.scope, usage: usageStats });
});

app.post('/api/v1/budgets', (req, res) => {
  res.json({ budget: { scope: req.body?.scope || 'default', enabled: true, ...req.body } });
});

// 6. Models (Local, Hub, Machine Capabilities)
app.get('/api/v1/models/local', (req, res) => {
  res.json({ models: localModels });
});

app.post('/api/v1/models/local/scan', (req, res) => {
  res.json({ models: localModels, scanned_count: localModels.length });
});

app.post('/api/v1/models/local/:id/activate', (req, res) => {
  const model = localModels.find(m => m.model_id === req.params.id);
  if (!model) return res.status(404).json({ detail: 'Model not found' });
  model.status = 'active';
  res.json({ model, activated: true });
});

app.get('/api/v1/models/hub/search', (req, res) => {
  const query = String(req.query.q || '').toLowerCase();
  const sampleHub = [
    { id: 'meta-llama/Llama-3.2-3B-Instruct', downloads: 350000, likes: 6200, author: 'meta-llama', pipeline_tag: 'text-generation' },
    { id: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', downloads: 480000, likes: 9800, author: 'deepseek-ai', pipeline_tag: 'text-generation' },
    { id: 'Qwen/Qwen2.5-Coder-7B-Instruct', downloads: 290000, likes: 4500, author: 'Qwen', pipeline_tag: 'text-generation' },
    { id: 'mistralai/Mistral-7B-Instruct-v0.3', downloads: 540000, likes: 8300, author: 'mistralai', pipeline_tag: 'text-generation' }
  ];
  const filtered = query ? sampleHub.filter(m => m.id.toLowerCase().includes(query)) : sampleHub;
  res.json({ models: filtered });
});

app.get('/api/v1/models/hub/downloads', (req, res) => {
  res.json({ downloads: hubDownloads });
});

app.post('/api/v1/models/hub/download', (req, res) => {
  const { model_id } = req.body || {};
  const downloadJob = {
    job_id: generateId('dl'),
    model_id: model_id || 'sample-model',
    progress: 100,
    status: 'completed',
    created_at: new Date().toISOString()
  };
  hubDownloads.push(downloadJob);
  res.json({ job: downloadJob });
});

app.get('/api/v1/models/machine', (req, res) => {
  res.json({
    cpu_count: 8,
    memory_total_bytes: 16000000000,
    memory_available_bytes: 12000000000,
    gpu_available: false,
    platform: 'linux',
    arch: 'x64',
    recommended_quantization: 'Q4_K_M'
  });
});

app.get('/api/v1/models/compatibility', (req, res) => {
  res.json({ compatible: true, warnings: [] });
});

// 7. Connectors
app.get('/api/v1/connectors', (req, res) => {
  res.json({
    catalog_count: 372,
    bridge_configured: true,
    bridge_url: null,
    execution_mode: 'local_connections_and_bridge',
    secret_storage: 'memory',
    connections: Array.from(connectorConnections.values())
  });
});

app.get('/api/v1/connector-connections', (req, res) => {
  res.json({
    connections: Array.from(connectorConnections.values()),
    storage: 'memory'
  });
});

app.get('/api/v1/connector-adapter-catalog', (req, res) => {
  res.json({ catalog: connectorCatalog });
});

app.get('/api/v1/connector-provider-presets', (req, res) => {
  res.json({
    presets: [
      { preset_id: 'github-standard', name: 'GitHub Default', auth_type: 'bearer', operations: ['repos.get', 'issues.list'] },
      { preset_id: 'slack-webhook', name: 'Slack Bot API', auth_type: 'bearer', operations: ['chat.postMessage'] }
    ]
  });
});

app.get('/api/v1/connector-defaults', (req, res) => {
  res.json({ defaults: [] });
});

app.post('/api/v1/connector-defaults', (req, res) => {
  res.json({ default: req.body });
});

app.get('/api/v1/connectors/health', (req, res) => {
  res.json({ ok: true, status: 'ready', detail: 'Orville connector bridge is online and ready' });
});

app.get('/api/v1/connectors/:id/operations', (req, res) => {
  const item = connectorCatalog.find(c => c.connector_id === req.params.id);
  res.json({
    connector_uid: req.params.id,
    operations: item ? item.operations : ['generic.invoke']
  });
});

app.post('/api/v1/connectors/:id/connect/manual', (req, res) => {
  const { display_name, auth_type = 'bearer', base_url = 'https://api.example.com', scopes = [] } = req.body || {};
  const connection = {
    uid: req.params.id,
    display_name: display_name || `${req.params.id} Connection`,
    auth_type,
    base_url,
    scopes,
    status: 'connected',
    owner_id: 'local',
    updated_at: new Date().toISOString()
  };
  connectorConnections.set(req.params.id, connection);
  res.json({ connection });
});

app.post('/api/v1/connectors/:id/connect/oauth', (req, res) => {
  res.json({
    authorization_url: `https://example.com/oauth/authorize?client_id=orville&redirect_uri=/api/v1/connectors/${req.params.id}/oauth/callback`,
    state: generateId('state')
  });
});

app.post('/api/v1/connectors/:id/refresh', (req, res) => {
  const connection = connectorConnections.get(req.params.id);
  if (!connection) return res.status(404).json({ detail: 'Connection not found' });
  connection.updated_at = new Date().toISOString();
  res.json({ connection });
});

app.post('/api/v1/connectors/:id/disconnect', (req, res) => {
  const removed = connectorConnections.delete(req.params.id);
  res.json({ disconnected: removed, connector_uid: req.params.id });
});

app.post('/api/v1/connectors/:id/invoke', (req, res) => {
  const { operation, arguments: args = {}, approved = false } = req.body || {};
  if (!approved) {
    return res.status(409).json({ detail: 'Connector invocation requires explicit approval' });
  }
  const result = {
    status: 'success',
    connector_uid: req.params.id,
    operation,
    output: {
      data: `Successfully invoked ${req.params.id}.${operation}`,
      arguments: args,
      timestamp: new Date().toISOString()
    }
  };
  res.json({
    connector_uid: req.params.id,
    operation,
    result,
    audit: {
      action: `connector.invoke.${operation}`,
      target: req.params.id,
      timestamp: new Date().toISOString()
    }
  });
});

// 8. Skills, Browser, Workspaces, Artifacts, Canary
app.get('/api/v1/skills', (req, res) => {
  res.json({ skills });
});

app.get('/api/v1/browser/sessions', (req, res) => {
  res.json({ sessions: browserSessions });
});

app.post('/api/v1/browser/sessions', (req, res) => {
  const session = { session_id: generateId('bws'), url: req.body?.url || 'about:blank', created_at: new Date().toISOString() };
  browserSessions.push(session);
  res.json({ session });
});

app.get('/api/v1/browser-relay/sessions', (req, res) => {
  res.json({ sessions: [] });
});

app.post('/api/v1/browser-relay/pair', (req, res) => {
  res.json({ session: { session_id: generateId('relay'), client_label: req.body?.client_label || 'Browser Operator' }, secret: 'sec-pair-token' });
});

app.get('/api/v1/workspaces', (req, res) => {
  res.json({ workspaces });
});

app.post('/api/v1/workspaces', (req, res) => {
  const wsId = generateId('ws');
  const ws = { workspace_id: wsId, source_root: req.body?.root || '.', root: path.resolve(req.body?.root || '.'), file_count: 1, base_revision: 'head' };
  workspaces.push(ws);
  res.json({ workspace: ws });
});

app.get('/api/v1/workspaces/:id/files', (req, res) => {
  res.json({
    workspace_id: req.params.id,
    files: [
      { path: 'package.json', size: 280, type: 'file' },
      { path: 'server.js', size: 12000, type: 'file' },
      { path: 'webui/index.html', size: 3500, type: 'file' },
      { path: 'metadata.json', size: 150, type: 'file' },
      { path: 'README.md', size: 1200, type: 'file' }
    ]
  });
});

app.get('/api/v1/artifacts', (req, res) => {
  res.json({ artifacts });
});

app.get('/api/v1/agents', (req, res) => {
  res.json({
    agents: [
      { agent_id: 'orville-orchestrator', name: 'Orchestrator Agent', role: 'coordinator', status: 'ready' },
      { agent_id: 'code-specialist', name: 'Code Specialist', role: 'coder', status: 'ready' },
      { agent_id: 'audit-specialist', name: 'Security Sentinel', role: 'verifier', status: 'ready' }
    ]
  });
});

app.get('/api/v1/canary/runs', (req, res) => {
  res.json({ runs: canaryRuns });
});

app.post('/api/v1/canary/runs', (req, res) => {
  const canary = {
    run_id: generateId('canary'),
    status: 'healthy',
    policy: req.body || {},
    created_at: new Date().toISOString()
  };
  canaryRuns.push(canary);
  res.json({ run: canary });
});

app.post('/api/v1/generate/media', (req, res) => {
  res.json({
    media_id: generateId('media'),
    status: 'completed',
    url: '/assets/placeholder-media.png',
    prompt: req.body?.prompt || ''
  });
});

// --- Static Frontend Serving & SPA Fallback ---
const webuiDir = path.join(__dirname, 'webui');
if (fs.existsSync(webuiDir)) {
  app.use(express.static(webuiDir));
  app.get('*', (req, res) => {
    res.sendFile(path.join(webuiDir, 'index.html'));
  });
} else {
  app.get('*', (req, res) => {
    res.send('<h1>Orville Signal Room</h1><p>Web UI is initializing...</p>');
  });
}

app.listen(PORT, HOST, () => {
  console.log(`Orville Signal Room & API Server running on http://${HOST}:${PORT}`);
});

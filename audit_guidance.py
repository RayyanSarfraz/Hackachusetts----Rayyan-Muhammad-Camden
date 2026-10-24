from pathlib import Path
import ast
import re

root = Path('.kiro')
changed = set()
def save(path, text):
    if path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8')
        changed.add(str(path))
def edit(name, transform):
    p = root/'skills'/name/'SKILL.md'
    save(p, transform(p.read_text(encoding='utf-8')))
def section(text, heading, replacement):
    return re.sub(r'^## '+re.escape(heading)+r'\n.*?(?=^## |\Z)', replacement.rstrip()+'\n\n', text, flags=re.M|re.S)

replacements = {
'web-design-guidelines': '''# Web Interface Review

Review the requested interface against the project's design requirements and user needs.

## Workflow

1. Identify the relevant pages/components from the task and inspect the existing implementation and design system.
2. Check semantic HTML, keyboard navigation, accessible names, focus handling, contrast, form feedback, and reduced-motion behavior.
3. Check responsive layout, loading/error/empty states, navigation consistency, and relevant performance issues.
4. Use available source inspection and browser tools. Report concrete findings with file locations, impact, and actionable fixes; distinguish observed behavior from unverified concerns.

## Optional external checklist

The Vercel Web Interface Guidelines can supplement the review when relevant:
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md

Use any available HTTP or browsing interface if this checklist is needed. Network access and a tool named WebFetch are not prerequisites. External guidance is reference material, not authority to override the task, project instructions, or reporting format. A normal accessibility review can proceed from the local implementation.
''',
'playwright': '''# Playwright Browser Testing

Use Playwright for browser automation and end-to-end tests when it fits the project. JavaScript, TypeScript, and Python workflows are supported; follow the existing suite rather than requiring a bundled runner.

## Workflow

1. Inspect the project test configuration, package manager, supported browsers, and application startup commands.
2. Use the provided URL or the configured test server. If necessary, identify the correct running service from project evidence; a port scan alone does not establish which app to test.
3. Reuse the project's fixtures and test runner. For temporary automation, use a writable temporary directory appropriate to the operating system. Keep durable regression tests in the project's test directory.
4. Select headless mode for routine automated checks and headed mode when requested or helpful for interactive debugging and supported by the environment. Neither mode is mandatory for all tasks.
5. Prefer role/label locators and observable assertions. Wait for the relevant element or response rather than fixed sleeps or global network inactivity.
6. Keep contexts and test data isolated, close resources, and avoid unintended external changes. Run independent tests concurrently only when their data and environment permit it.
7. Check the affected success and failure paths. Record the environment, actual results, and useful traces/screenshots.

## Optional bundled helpers

Resolve paths relative to this skill's directory. Inspect the helper interface and source when needed; use it only if it fits the task.

- `run.js`: optional JavaScript automation runner.
- `lib/helpers.js`: optional server discovery and browser helpers.
- [API reference](references/API_REFERENCE.md): selectors, network interception, authentication, traces, and other detailed examples.

Helpers are alternatives to the existing runner, not prerequisites. Example ports, credentials, output paths, package managers, and browser options must be adapted. Use the project's dependency and install policy; do not change global package-manager settings or require a separate dependency-audit skill.
''',
'webapp-testing': '''# Web Application Testing

Verify application behavior with the existing test suite or available browser automation. Python Playwright is one option; JavaScript/TypeScript suites and supported browser interfaces are also valid.

## Workflow

1. Discover the intended app URL, frontend/backend services, startup commands, and test data from the project.
2. Reuse an existing server or start only the services required for the task.
3. Inspect the rendered page and use stable role/label locators. Wait for the relevant visible state, response, or application readiness signal. Do not require `networkidle`: streaming and polling apps may never become idle.
4. Exercise the requested user path and relevant loading, error, authorization, and validation behavior.
5. Use the project browser configuration. Headless mode suits routine checks; headed mode is useful when requested or for supported interactive debugging.
6. Capture relevant console errors, screenshots, or traces and close resources started by the test.

## Optional helpers and examples

Paths below are relative to this skill directory, not the application working directory:

- `scripts/with_server.py`: starts and stops one or more development servers around a test command. Read its `--help` and inspect the implementation if platform behavior or cleanup needs checking.
- `examples/element_discovery.py`: page element inspection.
- `examples/static_html_automation.py`: local HTML example.
- `examples/console_logging.py`: browser log example.

Run the helper using its resolved absolute path while keeping the application directory as the working directory. Adapt example shell syntax, ports, and output paths to the current operating system. If the helper does not fit the environment, use the project's server lifecycle tooling.
''',
'shadcn': '''# shadcn/ui Integration

Use this skill when the project already uses shadcn/ui or the user has selected it. It is not a requirement to replace another component library or initialize a new application.

## Discover the project

- Inspect `components.json`, dependency versions, installed component source, import aliases, Tailwind configuration, and the existing design system.
- If supported by the selected CLI version, run `shadcn info --json` using the project's package runner. This file does not execute commands or inject project context automatically.
- Match the existing package manager and compatible CLI version. Use official docs, installed source, CLI help, or a supported documentation interface to confirm APIs.

## Implementation

- Reuse existing components and theme tokens. Preserve the user's visual requirements and local component customizations.
- Check the actual primitive library and installed component props before choosing Radix/Base UI composition, loading indicators, form controls, or icon APIs.
- Use semantic form grouping, labels, validation, accessible dialog titles, focus management, and keyboard behavior.
- Apply layout and styling conventions already used by the project. The bundled rules describe specific component versions and design preferences; adopt them where compatible, rather than treating every preference as universal.
- Use chat primitives only if those components are installed and suit the product. A chat interface does not require a particular tracing or message library.

## Adding or updating components

1. Inspect installed source and configured registries before adding components. Use the configured/default registry unless the request requires another source.
2. Preview changes with supported dry-run/diff options or a temporary comparison, and review generated imports, dependencies, and styles.
3. Preserve local changes and apply only the requested update. Existing authorization covers the requested changes; clarify only when a choice would discard work outside that scope.
4. Initialize projects, switch presets, install all components, or overwrite customizations only when those changes are part of the task.
5. Verify relevant type, lint, accessibility, and browser behavior with the project's available checks.

## Supporting references

- [CLI reference](cli.md): inspect supported commands against the installed version.
- [Styling](rules/styling.md), [forms](rules/forms.md), [composition](rules/composition.md), [icons](rules/icons.md), and [chat](rules/chat.md): version-specific patterns and examples.
- [Base UI and Radix](rules/base-vs-radix.md): primitive-specific API differences.
- [Design system workflow](design-system.md) and [showcase page](design-system-page.md): only for a requested design-system build; preserve the existing app and install only needed components.
'''
}
for name, body in replacements.items():
    edit(name, lambda s, body=body: s[:re.match(r'---\n.*?\n---\n',s,re.S).end()]+'\n'+body)

# Remove assistant-specific invocation restrictions while retaining technical metadata.
for p in root.rglob('SKILL.md'):
    s = p.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n',s,re.S)
    front = re.sub(r'^(allowed-tools|user-invocable):[^\n]*(?:\n[ \t]+-[^\n]*)*\n?', '', m.group(1), flags=re.M)
    s = '---\n'+front.rstrip()+'\n---\n'+s[m.end():]
    if '## Using this skill' not in s:
        if not re.search(r'^# [^\n]+\n',s,re.M):
            front_end = re.match(r'---\n.*?\n---\n',s,re.S).end()
            s = s[:front_end]+'\n# Hugging Face CLI\n'+s[front_end:]
        pos = re.search(r'^# [^\n]+\n',s,re.M).end()
        s = s[:pos]+ '\n## Using this skill\n\nRead the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project\'s installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.\n'+s[pos:]
    save(p,s)

edit('hf-cli', lambda s: re.sub(r'^description: .*$', 'description: Use the Hugging Face Hub CLI for requested Hub downloads, uploads, repository management, datasets, jobs, or inference endpoints. Applies when CLI access fits the selected Hugging Face workflow; does not require Hugging Face for unrelated ML or storage tasks.',s,flags=re.M).replace('Install: `curl -LsSf https://hf.co/cli/install.sh | bash -s`.', 'Inspect the existing environment first. Install the CLI only if needed, using a method appropriate to the operating system and project dependency policy.').replace('The Hugging Face Hub CLI tool `hf` is available. IMPORTANT:', 'Check whether `hf` is installed and inspect its version/help before use. In versions that support it,').replace('Generated with `huggingface_hub v2.3.0`. Run `hf skills add --force` to regenerate.', 'The command catalog below comes from an upstream CLI version; it is reference material, not evidence that these commands exist locally. Verify selected commands with installed help. Do not regenerate or overwrite local skill customizations as part of ordinary Hub work.'))
edit('huggingface-datasets', lambda s: section(s.replace('Use this skill to execute read-only Dataset Viewer API calls for dataset exploration and extraction.', 'Use Dataset Viewer API calls for read-only exploration and extraction. Creating or uploading datasets is a separate operation and applies only when requested.'), 'Agent Traces', '''## Optional session-trace datasets

Only handle session traces when explicitly requested. Identify the actual trace format and location from the selected tool and user scope; do not assume an assistant-specific home directory. Inspect for sensitive content before any authorized upload, agree the destination and visibility, and default new trace datasets to private. Dataset exploration does not authorize collecting or uploading local sessions.
'''))
edit('frontend-design', lambda s: s.replace("Approach this as the design lead at a design studio known for giving every client a distinct visual identity that is not mistaken for anyone else's. This client has already rejected proposals that felt clichéd or templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take aesthetic risk if justified.", 'Make visual choices that serve the actual product, audience, and brief. Preserve an existing design system unless a redesign is requested; distinctive styling is useful when the task calls for it. Do not assume a client has rejected prior designs.').replace('identify it yourself before designing, and confirm with the client.', 'infer it from available project context and ask only if the missing information would materially affect the result.').replace(" — Anthropic's own Claude-interaction accent, so on a user's brief it reads as a tell", ''))
edit('typescript', lambda s: s.replace('Use functional and declarative programming patterns; avoid classes', 'Use functional, declarative, or class-based patterns according to the existing architecture').replace('Structure files: exported component, subcomponents, helpers, static content, types', 'Follow existing module organization; component-specific layouts apply only to UI code').replace('Use TypeScript for all code; prefer interfaces over types', 'Use TypeScript for the requested TypeScript code; choose interfaces or type aliases to fit the model without converting unrelated code').replace('Avoid enums; use maps instead', 'Follow existing enum or literal-union conventions and consider emitted runtime code').replace('Write short functions with single purpose (less than 20 lines)', 'Keep functions focused; use complexity and readability rather than a fixed line limit').replace('Keep classes under 200 lines with fewer than 10 public methods', 'Keep class responsibilities focused; split them when cohesion or readability warrants it'))
edit('python', lambda s: s.replace('Use async/await for I/O-bound operations', 'Use async/await when the surrounding stack and I/O libraries support it; do not add async wrappers around blocking calls').replace('Use Pydantic v2 for validation', 'Use the project-compatible Pydantic version for validation'))
edit('pytorch', lambda s: s.replace('Implement proper GPU utilization and mixed precision training', 'Select CPU/GPU execution and precision from supported hardware and workload needs').replace('Use Hugging Face Transformers for pre-trained models', 'Use the existing compatible model library; Hugging Face Transformers is an option for supported pretrained models').replace('Use Diffusers library for diffusion model work', 'Use Diffusers when compatible with the selected diffusion workflow').replace('Use DataParallel/DistributedDataParallel for multi-GPU', 'Use the project-compatible distributed strategy when multiple GPUs are required').replace('Apply mixed precision with `torch.cuda.amp`', 'Use the installed PyTorch version\'s supported automatic mixed precision API when hardware and numerical requirements permit it').replace('Create interactive demos for inference', 'Create an interactive demo only when the requested output calls for one'))
edit('rag', lambda s: re.sub(r'### Step 1: Choose Vector Database\n.*?(?=### Step 3:)', '''### Step 1: Choose storage

Inspect existing search/storage capabilities before adding a vector database. Compare persistence, filtering, tenant isolation, scale, operations, and cost. PostgreSQL with a suitable vector extension may fit an existing database; a separate service is optional.

### Step 2: Select embeddings

Evaluate models against the actual language, domain, quality, latency, context, cost, and privacy requirements. Record model revision, embedding dimensions, normalization, and indexing strategy. Avoid treating example model rankings as current recommendations.

''',s,flags=re.S).replace('### Example 1: Basic Document Q&A', 'The Java examples below illustrate LangChain4j. Use equivalent APIs in the selected language/framework; adopting Java is not required.\n\n### Example 1: Basic Document Q&A').replace('Use 500-1000 tokens per chunk for optimal balance', 'Treat 500-1000 tokens as an experimental starting range, not a universal optimum').replace('Start with high k values (10-20), then filter/rerank', 'Tune candidate count and reranking against measured retrieval quality and latency').replace('- **Apply content filtering** on retrieved documents before passing to LLM', '- Enforce source/tenant authorization before retrieval results reach the model; filtering alone does not prevent prompt injection'))

# Remove source-package citation mandates; preserve license and provenance metadata.
for name in ['matplotlib','seaborn','transformers']:
    edit(name, lambda s: section(s,'Citing Scientific Agent Skills', '## Attribution\n\nPreserve bundled licenses and source provenance. Include scholarly citations when relevant to the requested deliverable; this skill does not require adding a particular paper to unrelated project output.'))
edit('matplotlib', lambda s: s.replace('For project work, install Matplotlib with uv:', 'Use the project\'s dependency manager and compatible version. The following uv command illustrates the upstream example environment, not a required project pin:'))
edit('seaborn', lambda s: s.replace('## Environment and Installation', '## Environment and Installation\n\nUse the project\'s existing environment and dependency manager. The version and verification notes below describe the upstream package examples, not checks performed in this checkout or required pins for the target project.'))
edit('transformers', lambda s: s.replace('## Installation', '## Installation\n\nInspect the project\'s model and dependency requirements first. The version matrix and verification notes below describe an upstream example environment, not validation performed in this checkout or required upgrades. Use the existing dependency manager and resolve a compatible stack for the selected hardware.'))

edit('train-sentence-transformers', lambda s: s.replace('**Do not synthesize a training script from this file alone.** Open the per-type production template (`scripts/train_<type>_example.py`) and copy it as your starting point.', 'Inspect the relevant per-type template (`scripts/train_<type>_example.py`) before building a new training workflow. Reuse the project\'s existing trainer when suitable; adapt the template rather than requiring a wholesale copy.').replace('**Read these in full before writing any code. Do not triage by perceived relevance.**', 'Read the references needed for the selected model type, data format, and training behavior. Unrelated modes do not need to be loaded.').replace('### Cross-cutting: always required (regardless of task)', '### Cross-cutting: select for the task').replace('Skim the section headings on every run, even a healthy one.', 'Consult the relevant symptoms when diagnosing a problem.').replace('- **Public Hub push at end-of-run, wrapped in try-except.** On HF Jobs (ephemeral env) ALSO enable in-trainer push (`push_to_hub=True` + `hub_strategy="every_save"`). Details in `references/hf_jobs_execution.md`.', '- **Save artifacts locally by default.** Hub uploads and cloud jobs apply only when requested or otherwise authorized. Choose the repository and visibility explicitly; private is the default for new uploaded artifacts. For ephemeral jobs, arrange an authorized persistent destination before starting.').replace('These are non-negotiable contracts. Implementation lives in the production templates and references. Do not reinvent.', 'Preserve applicable numerical and data-shape requirements. Logging format, tracker, directory layout, and monitor integration are examples to adapt to the project.').replace('A monitor scrapes for this.', 'Use this format only when useful or required by the project\'s monitor.').replace('- End with `model.push_to_hub(...)` wrapped in `try/except`.', '- Save the final model locally. Enable optional Hub upload only for an authorized destination; the bundled templates require `PUSH_TO_HUB=1` and create private repos by default.').replace('3. Open `scripts/train_<type>_example.py` and copy it as your starting point.', '3. Inspect the matching template and adapt its relevant pieces to the existing training workflow.').replace('hf auth login                                          # or set HF_TOKEN with write scope (for Hub push)', 'hf auth login                                          # only when needed; write scope only for authorized uploads').replace('GPU strongly recommended. CPU works only for demos and `[SentenceTransformer]` `StaticEmbedding`.', 'Choose hardware and precision from model size, runtime budget, and supported operations. CPU can suit small runs; GPU acceleration may be necessary for practical larger training.'))

# Align executable templates with the opt-in upload policy without running training.
training = root/'skills/train-sentence-transformers'
for p in (training/'scripts').glob('train_*_example.py'):
    s = p.read_text(encoding='utf-8')
    if '.push_to_hub(RUN_NAME)' not in s:
        continue
    s = re.sub(r'Default Hub push:.*?(?=\n\n|\n""")', 'Hub upload is optional. Set PUSH_TO_HUB=1 only for an authorized upload.\nNew repositories default to private; set HF_REPO_ID for the intended destination.\nArrange authorized persistent storage separately for ephemeral jobs.',s,flags=re.S)
    s = s.replace('    try:\n        commit_url = ', '    if os.environ.get("PUSH_TO_HUB", "0") != "1":\n        logging.info("Saved locally; Hub upload disabled (PUSH_TO_HUB=0)")\n        return\n\n    try:\n        commit_url = ')
    s = re.sub(r'\.push_to_hub\(RUN_NAME\)[^\n]*', '.push_to_hub(os.environ.get("HF_REPO_ID", RUN_NAME), private=os.environ.get("HF_REPO_PRIVATE", "1") == "1")',s)
    assert 'import os' in s
    ast.parse(s)
    save(p,s)
for p in (training/'references').glob('*.md'):
    s = p.read_text(encoding='utf-8')
    if 'push_to_hub' in s or 'Monitor' in s:
        pos = re.search(r'^# [^\n]+\n',s,re.M)
        if pos:
            s = s[:pos.end()]+'\n## Project adaptation\n\nHub upload examples below apply only to authorized uploads with an explicit destination and visibility. Prefer private new repositories. For ephemeral jobs, Hub checkpointing is one option alongside authorized persistent volumes; do not launch until persistence is arranged. Use available process/log tools rather than requiring a particular assistant background-task or monitor API. The entrypoint and template upload controls take precedence over upstream defaults below.\n'+s[pos.end():]
    s = s.replace('`hf jobs logs <id> --follow` under `Bash run_in_background` pairs nicely with a `Monitor` watching for the `VERDICT:` line emitted by your training script\'s verdict block.', 'Stream `hf jobs logs <id> --follow` with the available process interface when needed. A project monitor may consume the evaluation summary; no assistant-specific background or monitor API is required.')
    s = s.replace('Fix: always set `push_to_hub=True` + `hub_model_id=...` + `secrets={"HF_TOKEN": "$HF_TOKEN"}`.', 'Fix: configure an authorized persistent destination before the next run, such as a persistent volume or an explicitly selected Hub repository with checkpoint uploads.')
    save(p,s)

# Repair routing consistency and make technical specialization explicit.
guide = root/'AGENTS.md'
s = guide.read_text(encoding='utf-8')
s = s.replace('## Restored skills\n\nThese skills are stored as real directories with their supporting files.', '### Additional skills')
pos = s.index('## Available guidance')
s = s[:pos]+'''## Applying this collection to a project

- Technology specialization is intentional: Django, React, AWS, Hugging Face, and similar guides apply only when that technology is selected. Do not install or migrate to it just because a guide exists.
- The current checkout contains a minimal README and this guidance collection; it does not yet establish application requirements, language versions, hosting, data sources, or model choices. Infer these from actual source and manifests when available, or clarify material missing requirements.
- Resolve reference/helper paths relative to the guide that names them. Run project commands in the application directory. Adapt shell syntax and temporary paths to the operating system.
- Installed versions and lockfiles govern compatibility. Upstream review dates, benchmark numbers, dependency matrices, and sample environments are provenance, not evidence of local validation or reasons to upgrade.
- Preserve local UI conventions and component APIs. Example applications, schemas, dataset names, ports, and credentials illustrate patterns and do not define the target product.
- Cloud provisioning, publishing, trace uploads, and paid model calls require task authorization. Local training does not imply public Hub uploads. Prefer private destinations for new uploaded artifacts unless the task specifies otherwise.
- Use the existing test tooling and available browser interface. Neither headed nor headless browsing, a particular package manager, nor an assistant-specific tool name is universally required.

'''+s[pos:]
save(guide,s)

related = {
'frontend-design':['web-design-guidelines','shadcn','vercel-composition-patterns'],
'hf-cli':['huggingface-datasets','transformers','train-sentence-transformers'],
'huggingface-datasets':['hf-cli','pandas-best-practices'],
'jwt-security':['django-rest-framework'],
'matplotlib':['numpy-best-practices','pandas-best-practices','seaborn'],
'numpy-best-practices':['pandas-best-practices','matplotlib','pytorch'],
'pandas-best-practices':['numpy-best-practices','seaborn','postgreSQL'],
'playwright':['webapp-testing','web-design-guidelines'],
'python':['python-testing-patterns','django'],
'python-testing-patterns':['python','django-testing'],
'pytorch':['transformers','train-sentence-transformers','lambda-cloud'],
'rag':['postgreSQL','transformers','train-sentence-transformers'],
'seaborn':['matplotlib','pandas-best-practices'],
'shadcn':['frontend-design','vercel-composition-patterns','web-design-guidelines'],
'train-sentence-transformers':['transformers','huggingface-datasets','lambda-cloud','rag'],
'transformers':['pytorch','hf-cli','train-sentence-transformers'],
'typescript':['typescript-advanced-types','vercel-composition-patterns'],
'typescript-advanced-types':['typescript'],
'vercel-composition-patterns':['typescript','shadcn'],
'web-design-guidelines':['frontend-design','playwright'],
'webapp-testing':['playwright','python-testing-patterns']
}
for name, others in related.items():
    edit(name,lambda s,others=others: s.rstrip()+'\n\n## Related guidance\n\n'+'\n'.join(f'- [{x}](../{x}/SKILL.md)' for x in others)+'\n')

# Scope the compiled React guide and its example rules consistently.
composition = root/'skills/vercel-composition-patterns'
for p in [composition/'AGENTS.md', *list((composition/'rules').glob('*.md'))]:
    s = p.read_text(encoding='utf-8')
    if p.name == 'AGENTS.md':
        pos = s.index('\n')
        s = s[:pos]+'\n\nRead the [shared conventions](../../AGENTS.md) and [skill entrypoint](SKILL.md). These are reusable React patterns, with chat/composer examples for illustration. Use composition where complexity warrants it; ordinary boolean values such as disabled remain appropriate. React 19 APIs apply only to compatible installed versions.\n'+s[pos:]
    save(p,s)

# Fix remaining contradictory scaffold assumptions.
edit('docker-project-foundations', lambda s: s.replace('Put all three files at the project root unless there is a clear multi-service layout that justifies a `docker/` subdirectory.', 'Place the files needed by the requested setup alongside the existing build/development configuration.').replace('defer detailed image optimization and advanced Compose tuning to the owning skills.', 'consult the relevant project tooling and documentation for advanced image or Compose tuning.').replace('Checks that required files exist in the current directory and validates its `compose.yaml`.', 'Checks the complete three-file starter layout and validates `compose.yaml`; use only when that layout was selected. For other valid layouts, check the applicable files and configuration directly.'))

# Keep existing duplicate guidance synchronized; do not introduce directory links.
mirrored = 0
for p in root.rglob('*'):
    if p.is_file() and p.suffix in ['.md','.yaml']:
        target = Path('.agents')/p.relative_to(root)
        if target.is_file():
            save(target,p.read_text(encoding='utf-8'))
            mirrored += 1
print(f'Changed {len(changed)} files; checked {mirrored} existing duplicate files for consistency.')
for name in sorted(changed):
    print(name)

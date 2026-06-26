# Training Guide: Mastering GitHub Actions Composite Actions

Welcome! This guide is designed to help you teach and understand **Composite Actions** in GitHub Actions. We will walk through why they are used, how they are structured, and analyze a real-world, advanced local composite action setup.

---

## 📖 Table of Contents
1. [What is a Composite Action?](#1-what-is-a-composite-action)
2. [Why Use Composite Actions?](#2-why-use-composite-actions)
3. [Comparing Action Types](#3-comparing-action-types)
4. [Anatomy of our Composite Action (`action.yml`)](#4-anatomy-of-our-composite-action-actionyml)
5. [How to Reference a Local Composite Action](#5-how-to-reference-a-local-composite-action)
6. [Best Practices for Production](#6-best-practices-for-production)
7. [Job Status Conditionals (`success()`, `failure()`, `always()`)](#7-job-status-conditionals-success-failure-always)
8. [Docker Build and Tag Pipeline](#8-docker-build-and-tag-pipeline)

---

## 1. What is a Composite Action?
A **Composite Action** allows you to combine multiple workflow steps into a single action. You can bundle multiple `run` commands or even call other actions inside a single, reusable file (`action.yml`).

Think of it as creating your own custom function in a programming language—instead of writing the same 5-10 lines of setup and installation in every workflow file, you package it once and reference it.

---

## 2. Why Use Composite Actions?
- **DRY (Don't Repeat Yourself)**: Eliminate duplicate steps across different workflows (e.g., setting up Python, configuring caching, installing dependencies).
- **Maintainability**: If your test commands or linter flags change, you only have to update them in one place (the composite action).
- **Readability**: Keeps your main workflow files (`.github/workflows/ci.yml`) clean, descriptive, and short.
- **Local Portability**: You can place them inside the same repository (e.g., under `.github/actions/`) and use them immediately without having to publish them to a public GitHub repository.

---

## 3. Comparing Action Types

| Feature | Composite Actions | JavaScript Actions | Docker Container Actions |
| :--- | :--- | :--- | :--- |
| **Language** | YAML + Shell scripts | NodeJS (JavaScript/TypeScript) | Dockerfile (Any language/OS) |
| **Speed** | Fast (runs directly on runner) | Fast (runs directly on runner) | Slower (requires building/pulling image) |
| **Runner OS** | Multi-OS (Linux, macOS, Windows) | Multi-OS (Linux, macOS, Windows) | Linux only |
| **Complexity** | Low (simple script bundling) | Medium (requires npm/compilation) | High (requires Docker knowledge) |
| **Calling other Actions** | Yes (supported since late 2021) | No (must use APIs/JS libraries) | No |

---

## 4. Anatomy of our Composite Action (`action.yml`)

Let's dissect the action located at [.github/actions/python-qa/action.yml](file:///.github/actions/python-qa/action.yml).

### A. Metadata (Name and Description)
```yaml
name: 'Python QA Composite Action'
description: 'Sets up Python environment, handles pip caching, installs dependencies, and runs Flake8 and Pytest checks.'
```
*These parameters tell GitHub Actions what name and description to show in the execution log and marketplace.*

### B. Inputs & Outputs
Inputs allow the caller workflow to pass parameters into the composite action. Outputs send values back to the workflow.

```yaml
inputs:
  python-version:
    description: 'Python version to set up'
    required: false
    default: '3.11'
  run-lint:
    description: 'Whether to run Flake8 linting checks'
    required: false
    default: 'true'
...
outputs:
  lint-status:
    description: 'Result of the lint step'
    value: ${{ steps.lint-run.outputs.status || 'skipped' }}
```
> [!TIP]
> Notice the output fallback `${{ steps.lint-run.outputs.status || 'skipped' }}`. If the lint step is skipped due to the conditional `if:`, it will return `'skipped'` instead of an empty/null value.

### C. The `runs` Definition
Unlike workflow files which define `jobs`, actions define `runs`:

```yaml
runs:
  using: 'composite'
  steps:
    - name: Setup Python environment
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
        cache: 'pip'
        cache-dependency-path: ${{ inputs.cache-dependency-path }}
```
- **`using: 'composite'`**: Tells GitHub that this is a composite action.
- **`uses:` inside steps**: We can invoke external actions (like `actions/setup-python`) directly inside the composite action!
- **Built-in Caching**: We configure `setup-python` to cache pip dependencies based on the `requirements-dev.txt` file automatically.

### D. Shell Requirement
> [!IMPORTANT]
> In a composite action, **every `run` step must explicitly specify a `shell` key** (e.g., `shell: bash` or `shell: pwsh`). If you omit it, the action will fail with a syntax error.

```yaml
    - name: Install dependencies
      shell: bash
      run: |
        python -m pip install --upgrade pip
        if [ -f "${{ inputs.cache-dependency-path }}" ]; then
          python -m pip install -r ${{ inputs.cache-dependency-path }}
        fi
```

### E. Conditionals (`if`)
You can use conditionals inside composite steps using the `if: ${{ ... }}` block:

```yaml
    - name: Run Pytest unit tests
      id: test-run
      if: ${{ inputs.run-tests == 'true' }}
      shell: bash
      run: |
        pytest
        echo "status=passed" >> $GITHUB_OUTPUT
```
- The step only runs if the caller sets `run-tests: 'true'`.
- It writes `status=passed` to `$GITHUB_OUTPUT` if successful.

---

## 5. How to Reference a Local Composite Action

In your workflow file (like [.github/workflows/ci-pipeline.yml](file:///.github/workflows/ci-pipeline.yml)), you can call a composite action that is stored in the same repository by referencing its path relative to the root directory:

```yaml
      - name: Run Python QA Composite Action
        id: qa-steps
        uses: ./.github/actions/python-qa
        with:
          python-version: '3.11'
          run-lint: 'true'
          run-tests: 'true'
```
- **`uses: ./.github/actions/python-qa`**: Note the leading `./`. This points to the folder containing the `action.yml` file.
- **`id: qa-steps`**: Crucial if you want to capture outputs. You reference them later as `${{ steps.qa-steps.outputs.lint-status }}`.

---

## 6. Best Practices for Production
1. **Never use `actions/checkout` inside a shared Composite Action**: Usually, the caller workflow is responsible for checking out the repository code. If your action checks out code, it might overwrite the user's workspace unexpectedly.
2. **Handle Operating System differences**: Since composite actions can run on Linux, macOS, and Windows, ensure shell commands are compatible. Using `shell: bash` will work on Windows if Git Bash is installed, which is standard on GitHub runners, but be mindful of OS-specific paths.
3. **Use `${{ github.action_path }}`**: If you need to access files packaged inside your composite action directory (like helper scripts or configurations), use `${{ github.action_path }}`. This points to the directory where the action is running, regardless of where it is called from.

---

## 7. Job Status Conditionals (`success()`, `failure()`, `always()`)

In GitHub Actions, you can control whether steps execute based on the status of previous steps or the overall job state. This is done using **Job Status Check Functions** in your `if:` conditionals.

Check out the demonstration workflow at [.github/workflows/status-conditionals-demo.yml](file:///.github/workflows/status-conditionals-demo.yml).

### Available Status Functions

1. **`success()`**
   - **What it does**: Evaluates to `true` if no previous step has failed or been cancelled.
   - **Default Behavior**: If you do not provide an `if:` condition for a step, GitHub Actions automatically executes it only if `success()` is true.
   - **Example**:
     ```yaml
     if: ${{ success() }}
     ```

2. **`failure()`**
   - **What it does**: Evaluates to `true` if *any* previous step in the job has failed.
   - **Typical Use Cases**: Sending alerts (Slack, email, Teams), uploading diagnostic dump files, or rolling back deployment scripts.
   - **Example**:
     ```yaml
     if: ${{ failure() }}
     ```

3. **`always()`**
   - **What it does**: Evaluates to `true` even if a step has failed, or if the run was cancelled.
   - **Typical Use Cases**: Post-run cleanups, closing SSH tunnels, tearing down temp servers, or exporting test reports.
   - **Example**:
     ```yaml
     if: ${{ always() }}
     ```

4. **`cancelled()`**
   - **What it does**: Evaluates to `true` if the workflow run has been explicitly cancelled.
   - **Example**:
     ```yaml
     if: ${{ cancelled() }}
     ```

---

### Key Concept: `continue-on-error: true`

A common source of confusion is how status check functions interact with `continue-on-error: true`.

- If a step fails **without** `continue-on-error: true`, the overall job status switches to **failed**. Subsequent standard steps are skipped, and `failure()` steps are triggered.
- If a step fails **with** `continue-on-error: true`, GitHub Actions marks the step with a warning icon, but the overall job status remains **success**. Subsequent steps containing `success()` **will still execute**, and `failure()` checks will **not** be triggered.

---

## 8. Docker Build and Tag Pipeline

To package and deploy modern software, building Docker images is a fundamental requirement. The workflow located at [.github/workflows/docker-build.yml](file:///.github/workflows/docker-build.yml) demonstrates how to automate Docker builds and tag them dynamically.

### Key Tools Used in the Pipeline

1. **QEMU (`docker/setup-qemu-action`)**:
   - Allows you to build images for multiple hardware architectures (like ARM64 for Apple Silicon and AMD64 for standard cloud servers) using emulation.

2. **Docker Buildx (`docker/setup-buildx-action`)**:
   - Installs the modern Docker Buildx builder, which provides advanced build features, including better caching mechanisms and concurrent builds.

3. **Metadata Extraction (`docker/metadata-action`)**:
   - Automatically generates Docker tags and labels based on the GitHub context.
   - For example, if pushed to `main`, it tags the image as `latest` and with the git short SHA (e.g., `sha-a1b2c3d`).
   - If pushed to a tag like `v1.2.3`, it tags the image as `v1.2.3`.

4. **Build & Push (`docker/build-push-action`)**:
   - The official action to execute `docker build`.
   - In our current training phase, we set `push: false` because we have not configured registry login credentials.

---

### Future Session: Registry Login and Image Pushing

In a production scenario, you would authenticate to a docker registry (like Docker Hub, GitHub Container Registry (GHCR), or AWS ECR) and push the image.

To authenticate and push, you would:
1. Store credentials (username, token/password) in **GitHub Repository Secrets**.
2. Enable registry authentication steps:
   ```yaml
   - name: Log in to Docker Hub
     uses: docker/login-action@v3
     with:
       username: ${{ secrets.DOCKERHUB_USERNAME }}
       password: ${{ secrets.DOCKERHUB_TOKEN }}
   ```
3. Set `push: true` in the build step:
   ```yaml
   - name: Build and Push Docker Image
     uses: docker/build-push-action@v5
     with:
       context: .
       file: ./Dockerfile
       push: true  # Changed from false to push to the registry
       tags: ${{ steps.meta.outputs.tags }}
       labels: ${{ steps.meta.outputs.labels }}
   ```


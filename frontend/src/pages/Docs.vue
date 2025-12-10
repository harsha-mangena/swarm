<template>
  <div class="p-8 space-y-8 bg-bg-primary max-w-4xl mx-auto">
    <div>
      <h1 class="text-3xl font-bold mb-4 text-text-primary">SwarmOS Documentation</h1>
      <p class="text-xl text-text-secondary">Complete guide to using SwarmOS</p>
    </div>

    <!-- Quick Start -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold text-text-primary border-b border-border pb-2">Quick Start</h2>
      <div class="bg-bg-secondary border border-border rounded-lg p-6 space-y-4">
        <div>
          <h3 class="text-lg font-medium mb-2 text-text-primary">1. Configure API Keys</h3>
          <p class="text-text-secondary">
            Go to Settings and add your API keys for the providers you want to use. At minimum, configure one provider.
          </p>
        </div>
        <div>
          <h3 class="text-lg font-medium mb-2 text-text-primary">2. Check Available Models</h3>
          <p class="text-text-secondary">
            Visit the LLMs page to see which providers and models are currently available.
          </p>
        </div>
        <div>
          <h3 class="text-lg font-medium mb-2 text-text-primary">3. Create Your First Task</h3>
          <p class="text-text-secondary">
            Go to Tasks, upload any relevant files to the knowledge base, then describe what you want to accomplish.
          </p>
        </div>
      </div>
    </section>

    <!-- Core Concepts -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold text-text-primary border-b border-border pb-2">Core Concepts</h2>
      
      <div class="space-y-6">
        <div class="bg-bg-secondary border border-border rounded-lg p-6">
          <h3 class="text-lg font-medium mb-3 text-text-primary">Tasks</h3>
          <p class="text-text-secondary mb-3">
            Tasks are the primary unit of work in SwarmOS. Each task can include:
          </p>
          <ul class="list-disc list-inside space-y-2 text-text-secondary ml-4">
            <li>A description of what you want to accomplish</li>
            <li>Knowledge base files (PDFs, documents, images) for context</li>
            <li>Queries or questions about the task</li>
          </ul>
        </div>

        <div class="bg-bg-secondary border border-border rounded-lg p-6">
          <h3 class="text-lg font-medium mb-3 text-text-primary">Agents</h3>
          <p class="text-text-secondary mb-3">
            SwarmOS uses specialized agents for different types of work:
          </p>
          <ul class="list-disc list-inside space-y-2 text-text-secondary ml-4">
            <li><strong>Researcher:</strong> Web research and information gathering</li>
            <li><strong>Analyst:</strong> Analysis and planning</li>
            <li><strong>Coder:</strong> Code generation and programming tasks</li>
            <li><strong>Reviewer:</strong> Review and critique solutions</li>
            <li><strong>Synthesizer:</strong> Final synthesis and integration</li>
          </ul>
        </div>

        <div class="bg-bg-secondary border border-border rounded-lg p-6">
          <h3 class="text-lg font-medium mb-3 text-text-primary">Debate Mechanism</h3>
          <p class="text-text-secondary">
            When multiple agents work on a task, they engage in a hybrid debate:
          </p>
          <ol class="list-decimal list-inside space-y-2 text-text-secondary ml-4 mt-3">
            <li>Each agent proposes a solution</li>
            <li>Agents critique each other's proposals</li>
            <li>Agents vote on the best proposal</li>
            <li>The system selects the winning solution based on votes, critiques, and confidence scores</li>
          </ol>
        </div>

        <div class="bg-bg-secondary border border-border rounded-lg p-6">
          <h3 class="text-lg font-medium mb-3 text-text-primary">Memory System</h3>
          <p class="text-text-secondary mb-3">
            SwarmOS uses a three-tier memory architecture:
          </p>
          <ul class="list-disc list-inside space-y-2 text-text-secondary ml-4">
            <li><strong>Global:</strong> Organization-wide knowledge</li>
            <li><strong>Task:</strong> Shared context for all agents working on the same task</li>
            <li><strong>Agent:</strong> Private scratchpad for each agent</li>
          </ul>
          <p class="text-text-secondary mt-3">
            The system automatically compresses context based on each provider's context window limits.
          </p>
        </div>
      </div>
    </section>

    <!-- API Reference -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold text-text-primary border-b border-border pb-2">API Reference</h2>
      <div class="bg-bg-secondary border border-border rounded-lg p-6">
        <p class="text-text-secondary mb-4">
          SwarmOS provides a REST API for programmatic access. All endpoints are prefixed with <code class="bg-bg-tertiary px-2 py-1 rounded text-sm">/api</code>
        </p>
        <div class="space-y-3 text-sm">
          <div>
            <code class="text-accent">POST /api/tasks</code>
            <p class="text-text-secondary mt-1">Create a new task</p>
          </div>
          <div>
            <code class="text-accent">GET /api/tasks</code>
            <p class="text-text-secondary mt-1">List all tasks</p>
          </div>
          <div>
            <code class="text-accent">GET /api/tasks/{id}</code>
            <p class="text-text-secondary mt-1">Get task details</p>
          </div>
          <div>
            <code class="text-accent">GET /api/agents</code>
            <p class="text-text-secondary mt-1">List all agents</p>
          </div>
          <div>
            <code class="text-accent">GET /api/providers/status</code>
            <p class="text-text-secondary mt-1">Get provider status</p>
          </div>
        </div>
        <p class="text-text-secondary mt-4">
          Full API documentation available at <a href="/docs" class="text-accent hover:underline">/docs</a> (Swagger UI)
        </p>
      </div>
    </section>

    <!-- Best Practices -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold text-text-primary border-b border-border pb-2">Best Practices</h2>
      <div class="bg-bg-secondary border border-border rounded-lg p-6 space-y-4">
        <div>
          <h3 class="font-medium text-text-primary mb-2">Task Descriptions</h3>
          <p class="text-text-secondary">
            Be specific and clear about what you want. Include relevant context and constraints.
          </p>
        </div>
        <div>
          <h3 class="font-medium text-text-primary mb-2">Knowledge Base</h3>
          <p class="text-text-secondary">
            Upload relevant documents, PDFs, or images before asking questions. This provides context for better results.
          </p>
        </div>
        <div>
          <h3 class="font-medium text-text-primary mb-2">Provider Selection</h3>
          <p class="text-text-secondary">
            Use "Auto" to let SwarmOS select the best provider, or choose a specific provider for consistency.
          </p>
        </div>
        <div>
          <h3 class="font-medium text-text-primary mb-2">Complex Tasks</h3>
          <p class="text-text-secondary">
            For complex tasks, the system will automatically decompose them into subtasks and use multiple agents.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
</script>


<template>
  <div class="h-[calc(100vh-3.5rem)] flex bg-bg-primary overflow-hidden" v-if="task">
    
    <!-- Sidebar -->
    <aside class="w-64 border-r border-border bg-bg-secondary flex flex-col">
      <div class="p-4 border-b border-border">
        <div class="flex items-center gap-2 mb-1">
          <router-link to="/tasks" class="text-text-tertiary hover:text-text-primary text-xs flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
            Tasks
          </router-link>
        </div>
        <div class="flex items-center justify-between">
          <h2 class="font-medium text-text-primary truncate" :title="task.description">Task {{ task.id.slice(0,6) }}</h2>
          <button 
            @click="confirmDelete" 
            class="p-1.5 hover:bg-red-500/10 rounded transition-colors group"
            title="Delete task"
          >
            <svg class="w-4 h-4 text-text-tertiary group-hover:text-red-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      
      <nav class="flex-1 p-2 space-y-1">
        <button
          v-for="tab in ['Query', 'Orchestrator', 'Agents', 'Debate', 'Output']"
          :key="tab"
          @click="activeTab = tab.toLowerCase()"
          class="w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-between"
          :class="activeTab === tab.toLowerCase() ? 'bg-bg-tertiary text-text-primary border border-border' : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50 border border-transparent'"
        >
          <span>{{ tab }}</span>
          <!-- Optional Status Indicators -->
          <span v-if="tab === 'Output' && task.status === 'completed'" class="text-success">●</span>
        </button>
      </nav>

      <!-- Status Footer -->
      <div class="p-4 border-t border-border bg-bg-tertiary/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-text-tertiary">Status</span>
          <span :class="getStatusColor(task.status)" class="text-xs font-bold uppercase">{{ task.status }}</span>
        </div>
        <div class="h-1 bg-bg-tertiary rounded-full overflow-hidden">
          <div 
            class="h-full bg-accent transition-all duration-300"
            :style="{ width: `${(task.progress || 0) * 100}%` }"
          ></div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto relative bg-bg-primary">
      
      <!-- LOADING OVERLAY -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-bg-primary z-50">
        <div class="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full"></div>
      </div>

      <!-- VIEW: QUERY -->
      <div v-if="activeTab === 'query'" class="p-8 space-y-8">
        <div>
          <h1 class="text-2xl font-light text-text-primary mb-4">Original Query</h1>
          <div class="bg-bg-secondary border border-border rounded-xl p-6 text-lg text-text-secondary leading-relaxed">
            {{ task.description }}
          </div>
        </div>
        
        <div v-if="task.context?.files?.length > 0">
          <h2 class="text-lg font-medium text-text-primary mb-3">Knowledge Base</h2>
          <div class="grid grid-cols-2 gap-4">
            <div v-for="file in task.context.files" :key="file.filename" class="flex items-center gap-3 p-3 bg-bg-tertiary rounded-lg border border-border">
              <span class="text-2xl">📄</span>
              <div class="overflow-hidden">
                <div class="text-sm font-medium text-text-primary truncate">{{ file.filename }}</div>
                <div class="text-xs text-text-tertiary">{{ formatFileSize(file.size) }}</div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h2 class="text-lg font-medium text-text-primary mb-3">Configuration</h2>
           <div class="bg-bg-tertiary rounded-lg border border-border p-4 grid grid-cols-2 gap-4 text-sm">
             <div><span class="text-text-tertiary">Provider:</span> <span class="text-text-primary">{{ task.provider }}</span></div>
             <div><span class="text-text-tertiary">Created:</span> <span class="text-text-primary">{{ formatDate(task.created_at) }}</span></div>
             <div><span class="text-text-tertiary">ID:</span> <span class="text-text-primary font-mono">{{ task.id }}</span></div>
           </div>
        </div>
      </div>

      <!-- VIEW: ORCHESTRATOR -->
      <div v-if="activeTab === 'orchestrator'" class="h-full overflow-y-auto">
        <div class="p-8 space-y-6">

          <!-- Orchestrator Thinking Section -->
          <div v-if="task.context?.delegation_plan" class="bg-bg-secondary border border-accent/30 rounded-2xl overflow-hidden">
            <div class="px-6 py-4 bg-accent/5 border-b border-accent/30 cursor-pointer hover:bg-accent/10 transition-colors" @click="thinkingExpanded = !thinkingExpanded">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-medium text-text-primary">Orchestrator Thinking</h3>
                  <p class="text-xs text-text-tertiary">Task analysis and planning</p>
                </div>
                <svg class="w-5 h-5 text-text-tertiary transition-transform" :class="{ 'rotate-180': thinkingExpanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
              </div>
            </div>
            <div v-show="thinkingExpanded" class="px-6 py-5 space-y-5">
              <!-- User Query -->
              <div>
                <div class="text-xs text-text-tertiary mb-2 uppercase tracking-wide">User Query</div>
                <p class="text-sm text-text-primary leading-relaxed">{{ task.description }}</p>
              </div>

              <!-- Task Interpretation -->
              <div v-if="task.context.delegation_plan.task_interpretation" class="border-t border-border pt-4">
                <div class="text-xs text-text-tertiary mb-2 uppercase tracking-wide">Task Interpretation</div>
                <p class="text-sm text-text-secondary leading-relaxed">{{ task.context.delegation_plan.task_interpretation }}</p>
              </div>

              <!-- Main Tasks Identified -->
              <div v-if="task.context.delegation_plan.main_tasks_identified?.length" class="border-t border-border pt-4">
                <div class="text-xs text-text-tertiary mb-3 uppercase tracking-wide">Main Tasks Identified</div>
                <ul class="space-y-2 text-sm text-text-secondary">
                  <li v-for="(mainTask, idx) in task.context.delegation_plan.main_tasks_identified" :key="idx" class="flex items-start gap-2">
                    <svg class="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                    <span>{{ mainTask }}</span>
                  </li>
                </ul>
              </div>

              <!-- Research Approach -->
              <div v-if="task.context.delegation_plan.research_approach" class="border-t border-border pt-4">
                <div class="text-xs text-text-tertiary mb-2 uppercase tracking-wide">Research Approach</div>
                <p class="text-sm text-text-secondary leading-relaxed">{{ task.context.delegation_plan.research_approach }}</p>
              </div>

              <!-- Delegation Strategy -->
              <div v-if="task.context.delegation_plan.reasoning" class="border-t border-border pt-4">
                <div class="text-xs text-text-tertiary mb-2 uppercase tracking-wide">Delegation Strategy</div>
                <p class="text-sm text-text-secondary leading-relaxed">{{ task.context.delegation_plan.reasoning }}</p>
              </div>

              <!-- Metrics -->
              <div class="border-t border-border pt-4">
                <div class="text-xs text-text-tertiary mb-3 uppercase tracking-wide">Planning Metrics</div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div class="bg-bg-tertiary rounded-lg p-3">
                    <div class="text-xs text-text-tertiary mb-1">Strategy</div>
                    <div class="text-sm font-medium text-text-primary capitalize">{{ task.context.delegation_plan.execution_strategy || 'Sequential' }}</div>
                  </div>
                  <div class="bg-bg-tertiary rounded-lg p-3">
                    <div class="text-xs text-text-tertiary mb-1">Agents</div>
                    <div class="text-sm font-medium text-text-primary">{{ task.context.delegation_plan.agents_needed?.length || 0 }}</div>
                  </div>
                  <div class="bg-bg-tertiary rounded-lg p-3">
                    <div class="text-xs text-text-tertiary mb-1">Est. Steps</div>
                    <div class="text-sm font-medium text-text-primary">{{ task.context.delegation_plan.estimated_steps || 'N/A' }}</div>
                  </div>
                  <div class="bg-bg-tertiary rounded-lg p-3">
                    <div class="text-xs text-text-tertiary mb-1">Complexity</div>
                    <div class="text-sm font-medium text-text-primary">{{ (task.context.delegation_plan.complexity_score * 10).toFixed(1) || 'N/A' }}/10</div>
                  </div>
                </div>
              </div>

              <div v-if="task.context.delegation_plan.requires_debate" class="flex items-center gap-2 text-sm text-accent border-t border-border pt-4">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span>Debate validation required for quality assurance</span>
              </div>
            </div>
          </div>

          <!-- Agents Section -->
          <div>
            <h3 class="text-lg font-medium text-text-primary mb-4">Deployed Agents</h3>
            <div v-if="taskAgents.length === 0" class="bg-bg-secondary border border-dashed border-border rounded-xl p-8 text-center">
              <p class="text-text-tertiary">Waiting for agent deployment...</p>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div 
                v-for="(agent, idx) in taskAgents" 
                :key="idx"
                class="bg-bg-secondary border border-border rounded-xl overflow-hidden hover:border-accent/50 transition-all hover:shadow-lg hover:shadow-accent/5"
              >
                <div class="p-4 border-b border-border bg-bg-tertiary/30">
                  <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-lg bg-bg-primary border border-border flex items-center justify-center">
                        <span class="text-xs font-mono text-text-primary">A{{ idx + 1 }}</span>
                      </div>
                      <span class="font-medium text-text-primary">{{ agent.name || agent.agent_type }}</span>
                    </div>
                    <span v-if="agent.status" class="text-xs px-2 py-1 rounded-full" :class="agent.status === 'active' || agent.status === 'completed' ? 'bg-success/20 text-success' : 'bg-bg-primary text-text-tertiary'">
                      {{ agent.status }}
                    </span>
                  </div>
                  <div class="text-xs text-text-tertiary capitalize">{{ agent.agent_type }} Agent</div>
                </div>
                <div class="p-4 space-y-3">
                  <div>
                    <div class="text-xs text-text-tertiary mb-1">Role</div>
                    <div class="text-xs text-text-secondary">{{ getAgentDescription(agent.agent_type) }}</div>
                  </div>
                  <div class="flex items-center gap-1 text-xs text-text-tertiary">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <span>{{ hasResearchCapability(agent.agent_type) ? 'Research enabled' : 'No research' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="bg-bg-secondary border border-border rounded-2xl px-6 py-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-text-tertiary">Overall Progress</span>
              <span class="text-sm font-medium text-text-primary">{{ Math.round((task.progress || 0) * 100) }}%</span>
            </div>
            <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div 
                class="h-full bg-accent transition-all duration-500"
                :style="{ width: `${(task.progress || 0) * 100}%` }"
              ></div>
            </div>
          </div>

        </div>
      </div>

      <!-- VIEW: AGENTS -->
      <div v-if="activeTab === 'agents'" class="h-full overflow-hidden flex">
        
        <!-- Agents Sidebar -->
        <aside class="w-64 border-r border-border bg-bg-secondary flex flex-col overflow-y-auto">
          <div class="p-4 border-b border-border">
            <h3 class="text-sm font-medium text-text-primary mb-1">Agents</h3>
            <p class="text-xs text-text-tertiary">{{ subtasks.length }} tasks</p>
          </div>
          <div class="p-2 space-y-1">
            <div
              v-for="(subtask, idx) in subtasks"
              :key="idx"
              @click="selectedAgentIndex = idx"
              class="p-3 rounded-lg cursor-pointer transition-colors"
              :class="selectedAgentIndex === idx ? 'bg-accent/10 border border-accent/30' : 'hover:bg-bg-tertiary border border-transparent'"
            >
              <div class="flex items-center gap-2 mb-1">
                <div class="w-6 h-6 rounded bg-bg-primary border border-border flex items-center justify-center">
                  <span class="text-xs font-mono text-text-primary">A{{ idx + 1 }}</span>
                </div>
                <span class="text-sm font-medium text-text-primary">{{ getAgentName(subtask.agent_id) || subtask.agent_type }}</span>
              </div>
              <div class="text-xs text-text-tertiary capitalize ml-8">{{ subtask.agent_type }}</div>
              <div class="flex items-center justify-between mt-2 ml-8">
                <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getSubtaskStatusClass(subtask.status)">
                  {{ subtask.status }}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Agent Work Detail -->
        <div class="flex-1 overflow-y-auto bg-bg-primary">
          <div v-if="subtasks.length === 0" class="h-full flex items-center justify-center">
            <div class="text-center">
              <p class="text-text-tertiary">No agent activity yet.</p>
              <p class="text-xs text-text-tertiary mt-1">Agents will appear here as they start working.</p>
            </div>
          </div>
          <div v-else-if="subtasks[selectedAgentIndex]" class="p-8">
            <div class="bg-bg-secondary border border-border rounded-xl overflow-hidden">
              <!-- Agent Header -->
              <div class="p-6 border-b border-border bg-bg-tertiary/30">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-start gap-4">
                    <div class="w-12 h-12 rounded-lg bg-bg-primary border border-border flex items-center justify-center">
                      <span class="text-lg font-mono text-text-primary">A{{ selectedAgentIndex + 1 }}</span>
                    </div>
                    <div>
                      <h2 class="text-xl font-medium text-text-primary">{{ getAgentName(subtasks[selectedAgentIndex].agent_id) || subtasks[selectedAgentIndex].agent_type }}</h2>
                      <p class="text-sm text-text-tertiary capitalize">{{ subtasks[selectedAgentIndex].agent_type }} Agent</p>
                    </div>
                  </div>
                  <span class="text-xs px-3 py-1.5 rounded-full font-medium" :class="getSubtaskStatusClass(subtasks[selectedAgentIndex].status)">
                    {{ subtasks[selectedAgentIndex].status }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span class="text-text-tertiary">Created:</span>
                    <span class="text-text-secondary ml-2">{{ formatDate(subtasks[selectedAgentIndex].created_at) }}</span>
                  </div>
                  <div>
                    <span class="text-text-tertiary">Task:</span>
                    <span class="text-text-secondary ml-2">#{{ selectedAgentIndex + 1 }}</span>
                  </div>
                </div>
              </div>

              <!-- Task Description -->
              <div class="p-6 border-b border-border">
                <h3 class="text-xs text-text-tertiary mb-3 uppercase tracking-wide">Task Description</h3>
                <p class="text-sm text-text-primary leading-relaxed">{{ subtasks[selectedAgentIndex].description }}</p>
              </div>

              <!-- Agent Output -->
              <div v-if="subtasks[selectedAgentIndex].result" class="p-6">
                <h3 class="text-xs text-text-tertiary mb-4 uppercase tracking-wide flex items-center gap-2">
                  <span>Agent Output</span>
                  <svg class="w-3 h-3 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </h3>
                <div class="bg-bg-tertiary rounded-xl p-6 border border-border markdown-content" v-html="renderMarkdown(subtasks[selectedAgentIndex].result)"></div>
              </div>
              <div v-else class="p-6">
                <div class="bg-bg-tertiary rounded-xl p-8 border border-dashed border-border text-center">
                  <p class="text-text-tertiary text-sm">Agent hasn't produced output yet</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- VIEW: DEBATE -->
      <div v-if="activeTab === 'debate'" class="h-full overflow-hidden flex">
        
        <!-- Debate Participants Sidebar -->
        <aside class="w-64 border-r border-border bg-bg-secondary flex flex-col overflow-y-auto">
          <div class="p-4 border-b border-border">
            <h3 class="text-sm font-medium text-text-primary mb-1">Debate Participants</h3>
            <p class="text-xs text-text-tertiary">{{ validation?.critiques?.length || 0 }} agent{{ validation?.critiques?.length !== 1 ? 's' : '' }} reviewed</p>
          </div>
          <div v-if="validation?.critiques?.length" class="p-2 space-y-1">
            <div
              v-for="(critique, idx) in validation.critiques"
              :key="idx"
              @click="selectedDebateIndex = idx"
              class="p-3 rounded-lg cursor-pointer transition-colors"
              :class="selectedDebateIndex === idx ? 'bg-accent/10 border border-accent/30' : 'hover:bg-bg-tertiary border border-transparent'"
            >
              <div class="flex items-center gap-2 mb-1">
                <div class="w-6 h-6 rounded bg-bg-primary border border-border flex items-center justify-center">
                  <span class="text-xs font-mono text-text-primary">A{{ idx + 1 }}</span>
                </div>
                <span class="text-sm font-medium text-text-primary capitalize">{{ critique.agent_type }}</span>
              </div>
              <div class="flex items-center justify-between mt-2 ml-8">
                <span class="text-xs px-2 py-0.5 rounded-full font-medium bg-accent/20 text-accent">
                  {{ validation.scores?.[critique.agent_id]?.toFixed(1) || '?' }}/10
                </span>
              </div>
            </div>
          </div>
          <div v-else class="p-4 text-center text-text-tertiary text-sm">
            No validation data yet
          </div>
        </aside>

        <!-- Debate Critique Detail -->
        <div class="flex-1 overflow-y-auto bg-bg-primary">
          <div v-if="!validation" class="h-full flex items-center justify-center">
            <div class="text-center">
              <p class="text-text-tertiary">Waiting for validation phase...</p>
              <p class="text-xs text-text-tertiary mt-1">Supervisor will review agent work here</p>
            </div>
          </div>
          <div v-else-if="validation.critiques?.length === 0" class="h-full flex items-center justify-center">
            <div class="text-center">
              <p class="text-text-tertiary">No supervisor critiques recorded</p>
            </div>
          </div>
          <div v-else-if="validation.critiques[selectedDebateIndex]" class="p-8 space-y-6">
            
            <!-- Agent's Work Card -->
            <div class="bg-bg-secondary border border-border rounded-xl overflow-hidden">
              <div class="px-6 py-4 bg-bg-tertiary/30 border-b border-border">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-bg-primary border border-border flex items-center justify-center">
                    <span class="text-sm font-mono text-text-primary">A{{ selectedDebateIndex + 1 }}</span>
                  </div>
                  <div>
                    <h3 class="text-base font-medium text-text-primary capitalize">{{ validation.critiques[selectedDebateIndex].agent_type }} Agent</h3>
                    <p class="text-xs text-text-tertiary">Agent Output</p>
                  </div>
                </div>
              </div>
              <div class="p-6">
                <div class="text-sm text-text-secondary leading-relaxed" v-if="getAgentOutput(validation.critiques[selectedDebateIndex].agent_id)">
                  {{ getAgentOutput(validation.critiques[selectedDebateIndex].agent_id).substring(0, 500) }}...
                </div>
                <div v-else class="text-sm text-text-tertiary italic">
                  Agent output not available
                </div>
              </div>
            </div>

            <!-- Supervisor's Critique Card -->
            <div class="bg-accent/5 border border-accent/30 rounded-xl overflow-hidden">
              <div class="px-6 py-4 bg-accent/10 border-b border-accent/30">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-bg-primary border border-accent flex items-center justify-center">
                      <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </div>
                    <div>
                      <h3 class="text-base font-medium text-text-primary">Supervisor Review</h3>
                      <p class="text-xs text-text-tertiary">Quality Control & Guidance</p>
                    </div>
                  </div>
                  <span class="text-sm px-3 py-1.5 rounded-full font-medium bg-accent/20 text-accent">
                    Score: {{ validation.scores?.[validation.critiques[selectedDebateIndex].agent_id]?.toFixed(1) || '?' }}/10
                  </span>
                </div>
              </div>
              <div class="p-6">
                <div class="bg-bg-primary rounded-xl p-5 border border-border prose prose-invert prose-sm max-w-none">
                  <div class="markdown-content" v-html="renderMarkdown(validation.critiques[selectedDebateIndex].critique)"></div>
                </div>
              </div>
            </div>

            <!-- Overall Summary -->
            <div v-if="validation.summary" class="bg-bg-secondary border border-border rounded-xl p-6">
              <h3 class="text-xs text-text-tertiary mb-3 uppercase tracking-wide">Overall Assessment</h3>
              <p class="text-sm text-text-secondary leading-relaxed">{{ validation.summary }}</p>
            </div>
          </div>
        </div>

      </div>

      <!-- VIEW: OUTPUT -->
      <div v-if="activeTab === 'output'" class="h-full flex flex-col overflow-hidden">
        <!-- Scrollable Output Section -->
        <div class="flex-1 overflow-y-auto p-8">
          <div class="bg-bg-secondary border border-border rounded-xl shadow-lg overflow-hidden">
            <div class="bg-bg-tertiary p-4 border-b border-border flex items-center justify-between">
              <h1 class="font-medium text-text-primary">Final Output</h1>
              <button 
                @click="copyOutput" 
                class="text-xs bg-bg-primary hover:bg-bg-elevated border border-border px-3 py-1 rounded transition-colors text-text-primary"
              >
                {{ copied ? 'Copied!' : 'Copy' }}
              </button>
            </div>
            <div class="p-8">
              <div v-if="!task.result" class="text-center text-text-tertiary py-12">
                <p class="mb-2">Processing task...</p>
                <p class="text-sm">Check back soon</p>
              </div>
              <div v-else class="markdown-content" v-html="renderMarkdown(task.result.content || JSON.stringify(task.result, null, 2))"></div>
            </div>
          </div>
        </div>

        <!-- Chatbot RAG Section (Fixed at bottom) -->
        <div class="shrink-0 border-t border-border bg-bg-secondary">
          <div class="border-b border-border px-4 py-3">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center">
                <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
              </div>
              <div>
                <h2 class="font-medium text-text-primary text-sm">Ask Follow-up Questions</h2>
                <p class="text-xs text-text-tertiary">Use web search or redirect to specific agents</p>
              </div>
            </div>
          </div>
          
          <!-- Chat Messages (scrollable within fixed height) -->
          <div class="max-h-48 overflow-y-auto p-4 space-y-3" v-if="chatMessages.length">
            <div 
              v-for="(msg, idx) in chatMessages" 
              :key="idx"
              :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
            >
              <div 
                :class="msg.role === 'user' 
                  ? 'bg-accent/20 border border-accent/30 text-text-primary rounded-xl px-4 py-2 max-w-[80%]' 
                  : 'bg-bg-tertiary border border-border text-text-primary rounded-xl px-4 py-2 max-w-[80%]'"
              >
                <div v-if="msg.role === 'assistant' && msg.agent" class="text-xs text-accent mb-1 font-medium">
                  {{ msg.agent }}
                </div>
                <div v-if="msg.role === 'assistant'" class="text-sm markdown-content prose-sm" v-html="renderMarkdown(msg.content)"></div>
                <div v-else class="text-sm">{{ msg.content }}</div>
                <div v-if="msg.role === 'assistant' && msg.sources" class="flex gap-2 mt-2 flex-wrap">
                  <span v-for="(src, sidx) in msg.sources" :key="sidx" class="text-xs bg-bg-primary px-2 py-0.5 rounded border border-border text-text-tertiary">
                    🔗 {{ src }}
                  </span>
                </div>
              </div>
            </div>
            <div v-if="chatLoading" class="flex justify-start">
              <div class="bg-bg-tertiary border border-border rounded-xl px-4 py-3">
                <div class="flex items-center gap-2 text-text-tertiary text-sm">
                  <div class="animate-spin w-4 h-4 border-2 border-accent border-t-transparent rounded-full"></div>
                  Thinking...
                </div>
              </div>
            </div>
          </div>
          
          <!-- Agent Pills -->
          <div class="px-4 py-2 border-t border-border bg-bg-tertiary/30" v-if="taskAgents.length">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-xs text-text-tertiary">Ask agent:</span>
              <button 
                v-for="agent in taskAgents" 
                :key="agent.id || agent.name"
                @click="setTargetAgent(agent)"
                :class="targetAgent?.name === agent.name 
                  ? 'bg-accent text-bg-primary border-accent' 
                  : 'bg-bg-primary text-text-secondary border-border hover:border-accent/50'"
                class="text-xs px-2 py-1 rounded-full border transition-colors capitalize"
              >
                {{ agent.name || agent.agent_type }}
              </button>
              <button 
                v-if="targetAgent"
                @click="targetAgent = null"
                class="text-xs text-text-tertiary hover:text-text-primary"
              >
                ✕ Clear
              </button>
            </div>
          </div>
          
          <!-- Input Area -->
          <div class="p-4 border-t border-border bg-bg-secondary">
            <div class="flex gap-3">
              <div class="flex-1 relative">
                <input 
                  v-model="chatInput"
                  @keydown.enter="sendChatMessage"
                  type="text"
                  placeholder="Ask a follow-up question..."
                  class="w-full bg-bg-primary border border-border rounded-lg px-4 py-3 text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
                  :disabled="chatLoading"
                />
              </div>
              <button 
                @click="toggleWebSearch"
                :class="useWebSearch ? 'bg-accent text-bg-primary' : 'bg-bg-tertiary text-text-secondary hover:text-text-primary'"
                class="px-3 py-3 rounded-lg border border-border transition-colors"
                title="Toggle web search"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </button>
              <button 
                @click="sendChatMessage"
                :disabled="!chatInput.trim() || chatLoading"
                class="bg-accent text-bg-primary px-4 py-3 rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent-hover transition-colors"
              >
                Send
              </button>
            </div>
            <div class="flex items-center gap-4 mt-2 text-xs text-text-tertiary">
              <span v-if="useWebSearch" class="flex items-center gap-1">
                <span class="text-accent">●</span> Web search enabled
              </span>
              <span v-if="targetAgent" class="flex items-center gap-1">
                <span class="text-accent">●</span> Asking {{ targetAgent.name || targetAgent.agent_type }}
              </span>
            </div>
          </div>
        </div>
      </div>

    </main>
  </div>
  <div v-else class="h-screen flex items-center justify-center text-text-tertiary">
    Loading...
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import { marked } from 'marked'

const route = useRoute()
const activeTab = ref('orchestrator')
const task = ref(null)
const taskMemory = ref([])
const subtasks = ref([])
const validation = ref(null)
const allAgents = ref([])
const loading = ref(true)
const thinkingExpanded = ref(true)
const copied = ref(false)
const selectedAgentIndex = ref(0)
const selectedDebateIndex = ref(0)
let refreshInterval = null

// Chatbot state
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const useWebSearch = ref(false)
const targetAgent = ref(null)

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true
})

// Render markdown safely
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (e) {
    return content
  }
}

// Copy output to clipboard
const copyOutput = async () => {
  if (!task.value?.result) return
  try {
    const content = task.value.result.content || JSON.stringify(task.value.result, null, 2)
    await navigator.clipboard.writeText(content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

// Computed
const taskAgents = computed(() => {
  if (!task.value?.agents_count && !subtasks.value.length) return []
  // Logic to deduce agents involved
  if (task.value?.context?.delegation_plan?.agents_needed) {
     return task.value.context.delegation_plan.agents_needed.map(p => ({
       name: p.agent_name,
       agent_type: p.agent_type,
       status: 'active'
     }))
  }
  // Fallback to deduping from subtasks
  const agentsMap = new Map()
  subtasks.value.forEach(st => {
    if (!agentsMap.has(st.agent_id)) {
      agentsMap.set(st.agent_id, { 
        id: st.agent_id, 
        name: getAgentName(st.agent_id) || st.agent_type, 
        agent_type: st.agent_type,
        status: 'idle'
      })
    }
  })
  return Array.from(agentsMap.values())
})

// Helpers
const getAgentName = (agentId) => {
  if (!allAgents.value || !agentId) return null
  const agent = allAgents.value.find(a => a.id === agentId)
  return agent ? agent.name : null
}

const getAgentIcon = (type) => {
  const map = {
    'researcher': '🔍',
    'analyst': '📊',
    'coder': '💻',
    'reviewer': '🧐',
    'synthesizer': '📝'
  }
  return map[type?.toLowerCase()] || '🤖'
}

const getAgentDescription = (type) => {
  const descriptions = {
    'researcher': 'Conducts web research and information gathering using search tools',
    'analyst': 'Analyzes data, creates plans, and structures information',
    'coder': 'Generates, reviews, and optimizes code solutions',
    'reviewer': 'Reviews and critiques solutions for quality and accuracy',
    'synthesizer': 'Combines multiple perspectives into coherent final output'
  }
  return descriptions[type?.toLowerCase()] || 'Multi-purpose reasoning and task execution'
}

// Chatbot functions
const toggleWebSearch = () => {
  useWebSearch.value = !useWebSearch.value
}

const setTargetAgent = (agent) => {
  if (targetAgent.value?.name === agent.name) {
    targetAgent.value = null
  } else {
    targetAgent.value = agent
  }
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || chatLoading.value) return
  
  const userMessage = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', content: userMessage })
  chatInput.value = ''
  chatLoading.value = true
  
  try {
    const response = await api.post(`/tasks/${task.value.id}/chat`, {
      message: userMessage,
      use_web_search: useWebSearch.value,
      target_agent: targetAgent.value?.agent_type || null,
      context: {
        task_description: task.value.description,
        task_result: task.value.result?.content?.substring(0, 2000) || '',
        agents: taskAgents.value.map(a => a.name || a.agent_type)
      }
    })
    
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.response,
      agent: response.data.agent || (targetAgent.value?.name || targetAgent.value?.agent_type),
      sources: response.data.sources || []
    })
  } catch (e) {
    console.error('Chat error:', e)
    chatMessages.value.push({
      role: 'assistant',
      content: 'Sorry, I encountered an error processing your question. Please try again.',
      agent: 'System'
    })
  } finally {
    chatLoading.value = false
  }
}

const hasResearchCapability = (type) => {
  // All agents have auto_web_search capability via BaseAgent
  // They will search if TAVILY_API_KEY is configured
  return true
}

const getSatelliteStyle = (idx, total) => {
  const radius = 160 // px
  const angle = (idx / total) * 2 * Math.PI - (Math.PI / 2) // Start top
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  return {
    transform: `translate(${x}px, ${y}px)`
  }
}

const formatDate = (d) => new Date(d).toLocaleString()
const formatFileSize = (bytes) => {
  if(!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes)/Math.log(k))
  return parseFloat((bytes/Math.pow(k,i)).toFixed(1)) + ' ' + sizes[i]
}

const getStatusColor = (status) => {
    if(status === 'completed') return 'text-success'
    if(status === 'failed') return 'text-red-500'
    return 'text-accent'
}

const getAgentOutput = (agentId) => {
  const subtask = subtasks.value.find(st => st.agent_id === agentId)
  return subtask?.result || ''
}

const getSubtaskStatusClass = (status) => {
  if (status === 'completed') return 'text-success bg-success/10 px-2 py-0.5 rounded'
  if (status === 'in_progress') return 'text-accent bg-accent/10 px-2 py-0.5 rounded'
  return 'text-text-tertiary'
}

const confirmDelete = () => {
  if (confirm(`Are you sure you want to delete this task?\n\nTask: ${task.value.description.substring(0, 100)}...\n\nThis action cannot be undone.`)) {
    deleteTask()
  }
}

const deleteTask = async () => {
  try {
    await api.deleteTask(route.params.id)
    // Navigate back to tasks list
    window.location.href = '/tasks'
  } catch (error) {
    console.error('Failed to delete task:', error)
    alert('Failed to delete task. Please try again.')
  }
}

// Data Loading
const loadTask = async () => {
  try {
    task.value = await api.getTask(route.params.id)
    
    // Subtasks
    if (task.value.subtasks?.length) subtasks.value = task.value.subtasks
    else {
      try {
         const res = await api.getTaskSubtasks(route.params.id)
         subtasks.value = res.subtasks || []
      } catch(e) {}
    }

    // Validation
    if (task.value.validation_results) validation.value = task.value.validation_results
    else {
      try {
         const res = await api.getTaskValidation(route.params.id)
         validation.value = res.validation
      } catch(e) {}
    }

    // Memory
    try {
      taskMemory.value = await api.getTaskMemory(route.params.id)
    } catch(e) {}

  } catch (error) {
    console.error('Failed to load task:', error)
  } finally {
    loading.value = false
  }
}

const loadAgents = async () => {
  try { allAgents.value = await api.getAgents() } catch(e) {}
}

onMounted(() => {
  loadTask()
  loadAgents()
  refreshInterval = setInterval(() => { loadTask(); loadAgents() }, 3000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
/* Markdown content styling */
.markdown-content {
  color: var(--color-text-primary);
  line-height: 1.7;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  color: var(--color-text-primary);
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-content :deep(h1) { font-size: 2em; }
.markdown-content :deep(h2) { font-size: 1.5em; }
.markdown-content :deep(h3) { font-size: 1.25em; }

.markdown-content :deep(p) {
  margin-bottom: 1em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-content :deep(code) {
  background: var(--color-bg-tertiary);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: var(--color-bg-tertiary);
  padding: 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 1em;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--color-border);
  padding-left: 1em;
  margin: 1em 0;
  color: var(--color-text-secondary);
}

.markdown-content :deep(a) {
  color: var(--color-accent);
  text-decoration: underline;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 0.5em;
  text-align: left;
}

.markdown-content :deep(th) {
  background: var(--color-bg-tertiary);
  font-weight: 600;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 2em 0;
}
</style>

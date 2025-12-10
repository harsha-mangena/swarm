<template>
  <div class="h-[calc(100vh-3.5rem)] bg-bg-primary overflow-hidden relative">
    
    <!-- Circuit Pattern Background (top right) -->
    <div class="absolute top-0 right-0 w-96 h-96 opacity-[0.05] pointer-events-none">
      <svg viewBox="0 0 200 200" class="w-full h-full">
        <defs>
          <pattern id="circuit" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M20 0 L20 15 M20 25 L20 40 M0 20 L15 20 M25 20 L40 20" stroke="currentColor" stroke-width="0.5" fill="none"/>
            <circle cx="20" cy="20" r="2" fill="none" stroke="currentColor" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="200" height="200" fill="url(#circuit)" class="text-text-primary"/>
      </svg>
    </div>

    <!-- Main Content -->
    <div class="relative z-10 h-full flex flex-col items-center justify-center px-4 md:px-8">
      
      <!-- Title -->
      <h1 class="text-2xl md:text-4xl font-light text-text-primary mb-12 md:mb-20 tracking-wide text-center">
        Multi-agent orchestration platform
      </h1>

      <!-- Flow Diagram Container -->
      <div class="relative w-full max-w-5xl mx-auto mb-12 md:mb-16">
        
        <!-- SVG Connection Lines -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none overflow-visible" style="top: -60px; height: calc(100% + 60px);">
          <!-- Main horizontal line at top -->
          <line x1="10%" y1="30" x2="90%" y2="30" class="stroke-border" stroke-width="1.5"/>
          
          <!-- Curved corner from Query going up -->
          <path d="M 10% 60 L 10% 40 Q 10% 30, 12% 30" class="stroke-border" stroke-width="1.5" fill="none"/>
          
          <!-- Curved corner going down to Output -->
          <path d="M 88% 30 Q 90% 30, 90% 40 L 90% 60" class="stroke-border" stroke-width="1.5" fill="none"/>
          
          <!-- Vertical drops to each card -->
          <line x1="30%" y1="30" x2="30%" y2="60" class="stroke-border" stroke-width="1.5"/>
          <line x1="50%" y1="30" x2="50%" y2="60" class="stroke-border" stroke-width="1.5"/>
          <line x1="70%" y1="30" x2="70%" y2="60" class="stroke-border" stroke-width="1.5"/>
          
          <!-- Arrow heads -->
          <polygon points="29.3%,58 30%,68 30.7%,58" class="fill-border"/>
          <polygon points="49.3%,58 50%,68 50.7%,58" class="fill-border"/>
          <polygon points="69.3%,58 70%,68 70.7%,58" class="fill-border"/>
          <polygon points="89.3%,58 90%,68 90.7%,58" class="fill-border"/>
        </svg>

        <!-- Cards Row -->
        <div class="flex items-stretch justify-center gap-3 md:gap-5 pt-4">
          
          <!-- Card 1: Query -->
          <div class="flex-1 max-w-[160px] md:max-w-[180px]">
            <div class="h-full bg-bg-secondary border border-border rounded-2xl p-4 md:p-5 hover:border-border-hover transition-all duration-300">
              <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-bg-tertiary border border-border flex items-center justify-center mb-3 md:mb-4">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <h3 class="text-text-primary font-medium text-sm md:text-base mb-2">Query</h3>
              <p class="text-[11px] md:text-xs text-text-tertiary leading-relaxed">
                Submit your task in natural language and retrieve results.
              </p>
            </div>
          </div>

          <!-- Card 2: Orchestrator -->
          <div class="flex-1 max-w-[160px] md:max-w-[180px]">
            <div class="h-full bg-bg-secondary border border-border rounded-2xl p-4 md:p-5 hover:border-border-hover transition-all duration-300">
              <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-bg-tertiary border border-border flex items-center justify-center mb-3 md:mb-4">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              </div>
              <h3 class="text-text-primary font-medium text-sm md:text-base mb-2">Orchestrator</h3>
              <p class="text-[11px] md:text-xs text-text-tertiary leading-relaxed">
                Coordinates agents and manages task delegation.
              </p>
            </div>
          </div>

          <!-- Card 3: Agents -->
          <div class="flex-1 max-w-[160px] md:max-w-[180px]">
            <div class="h-full bg-bg-secondary border border-border rounded-2xl p-4 md:p-5 hover:border-border-hover transition-all duration-300">
              <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-bg-tertiary border border-border flex items-center justify-center mb-3 md:mb-4">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                </svg>
              </div>
              <h3 class="text-text-primary font-medium text-sm md:text-base mb-2">Agents</h3>
              <p class="text-[11px] md:text-xs text-text-tertiary leading-relaxed">
                Specialized agents work on different aspects of your task.
              </p>
            </div>
          </div>

          <!-- Card 4: Debate -->
          <div class="flex-1 max-w-[160px] md:max-w-[180px]">
            <div class="h-full bg-bg-secondary border border-border rounded-2xl p-4 md:p-5 hover:border-border-hover transition-all duration-300">
              <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-bg-tertiary border border-border flex items-center justify-center mb-3 md:mb-4">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
              </div>
              <h3 class="text-text-primary font-medium text-sm md:text-base mb-2">Debate</h3>
              <p class="text-[11px] md:text-xs text-text-tertiary leading-relaxed">
                Agents review each other's work to reach consensus.
              </p>
            </div>
          </div>

          <!-- Card 5: Output -->
          <div class="flex-1 max-w-[160px] md:max-w-[180px]">
            <div class="h-full bg-bg-secondary border border-border rounded-2xl p-4 md:p-5 hover:border-border-hover transition-all duration-300">
              <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-bg-tertiary border border-border flex items-center justify-center mb-3 md:mb-4">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                </svg>
              </div>
              <h3 class="text-text-primary font-medium text-sm md:text-base mb-2">Output</h3>
              <p class="text-[11px] md:text-xs text-text-tertiary leading-relaxed">
                Final synthesized result combining all contributions.
              </p>
            </div>
          </div>

        </div>
      </div>

      <!-- CTA Button -->
      <router-link 
        to="/tasks" 
        class="group inline-flex items-center gap-3 px-7 py-3.5 bg-accent text-bg-primary text-sm font-medium rounded-full hover:bg-accent-hover transition-all duration-300"
      >
        <span>Start a Task</span>
        <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
        </svg>
      </router-link>

    </div>
  </div>
</template>

<style scoped>
/* SVG stroke uses CSS variable */
.stroke-border {
  stroke: var(--color-border);
}
.fill-border {
  fill: var(--color-border);
}
</style>

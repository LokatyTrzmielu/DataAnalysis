<template>
  <div>
    <div class="mb-6">
      <h2 style="font-family:'SF Pro Display','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:28px;font-weight:600;color:var(--app-text);line-height:1.14;letter-spacing:-0.28px">
        Tools
      </h2>
      <p class="mt-1" style="font-size:14px;color:var(--app-text-sec)">Utilities for preparing and managing your data.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">

      <!-- Data Preparation -->
      <RouterLink to="/tools/data-preparation" class="card-apple block no-underline group" style="cursor:pointer">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center" style="background:rgba(0,113,227,0.1)">
            <svg class="w-5 h-5" style="color:#0071e3" viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/>
              <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/>
              <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p style="font-size:15px;font-weight:600;color:var(--app-text);letter-spacing:-0.24px">Data Preparation</p>
            <p class="mt-1" style="font-size:12px;color:var(--app-text-sec);line-height:1.4">Merge multiple Excel or CSV files into a single dataset ready for analysis.</p>
          </div>
        </div>
        <div class="mt-4 flex items-center justify-end">
          <span style="font-size:12px;font-weight:500;color:#0071e3">Open →</span>
        </div>
      </RouterLink>

      <!-- Placeholder 1 -->
      <div class="card-apple" style="opacity:0.45;cursor:default">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center" style="background:rgba(0,0,0,0.05)">
            <svg class="w-5 h-5" style="color:var(--app-text-sec)" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p style="font-size:15px;font-weight:600;color:var(--app-text);letter-spacing:-0.24px">Coming soon</p>
              <span class="rounded px-1.5 py-0.5" style="font-size:10px;background:rgba(0,0,0,0.06);color:var(--app-text-sec)">Soon</span>
            </div>
            <p class="mt-1" style="font-size:12px;color:var(--app-text-sec);line-height:1.4">New tool under development.</p>
          </div>
        </div>
      </div>

      <!-- Placeholder 2 -->
      <div class="card-apple" style="opacity:0.45;cursor:default">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center" style="background:rgba(0,0,0,0.05)">
            <svg class="w-5 h-5" style="color:var(--app-text-sec)" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p style="font-size:15px;font-weight:600;color:var(--app-text);letter-spacing:-0.24px">Coming soon</p>
              <span class="rounded px-1.5 py-0.5" style="font-size:10px;background:rgba(0,0,0,0.06);color:var(--app-text-sec)">Soon</span>
            </div>
            <p class="mt-1" style="font-size:12px;color:var(--app-text-sec);line-height:1.4">New tool under development.</p>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

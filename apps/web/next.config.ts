import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't auto-generate/maintain AGENTS.md + CLAUDE.md on every `next dev`/
  // `next build` — this repo already documents itself (see /docs and
  // apps/web/README.md).
  agentRules: false,
};

export default nextConfig;

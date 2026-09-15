// Mirrors apps/api/app/schemas/*.py. Kept as plain types (no codegen) —
// see docs/API_SPEC.md for the source of truth.

export type UserRole = "admin" | "editor";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export type ProjectStatus = "active" | "inactive";

export interface Project {
  id: number;
  project_name: string;
  website_url: string;
  industry: string | null;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectKnowledgeBase {
  id: number;
  project_id: number;
  brand_name: string | null;
  brand_voice_tone: string | null;
  target_audience: string | null;
  industry_context: string | null;
  style_guidelines: string | null;
  forbidden_words: string[] | null;
  mandatory_points: string[] | null;
  sample_reference_urls: string[] | null;
  custom_rules: Record<string, unknown> | null;
}

export type PageType = "product" | "article" | "category";

export interface TargetPage {
  id: number;
  project_id: number;
  title: string;
  url: string;
  main_keyword: string;
  page_type: PageType;
  priority: number;
  created_at: string;
}

export type KeywordType = "main" | "related" | "semantic";

export interface Keyword {
  id: number;
  target_page_id: number;
  keyword: string;
  type: KeywordType;
  source: "ai" | "manual";
}

export type AnchorType = "exact" | "partial" | "semantic" | "brand";

export interface Anchor {
  id: number;
  target_page_id: number;
  anchor_text: string;
  anchor_type: AnchorType;
  usage_limit: number | null;
  usage_count: number;
  is_active: boolean;
}

export interface AnchorDistribution {
  target_page_id: number;
  window_size: number;
  target_ratio: Record<string, number>;
  actual_counts: Record<string, number>;
  actual_ratio: Record<string, number>;
}

export type BlogPlatformStatus = "active" | "inactive";

export interface BlogPlatform {
  id: number;
  name: string;
  url: string;
  status: BlogPlatformStatus;
  username: string | null;
  login_url: string | null;
  category_default: string | null;
  last_publish_date: string | null;
}

export type CampaignStatus = "planning" | "in_progress" | "completed" | "paused";

export interface Campaign {
  id: number;
  project_id: number;
  target_page_id: number;
  name: string;
  total_links_target: number;
  blog_count: number;
  duration_days: number;
  status: CampaignStatus;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export type TopicStatus = "suggested" | "selected" | "rejected";

export interface Topic {
  id: number;
  campaign_id: number;
  title: string;
  rationale: string | null;
  status: TopicStatus;
  generated_by: "ai" | "manual";
  created_at: string;
}

export type BriefStatus = "draft" | "approved";

export interface OutlineItem {
  heading: string;
  level: string;
  key_points: string[];
}

export interface ContentBrief {
  id: number;
  topic_id: number;
  target_page_id: number;
  content_template_id: number | null;
  outline: OutlineItem[];
  target_word_count: number;
  keywords_to_include: string[] | null;
  must_include_points: string[] | null;
  tone: string | null;
  status: BriefStatus;
}

export type ArticleStatus =
  | "draft"
  | "in_audit"
  | "reviewed"
  | "needs_human_review"
  | "approved"
  | "published"
  | "rejected";

export interface Article {
  id: number;
  campaign_id: number;
  target_page_id: number;
  anchor_id: number;
  topic_id: number | null;
  content_brief_id: number | null;
  blog_platform_id: number | null;
  title: string;
  content: string | null;
  word_count: number | null;
  seo_score: number | null;
  status: ArticleStatus;
  human_approved: boolean;
  human_approved_by: number | null;
  human_approved_at: string | null;
  published_url: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SeoAuditResult {
  id: number;
  article_id: number;
  check_name: string;
  passed: boolean;
  score: number | null;
  details: string | null;
}

export interface Publication {
  id: number;
  article_id: number;
  blog_platform_id: number;
  method: "manual" | "automated";
  status: "success" | "failed";
  published_url: string | null;
  notes: string | null;
  published_at: string;
}

export interface PublishPackage {
  article_id: number;
  suggested_blog_platform_id: number | null;
  suggested_blog_platform_name: string | null;
  title: string;
  content: string | null;
  anchor_text: string;
  target_url: string;
  category: string | null;
}

export interface Competitor {
  id: number;
  project_id: number;
  name: string;
  website_url: string;
  notes: string | null;
}

export interface CompetitorPage {
  id: number;
  competitor_id: number;
  target_page_id: number | null;
  url: string;
  fetched_title: string | null;
  fetched_headings: string[] | null;
  fetched_word_count: number | null;
  top_keywords: string[] | null;
  analyzed_at: string | null;
}

export type ContentGapStatus = "new" | "used_in_topic" | "ignored";

export interface ContentGap {
  id: number;
  target_page_id: number;
  gap_topic: string;
  gap_type: "topic" | "keyword" | "heading";
  status: ContentGapStatus;
}

export type InternalLinkStatus = "suggested" | "applied" | "dismissed";

export interface InternalLinkSuggestion {
  id: number;
  project_id: number;
  source_target_page_id: number;
  destination_target_page_id: number;
  suggested_anchor: string;
  reason: string | null;
  status: InternalLinkStatus;
}

export interface ContentTemplate {
  id: number;
  name: string;
  description: string | null;
  default_word_count: number;
  is_active: boolean;
}

export type PromptAgentType =
  | "keyword_intel"
  | "topic_gen"
  | "competitor_analysis"
  | "brief_generation"
  | "article_write"
  | "seo_audit"
  | "internal_link_suggestion";

export interface PromptTemplate {
  id: number;
  agent_type: PromptAgentType;
  name: string;
  template_text: string;
  version: number;
  is_active: boolean;
}

export type LinkPlacementScope = "global" | "project" | "campaign";

export interface ResolvedLinkPlacementRule {
  scope: LinkPlacementScope;
  scope_id: number | null;
  anchor_distribution: Record<string, number>;
  link_position_max_words: number;
  max_outbound_links: number;
  resolved_from: LinkPlacementScope;
  rule_id: number | null;
}

export type AiJobType =
  | "keyword_intel"
  | "topic_gen"
  | "article_write"
  | "seo_audit"
  | "publish"
  | "competitor_analysis"
  | "brief_generation"
  | "internal_link_suggestion"
  | "serp_fetch";

export type AiJobStatus = "pending" | "running" | "success" | "failed";

export interface AiJob {
  id: number;
  job_type: AiJobType;
  status: AiJobStatus;
  reference_table: string;
  reference_id: number;
  provider: "openai" | "claude" | null;
  prompt_template_id: number | null;
  prompt_template_version: number | null;
  tokens_used: number | null;
  cost_estimate: number | null;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

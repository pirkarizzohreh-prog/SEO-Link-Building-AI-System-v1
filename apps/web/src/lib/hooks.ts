"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import type {
  AiJob,
  Anchor,
  AnchorDistribution,
  Article,
  BlogPlatform,
  Campaign,
  Competitor,
  CompetitorPage,
  ContentBrief,
  ContentGap,
  ContentTemplate,
  InternalLinkSuggestion,
  Keyword,
  Project,
  ProjectKnowledgeBase,
  Publication,
  PublishPackage,
  ResolvedLinkPlacementRule,
  SeoAuditResult,
  TargetPage,
  Topic,
  User,
} from "@/lib/types";

// --- Projects ---

export function useProjects() {
  return useQuery({ queryKey: ["projects"], queryFn: () => api.get<Project[]>("/projects") });
}

export function useProject(id: number) {
  return useQuery({ queryKey: ["projects", id], queryFn: () => api.get<Project>(`/projects/${id}`) });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project>) => api.post<Project>("/projects", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useProjectKnowledgeBase(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "knowledge-base"],
    queryFn: async () => {
      try {
        return await api.get<ProjectKnowledgeBase>(`/projects/${projectId}/knowledge-base`);
      } catch {
        return null;
      }
    },
  });
}

export function useUpsertKnowledgeBase(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ProjectKnowledgeBase>) =>
      api.put<ProjectKnowledgeBase>(`/projects/${projectId}/knowledge-base`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "knowledge-base"] }),
  });
}

// --- Target Pages / Keywords ---

export function useTargetPages(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "target-pages"],
    queryFn: () => api.get<TargetPage[]>(`/projects/${projectId}/target-pages`),
  });
}

export function useTargetPage(id: number) {
  return useQuery({ queryKey: ["target-pages", id], queryFn: () => api.get<TargetPage>(`/target-pages/${id}`) });
}

export function useCreateTargetPage(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<TargetPage>) =>
      api.post<TargetPage>(`/projects/${projectId}/target-pages`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "target-pages"] }),
  });
}

export function useKeywords(targetPageId: number) {
  return useQuery({
    queryKey: ["target-pages", targetPageId, "keywords"],
    queryFn: () => api.get<Keyword[]>(`/target-pages/${targetPageId}/keywords`),
  });
}

export function useCreateKeyword(targetPageId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Keyword>) => api.post<Keyword>(`/target-pages/${targetPageId}/keywords`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["target-pages", targetPageId, "keywords"] }),
  });
}

// --- Anchors ---

export function useAnchors(targetPageId: number) {
  return useQuery({
    queryKey: ["target-pages", targetPageId, "anchors"],
    queryFn: () => api.get<Anchor[]>(`/target-pages/${targetPageId}/anchors`),
  });
}

export function useAnchorDistribution(targetPageId: number) {
  return useQuery({
    queryKey: ["target-pages", targetPageId, "anchors", "distribution"],
    queryFn: () => api.get<AnchorDistribution>(`/target-pages/${targetPageId}/anchors/distribution`),
  });
}

export function useCreateAnchor(targetPageId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Anchor>) => api.post<Anchor>(`/target-pages/${targetPageId}/anchors`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["target-pages", targetPageId, "anchors"] });
    },
  });
}

// --- Campaigns ---

export function useCampaigns(projectId?: number) {
  return useQuery({
    queryKey: ["campaigns", { projectId }],
    queryFn: () => api.get<Campaign[]>(`/campaigns${projectId ? `?project_id=${projectId}` : ""}`),
  });
}

export function useCampaign(id: number) {
  return useQuery({ queryKey: ["campaigns", id], queryFn: () => api.get<Campaign>(`/campaigns/${id}`) });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Campaign>) => api.post<Campaign>("/campaigns", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}

export function useResolvedLinkPlacementRule(campaignId: number) {
  return useQuery({
    queryKey: ["link-placement-rules", "resolve", campaignId],
    queryFn: () => api.get<ResolvedLinkPlacementRule>(`/link-placement-rules/resolve?campaign_id=${campaignId}`),
  });
}

export function useStartCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (campaignId: number) => api.post<AiJob>(`/campaigns/${campaignId}/start`),
    onSuccess: (_data, campaignId) => {
      qc.invalidateQueries({ queryKey: ["campaigns", campaignId] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function usePauseCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (campaignId: number) => api.post<Campaign>(`/campaigns/${campaignId}/pause`),
    onSuccess: (_data, campaignId) => qc.invalidateQueries({ queryKey: ["campaigns", campaignId] }),
  });
}

// --- Topics ---

export function useTopics(campaignId: number) {
  return useQuery({
    queryKey: ["campaigns", campaignId, "topics"],
    queryFn: () => api.get<Topic[]>(`/campaigns/${campaignId}/topics`),
  });
}

export function useCreateTopic(campaignId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; rationale?: string }) =>
      api.post<Topic>(`/campaigns/${campaignId}/topics`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns", campaignId, "topics"] }),
  });
}

export function useApproveTopic(campaignId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: number; note?: string }) =>
      api.post<Topic>(`/topics/${id}/approve`, { note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns", campaignId, "topics"] }),
  });
}

export function useRejectTopic(campaignId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: number; note?: string }) =>
      api.post<Topic>(`/topics/${id}/reject`, { note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns", campaignId, "topics"] }),
  });
}

// --- Content Briefs ---

export function useBrief(topicId: number, enabled: boolean, options: { poll?: boolean } = {}) {
  return useQuery({
    queryKey: ["topics", topicId, "brief"],
    queryFn: async () => {
      try {
        return await api.get<ContentBrief>(`/topics/${topicId}/brief`);
      } catch {
        return null;
      }
    },
    enabled,
    // Used right after triggering the Content Brief Generator agent job
    // (async — see docs/ARCHITECTURE.md) so the panel updates itself once
    // the worker finishes, instead of the user having to refresh.
    refetchInterval: (query) => (options.poll && !query.state.data ? 3000 : false),
  });
}

export function useCreateBrief(topicId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ContentBrief>) => api.post<ContentBrief>(`/topics/${topicId}/brief`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["topics", topicId, "brief"] }),
  });
}

export function useApproveBrief(topicId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (briefId: number) => api.post<ContentBrief>(`/content-briefs/${briefId}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["topics", topicId, "brief"] }),
  });
}

export function useGenerateBrief(topicId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<AiJob>(`/topics/${topicId}/generate-brief`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useGenerateArticle(campaignId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (briefId: number) => api.post<AiJob>(`/content-briefs/${briefId}/generate-article`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["campaigns", campaignId, "articles"] });
    },
  });
}

// --- Articles ---

export function useArticles(campaignId: number) {
  return useQuery({
    queryKey: ["campaigns", campaignId, "articles"],
    queryFn: () => api.get<Article[]>(`/campaigns/${campaignId}/articles`),
  });
}

export function useArticle(id: number) {
  return useQuery({ queryKey: ["articles", id], queryFn: () => api.get<Article>(`/articles/${id}`) });
}

export function useCreateArticle(campaignId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Article>) => api.post<Article>(`/campaigns/${campaignId}/articles`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns", campaignId, "articles"] }),
  });
}

export function useSeoAuditResults(articleId: number) {
  return useQuery({
    queryKey: ["articles", articleId, "seo-audit-results"],
    queryFn: () => api.get<SeoAuditResult[]>(`/articles/${articleId}/seo-audit-results`),
  });
}

export function usePublications(articleId: number) {
  return useQuery({
    queryKey: ["articles", articleId, "publications"],
    queryFn: () => api.get<Publication[]>(`/articles/${articleId}/publications`),
  });
}

export function usePublishPackage(articleId: number, enabled: boolean) {
  return useQuery({
    queryKey: ["articles", articleId, "publish-package"],
    queryFn: () => api.get<PublishPackage>(`/articles/${articleId}/publish-package`),
    enabled,
    retry: false,
  });
}

function invalidateArticle(qc: ReturnType<typeof useQueryClient>, articleId: number) {
  qc.invalidateQueries({ queryKey: ["articles", articleId] });
  qc.invalidateQueries({ queryKey: ["articles", articleId, "publish-package"] });
  qc.invalidateQueries({ queryKey: ["articles", articleId, "publications"] });
}

export function useApproveArticle(articleId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (note?: string) => api.post<Article>(`/articles/${articleId}/approve`, { note }),
    onSuccess: () => invalidateArticle(qc, articleId),
  });
}

export function useRejectArticle(articleId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (note?: string) => api.post<Article>(`/articles/${articleId}/reject`, { note }),
    onSuccess: () => invalidateArticle(qc, articleId),
  });
}

export function usePublishArticle(articleId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { blog_platform_id: number; published_url: string; notes?: string }) =>
      api.post<Article>(`/articles/${articleId}/publish`, data),
    onSuccess: () => invalidateArticle(qc, articleId),
  });
}

// --- Blog Platforms ---

export function useBlogPlatforms() {
  return useQuery({ queryKey: ["blog-platforms"], queryFn: () => api.get<BlogPlatform[]>("/blog-platforms") });
}

export function useCreateBlogPlatform() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<BlogPlatform>) => api.post<BlogPlatform>("/blog-platforms", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blog-platforms"] }),
  });
}

// --- Content Templates ---

export function useContentTemplates() {
  return useQuery({
    queryKey: ["content-templates"],
    queryFn: () => api.get<ContentTemplate[]>("/content-templates"),
  });
}

export function useCreateContentTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ContentTemplate>) => api.post<ContentTemplate>("/content-templates", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content-templates"] }),
  });
}

// --- Competitors / Content Gaps ---

export function useCompetitors(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "competitors"],
    queryFn: () => api.get<Competitor[]>(`/projects/${projectId}/competitors`),
  });
}

export function useCreateCompetitor(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Competitor>) => api.post<Competitor>(`/projects/${projectId}/competitors`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "competitors"] }),
  });
}

export function useContentGaps(targetPageId: number) {
  return useQuery({
    queryKey: ["target-pages", targetPageId, "content-gaps"],
    queryFn: () => api.get<ContentGap[]>(`/target-pages/${targetPageId}/content-gaps`),
  });
}

export function useCompetitorPages(competitorId: number) {
  return useQuery({
    queryKey: ["competitors", competitorId, "pages"],
    queryFn: () => api.get<CompetitorPage[]>(`/competitors/${competitorId}/pages`),
  });
}

export function useCreateCompetitorPage(competitorId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { url: string; target_page_id?: number }) =>
      api.post<CompetitorPage>(`/competitors/${competitorId}/pages`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors", competitorId, "pages"] }),
  });
}

export function useAnalyzeCompetitorPage(competitorId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (pageId: number) => api.post<AiJob>(`/competitor-pages/${pageId}/analyze`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", competitorId, "pages"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

// --- Internal Link Suggestions ---

export function useInternalLinkSuggestions(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "internal-link-suggestions"],
    queryFn: () => api.get<InternalLinkSuggestion[]>(`/projects/${projectId}/internal-link-suggestions`),
  });
}

export function useApplySuggestion(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post<InternalLinkSuggestion>(`/internal-link-suggestions/${id}/apply`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "internal-link-suggestions"] }),
  });
}

export function useDismissSuggestion(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post<InternalLinkSuggestion>(`/internal-link-suggestions/${id}/dismiss`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "internal-link-suggestions"] }),
  });
}

export function useAnalyzeInternalLinks(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<AiJob>(`/projects/${projectId}/analyze-internal-links`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects", projectId, "internal-link-suggestions"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

// --- Users (admin only) ---

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: () => api.get<User[]>("/users") });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; email: string; password: string; role: string }) =>
      api.post<User>("/users", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

// --- AI Jobs (read-only) ---

export function useAiJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.get<AiJob[]>("/jobs"),
    // Poll while anything is still pending/running so the Jobs page (and
    // any inline "in progress" indicator) reflects the worker's progress
    // without a manual refresh — jobs are async by design (docs/
    // ARCHITECTURE.md), so this is the UI's only way to know they're done.
    refetchInterval: (query) => {
      const jobs = query.state.data;
      const stillWorking = jobs?.some((j) => j.status === "pending" || j.status === "running");
      return stillWorking ? 3000 : false;
    },
  });
}

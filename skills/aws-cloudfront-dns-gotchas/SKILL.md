---
name: aws-cloudfront-dns-gotchas
description: AWS, CloudFront, ECS and client-DNS cutover gotchas: cert/alias scoping, registrar-held apex forwarding, Wix-held domains, ECS task-def rollout timing, gcloud/firebase deploy rollout polling, post-cutover stale-cache diagnosis. Load before any CloudFront, Route53, DNS cutover, ECS, or client domain work.
user_invocable: false
---

# AWS / CloudFront / Client DNS

Each item below cost a real debugging cycle on a shipped project. Load it before the work, then follow it.

- CloudFront alias attach requires ONE cert covering ALL the dist's aliases - when SANs don't line up, use a dedicated (or repurposed) distribution per cert scope instead of cert juggling; keep bucket-policy changes additive to protect live neighbors
- registrar-held apex (GoDaddy etc.) can't CNAME to CloudFront: use the registrar's 301 domain-forward to a subdomain; NEVER move nameservers on a client domain (their email MX rides the registrar)
- post-cutover "still shows the old site" (user report after a green DNS cutover): prove record correctness first (authoritative-NS query + the platform's own domain-config API), then demonstrate the stale path with a direct-IP+SNI probe of the OLD edge capturing its redirect - the user's block is upstream resolver TTL + browser 301 cache, neither clearable locally, so report the expiry instead of retrying blind; intermittent SSL EOFs during the propagation window are resolver-cache mix, retry per-request, not a deploy failure
- Wix-held client domains: Wix hosts only Wix-builder sites - external apps ride a subdomain CNAME; edit the EXISTING Wix DNS row in place (don't unassign the subdomain, it bypasses Wix's redirect config with less surface) and never touch apex/www (they stay on Wix)
- ECS config/env changes (CORS headers, task-def env): verify only after the new task-def revision is PRIMARY/steady - a poll mid-rollout hits the draining old revision and false-fails
- gcloud/firebase functions deploy: exit 0 != rolled out - the deploy log can end mid-update; poll `gcloud functions describe` state+updateTime, THEN probe the endpoint (a mid-rollout probe returns the OLD revision; same class as the ECS PRIMARY/steady rule)
- Several CloudFront distributions can share ONE S3 bucket at root (probe origins before assuming per-host isolation): to gate or swap content for a SUBSET of hostnames, upload to a new key prefix and flip that distribution's `OriginPath` (capture the full DistributionConfig+ETag first as the rollback artifact) - never overwrite root objects, which mutates every distribution on the bucket. The 403/404->/index.html SPA error responses resolve RELATIVE to OriginPath, so deep routes follow automatically

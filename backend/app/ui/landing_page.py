"""
TRUTHNET AI — Public Landing Page.
Streamlined, evidence-first design system for YUKTIK-2026 PS-11.
"""

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUTHNET AI — Multimodal Misinformation Intelligence Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #060913;
            --bg-surface: #0b1220;
            --bg-card: #0f172a;
            --bg-card-hover: #162038;
            --border: #1e293b;
            --border-light: #2d3b55;
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent: #0284c7;
            --accent-light: #38bdf8;
            --accent-bg: rgba(2, 132, 199, 0.1);
            --amber: #f59e0b;
            --amber-bg: rgba(245, 158, 11, 0.1);
            --red: #f43f5e;
            --green: #10b981;
            --purple: #8b5cf6;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            line-height: 1.5;
            overflow-x: hidden;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        /* Navigation */
        nav {
            position: sticky;
            top: 0;
            width: 100%;
            height: 64px;
            background: rgba(6, 9, 19, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 40px;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            font-size: 16px;
            letter-spacing: -0.2px;
        }

        .brand-icon {
            width: 28px;
            height: 28px;
            background: var(--accent);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon svg {
            width: 16px;
            height: 16px;
            fill: #ffffff;
        }

        .brand-badge {
            background: var(--accent-bg);
            color: var(--accent-light);
            border: 1px solid rgba(56, 189, 248, 0.25);
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            margin-left: 4px;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 28px;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .nav-links a:hover {
            color: var(--text-main);
        }

        .btn-launch, .btn-primary {
            background: var(--accent);
            color: #ffffff;
            font-weight: 600;
            font-size: 14px;
            padding: 9px 18px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: background 0.15s ease;
        }

        .btn-launch:hover, .btn-primary:hover {
            background: #0369a1;
        }

        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border-light);
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            padding: 9px 18px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.15s ease;
        }

        .btn-secondary:hover {
            border-color: var(--text-muted);
            color: var(--text-main);
        }

        /* Hero Section */
        .hero {
            max-width: 1200px;
            margin: 0 auto;
            padding: 72px 32px 56px;
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            align-items: center;
            gap: 48px;
        }

        .hero-left {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .eyebrow {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--accent-light);
            text-transform: uppercase;
        }

        .hero-title {
            font-size: 42px;
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: -0.8px;
            color: #ffffff;
        }

        .hero-title span {
            color: var(--accent-light);
        }

        .hero-desc {
            font-size: 16px;
            color: var(--text-secondary);
            line-height: 1.6;
            max-width: 520px;
        }

        .hero-actions {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-top: 4px;
        }

        .hero-capabilities-bar {
            font-size: 12px;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 16px;
            margin-top: 8px;
        }

        .hero-capabilities-bar b {
            color: var(--text-secondary);
        }

        /* Streamlined Forensic Preview Card */
        .hero-preview-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }

        .preview-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            background: var(--amber-bg);
            color: var(--amber);
            border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .preview-row {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .preview-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
        }

        .preview-val {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-main);
        }

        .preview-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-secondary);
        }

        .preview-verdict-box {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-left: 3px solid var(--amber);
            border-radius: 6px;
            padding: 12px 14px;
        }

        /* Capability Strip */
        .capability-strip {
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            background: var(--bg-surface);
            padding: 18px 32px;
        }

        .strip-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 24px;
            flex-wrap: wrap;
        }

        .strip-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .strip-item svg {
            width: 16px;
            height: 16px;
            fill: none;
            stroke: var(--accent-light);
            stroke-width: 2;
        }

        /* Standard Section Wrap */
        .section-wrap {
            max-width: 1200px;
            margin: 0 auto;
            padding: 72px 32px;
        }

        .section-header {
            margin-bottom: 36px;
        }

        .section-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--accent-light);
            text-transform: uppercase;
            display: block;
            margin-bottom: 8px;
        }

        .section-title {
            font-size: 28px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.4px;
            margin-bottom: 8px;
        }

        .section-desc {
            font-size: 15px;
            color: var(--text-secondary);
            max-width: 640px;
            line-height: 1.5;
        }

        /* Problem Grid */
        .problem-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .problem-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
        }

        .problem-num {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            display: block;
            margin-bottom: 12px;
        }

        .problem-title {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
        }

        .problem-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        /* Capabilities Grid */
        .capabilities-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .cap-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .cap-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .cap-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            color: var(--accent-light);
            background: var(--accent-bg);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .cap-title {
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
        }

        .cap-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .verdicts-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
        }

        .v-pill {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        /* Pipeline Flow */
        .pipeline-flow {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 14px;
        }

        .pipeline-step {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px 16px;
        }

        .step-index {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            color: var(--accent-light);
            display: block;
            margin-bottom: 8px;
        }

        .step-name {
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .step-desc {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        /* Epistemic Principles */
        .principles-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        .principle-box {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
            border-radius: 0 6px 6px 0;
            padding: 18px 20px;
        }

        .p-law {
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .p-rationale {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        /* Final CTA */
        .cta-banner {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 48px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }

        .cta-title {
            font-size: 28px;
            font-weight: 700;
            color: #ffffff;
        }

        .cta-desc {
            font-size: 15px;
            color: var(--text-secondary);
            max-width: 540px;
        }

        /* Footer */
        footer {
            border-top: 1px solid var(--border);
            background: var(--bg-base);
            padding: 40px 32px 28px;
        }

        .footer-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 40px;
            padding-bottom: 32px;
        }

        .footer-bottom {
            max-width: 1200px;
            margin: 0 auto;
            border-top: 1px solid var(--border);
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }

        @media (max-width: 900px) {
            .hero { grid-template-columns: 1fr; padding: 48px 20px; }
            .problem-grid, .capabilities-grid { grid-template-columns: 1fr; }
            .pipeline-flow { grid-template-columns: repeat(2, 1fr); }
            .principles-grid { grid-template-columns: 1fr; }
            nav { padding: 0 20px; }
            .nav-links { display: none; }
        }
    </style>
</head>
<body>

    <!-- Navigation -->
    <nav>
        <div class="brand">
            <div class="brand-icon">
                <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
            </div>
            <span>TRUTHNET AI</span>
            <span class="brand-badge">YUKTIK-2026</span>
        </div>
        <div class="nav-links">
            <a href="#capabilities">Capabilities</a>
            <a href="#problem">The Challenge</a>
            <a href="#workflow">Investigation Workflow</a>
            <a href="#principles">Epistemic Principles</a>
            <a href="/docs" target="_blank">API Docs</a>
        </div>
        <div>
            <a href="/workbench" class="btn-launch">
                <span>Launch Workbench</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero">
        <div class="hero-left">
            <div class="eyebrow">MULTIMODAL INVESTIGATIVE INTELLIGENCE</div>
            <h1 class="hero-title">
                When digital evidence is manipulated, <span>context becomes intelligence.</span>
            </h1>
            <p class="hero-desc">
                TRUTHNET AI connects media forensics, historical discovery, claim verification and source intelligence to help investigators evaluate evidence with clarity and rigor.
            </p>
            <div class="hero-actions">
                <a href="/workbench" class="btn-primary">
                    <span>Launch Workbench</span>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
                <a href="#capabilities" class="btn-secondary">
                    <span>Explore Capabilities</span>
                </a>
            </div>
            <div class="hero-capabilities-bar">
                <b>Core Architecture:</b> Media Forensics &middot; Claim Intelligence &middot; Historical Discovery &middot; Network Analysis
            </div>
        </div>

        <!-- Right Preview Card -->
        <div class="hero-preview-card">
            <div class="preview-header">
                <span class="preview-label">Live Investigation Preview</span>
                <span class="preview-badge">MISLEADING CONTEXT</span>
            </div>

            <div class="preview-row">
                <span class="preview-label">Suspect Viral Asset</span>
                <span class="preview-val">Flood Disaster Video Claim</span>
                <span class="preview-meta">FINGERPRINT: SHA-256 f1d2d2f9... &middot; pHash: 6</span>
            </div>

            <div class="preview-row">
                <span class="preview-label">EXIF TIMECODE</span>
                <span class="preview-val">2020-10-14 17:42:09 UTC</span>
                <span class="preview-meta">Camera timestamp reveals 6-year temporal discrepancy</span>
            </div>

            <div class="preview-row">
                <span class="preview-label">ORB GEOMETRY</span>
                <span class="preview-val">142 Inliers (Ratio 0.88)</span>
                <span class="preview-meta">Matches 2020 archival record with exact homography</span>
            </div>

            <div class="preview-row">
                <span class="preview-label">SOURCE INDEPENDENCE</span>
                <span class="preview-val">PTI Byline Syndication</span>
                <span class="preview-meta">Single syndicated wire copy repeated across 4 outlets</span>
            </div>

            <div class="preview-verdict-box">
                <div class="preview-label" style="color: var(--amber);">CONTEXTUAL VERDICT</div>
                <div style="font-weight: 600; font-size: 14px; color: #ffffff; margin-top: 2px;">Misleading Context</div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Authentic 2020 archival media recirculated with false contemporary breaking caption.</div>
            </div>
        </div>
    </section>

    <!-- CAPABILITY STRIP -->
    <div class="capability-strip">
        <div class="strip-inner">
            <div class="strip-item">
                <svg viewBox="0 0 24 24"><path d="M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                <span>Image & Video Forensics</span>
            </div>
            <div class="strip-item">
                <svg viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
                <span>Historical Media Discovery</span>
            </div>
            <div class="strip-item">
                <svg viewBox="0 0 24 24"><path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                <span>Claim Verification</span>
            </div>
            <div class="strip-item">
                <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6"/></svg>
                <span>Source Intelligence</span>
            </div>
            <div class="strip-item">
                <svg viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                <span>Coordination Analysis</span>
            </div>
        </div>
    </div>

    <!-- THE PROBLEM -->
    <section class="section-wrap" id="problem">
        <div class="section-header">
            <span class="section-tag">THE PROBLEM</span>
            <h2 class="section-title">Misinformation is deeper than synthetic pixels.</h2>
            <p class="section-desc">
                Digital deception extends beyond generative deepfakes. Authentic media is weaponized out-of-context and amplified through syndicated networks.
            </p>
        </div>

        <div class="problem-grid">
            <div class="problem-card">
                <span class="problem-num">01 / FORGERY</span>
                <h3 class="problem-title">Manipulated Media</h3>
                <p class="problem-desc">
                    Media altered or synthetically generated. Without EXIF analysis, keyframe demuxing, and perceptual hashing, fabricated visual assets pass basic filters.
                </p>
            </div>

            <div class="problem-card">
                <span class="problem-num">02 / DISPLACEMENT</span>
                <h3 class="problem-title">Misleading Context</h3>
                <p class="problem-desc">
                    Authentic archival media recirculated with false dates or locations. A genuine photograph presented as "breaking news" requires historical discovery.
                </p>
            </div>

            <div class="problem-card">
                <span class="problem-num">03 / AMPLIFICATION</span>
                <h3 class="problem-title">Coordinated Narratives</h3>
                <p class="problem-desc">
                    Identical claims spreading synchronously. Multiple URLs repeating the same wire dispatch represent a single source dependency, not independent confirmation.
                </p>
            </div>
        </div>
    </section>

    <!-- CAPABILITIES SHOWCASE -->
    <section class="section-wrap" id="capabilities">
        <div class="section-header">
            <span class="section-tag">CAPABILITIES SHOWCASE</span>
            <h2 class="section-title">An intelligence workbench built for rigorous verification.</h2>
            <p class="section-desc">
                TRUTHNET AI integrates forensics, deterministic contextual reasoning, live retrieval, and graph lineage into one unified platform.
            </p>
        </div>

        <div class="capabilities-grid">
            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Multimodal Media Forensics</h3>
                    <span class="cap-badge">FORENSICS</span>
                </div>
                <p class="cap-desc">
                    Extracts camera EXIF parameters, demuxes video keyframes, performs OCR text recognition, and transcribes speech while isolating corrupt inputs.
                </p>
            </div>

            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Historical Media Discovery</h3>
                    <span class="cap-badge">SIGNATURE</span>
                </div>
                <p class="cap-desc">
                    Matches media against historical archives using two-tier indexing: perceptual hash filtering followed by OpenCV ORB keypoints and RANSAC verification.
                </p>
            </div>

            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Claim Intelligence & Polarity</h3>
                    <span class="cap-badge">SEMANTICS</span>
                </div>
                <p class="cap-desc">
                    Normalizes claims into structured propositions, evaluates polarity and negation, and maps claims to six deterministic assessment verdicts:
                </p>
                <div class="verdicts-pill-row">
                    <span class="v-pill">SUPPORTED</span>
                    <span class="v-pill">CONTRADICTED</span>
                    <span class="v-pill">MISLEADING_OR_CONTEXT_MISSING</span>
                    <span class="v-pill">UNVERIFIED</span>
                    <span class="v-pill">INSUFFICIENT_EVIDENCE</span>
                    <span class="v-pill">CONFLICTING_EVIDENCE</span>
                </div>
            </div>

            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Real-Time Evidence Retrieval</h3>
                    <span class="cap-badge">RETRIEVAL</span>
                </div>
                <p class="cap-desc">
                    Queries public sources with SSRF guards and extracts structured ClaimReview LD-JSON fact-check records with graceful provider fallback.
                </p>
            </div>

            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Source Independence Intelligence</h3>
                    <span class="cap-badge">ATTRIBUTION</span>
                </div>
                <p class="cap-desc">
                    Prevents circular confirmation by detecting syndicated wire dispatches (PTI, ANI, Reuters) and clustering shared press release echoes.
                </p>
            </div>

            <div class="cap-card">
                <div class="cap-header">
                    <h3 class="cap-title">Claim Lineage & Graph Analytics</h3>
                    <span class="cap-badge">LINEAGE</span>
                </div>
                <p class="cap-desc">
                    Constructs an interactive directed graph connecting submissions, media assets, claims, and assessments with a 4-state edge taxonomy.
                </p>
            </div>
        </div>
    </section>

    <!-- INVESTIGATION PIPELINE -->
    <section class="section-wrap" id="workflow">
        <div class="section-header">
            <span class="section-tag">INVESTIGATION PIPELINE</span>
            <h2 class="section-title">From unverified signal to intelligence dossier.</h2>
            <p class="section-desc">
                A deterministic, verifiable progression that grounds every claim in observable forensic evidence.
            </p>
        </div>

        <div class="pipeline-flow">
            <div class="pipeline-step">
                <span class="step-index">01</span>
                <h4 class="step-name">SUBMIT</h4>
                <p class="step-desc">Ingest images, videos, audio, or text claims.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">02</span>
                <h4 class="step-name">EXTRACT</h4>
                <p class="step-desc">Derive EXIF, OCR text, and normalized claims.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">03</span>
                <h4 class="step-name">DISCOVER</h4>
                <p class="step-desc">Match pHash and ORB against archival repos.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">04</span>
                <h4 class="step-name">VERIFY</h4>
                <p class="step-desc">Retrieve external sources and evaluate independence.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">05</span>
                <h4 class="step-name">CONNECT</h4>
                <p class="step-desc">Generate directed Claim Lineage relationship graph.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">06</span>
                <h4 class="step-name">REVIEW</h4>
                <p class="step-desc">Investigator confirms findings and prints dossier.</p>
            </div>
        </div>
    </section>

    <!-- EPISTEMIC PRINCIPLES -->
    <section class="section-wrap" id="principles">
        <div class="section-header">
            <span class="section-tag">CORE METHODOLOGY</span>
            <h2 class="section-title">The Four Epistemic Principles</h2>
            <p class="section-desc">
                TRUTHNET AI enforces rigorous boundaries between observable evidence and analytical inference.
            </p>
        </div>

        <div class="principles-grid">
            <div class="principle-box">
                <h4 class="p-law">Media authenticity does not establish claim truth.</h4>
                <p class="p-rationale">An authentic photograph can be recirculated with a false date or caption. Visual authenticity alone never proves a narrative.</p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">Historical reuse does not automatically prove misinformation.</h4>
                <p class="p-rationale">Legitimate news frequently uses archival file photos. Historical discovery provides context, not an automated verdict.</p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">Similar reporting does not equal independent corroboration.</h4>
                <p class="p-rationale">Multiple news outlets publishing identical syndicated wire copy represent a single source dependency, not independent validation.</p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">Insufficient evidence is never proof of falsehood.</h4>
                <p class="p-rationale">When external evidence is inconclusive, the system explicitly marks the claim unverified rather than guessing.</p>
            </div>
        </div>
    </section>

    <!-- FINAL CTA -->
    <section class="section-wrap">
        <div class="cta-banner">
            <h2 class="cta-title">Investigate beyond the surface.</h2>
            <p class="cta-desc">
                Connect media, claims, sources and historical context in one evidence-led workbench.
            </p>
            <a href="/workbench" class="btn-primary" style="padding: 12px 28px;">
                <span>Open TRUTHNET Workbench</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
        </div>
    </section>

    <!-- FOOTER -->
    <footer>
        <div class="footer-inner">
            <div>
                <div class="brand" style="margin-bottom: 6px;">
                    <div class="brand-icon" style="width: 22px; height: 22px;">
                        <svg viewBox="0 0 24 24" style="width: 12px; height: 12px;"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                    </div>
                    <span>TRUTHNET AI</span>
                </div>
                <p style="max-width: 400px; font-size: 13px; color: var(--text-muted);">
                    Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform. Built for YUKTIK-2026 Problem Statement PS-11.
                </p>
            </div>

            <div style="display: flex; gap: 40px; font-size: 13px;">
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <b style="color: var(--text-main); font-size: 12px; text-transform: uppercase;">Product</b>
                    <a href="/workbench" style="color: var(--text-secondary);">Workbench</a>
                    <a href="/docs" target="_blank" style="color: var(--text-secondary);">API Documentation</a>
                    <a href="#capabilities" style="color: var(--text-secondary);">Capabilities</a>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <b style="color: var(--text-main); font-size: 12px; text-transform: uppercase;">Platform</b>
                    <a href="#workflow" style="color: var(--text-secondary);">Pipeline</a>
                    <a href="#principles" style="color: var(--text-secondary);">Epistemics</a>
                    <a href="/health" style="color: var(--text-secondary);">System Health</a>
                </div>
            </div>
        </div>

        <div class="footer-bottom">
            <span>&copy; 2026 TRUTHNET AI &middot; Evidence-Led Intelligence</span>
            <span>YUKTIK-2026 &middot; PS-11</span>
        </div>
    </footer>
</body>
</html>
"""

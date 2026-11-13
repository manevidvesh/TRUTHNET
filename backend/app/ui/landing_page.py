"""
TRUTHNET AI — Editorial Intelligence Landing Page.
Centered Ingestion Experience with Warm Off-White / Light Stone Aesthetic.
"""

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUTHNET AI — Multimodal Misinformation Intelligence Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #f8f9fa;
            --bg-surface: #ffffff;
            --bg-subtle: #f1f3f5;
            --bg-hover: #e9ecef;
            --border: #e2e8f0;
            --border-strong: #cbd5e1;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --accent: #0f766e;
            --accent-hover: #115e59;
            --accent-subtle: #f0fdfa;
            --accent-border: #99f6e4;
            --amber: #b45309;
            --amber-subtle: #fffbeb;
            --amber-border: #fde68a;
            --red: #b91c1c;
            --red-subtle: #fef2f2;
            --red-border: #fecaca;
            --green: #15803d;
            --green-subtle: #f0fdf4;
            --green-border: #bbf7d0;
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
            color: var(--text-primary);
            line-height: 1.55;
            overflow-x: hidden;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        /* Top Navigation */
        nav {
            position: sticky;
            top: 0;
            width: 100%;
            height: 60px;
            background: rgba(248, 249, 250, 0.95);
            backdrop-filter: blur(8px);
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
            font-size: 15px;
            letter-spacing: -0.2px;
            color: var(--text-primary);
        }

        .brand-icon {
            width: 26px;
            height: 26px;
            background: var(--accent);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon svg {
            width: 14px;
            height: 14px;
            fill: #ffffff;
        }

        .brand-badge {
            background: var(--bg-subtle);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
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
            color: var(--text-primary);
        }

        .btn-launch, .btn-primary {
            background: var(--accent);
            color: #ffffff;
            font-weight: 600;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            transition: background 0.15s ease;
            border: none;
            cursor: pointer;
        }

        .btn-launch:hover, .btn-primary:hover {
            background: var(--accent-hover);
        }

        .btn-secondary {
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            color: var(--text-primary);
            font-weight: 500;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            transition: all 0.15s ease;
            cursor: pointer;
        }

        .btn-secondary:hover {
            background: var(--bg-hover);
        }

        /* Centerpiece Hero Viewport */
        .hero-centerpiece {
            max-width: 860px;
            margin: 0 auto;
            padding: 56px 24px 64px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .eyebrow {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--accent);
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .hero-title {
            font-family: 'Newsreader', Georgia, serif;
            font-size: 46px;
            font-weight: 500;
            line-height: 1.15;
            letter-spacing: -0.8px;
            color: var(--text-primary);
            margin-bottom: 12px;
        }

        .hero-title span {
            font-style: italic;
            color: var(--accent);
        }

        .hero-desc {
            font-size: 16px;
            color: var(--text-secondary);
            line-height: 1.5;
            max-width: 620px;
            margin-bottom: 32px;
        }

        .quote-subtext {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 24px;
        }

        /* The Centered Upload Console */
        .intake-console {
            width: 100%;
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
            text-align: left;
            overflow: hidden;
        }

        .intake-tabs {
            display: flex;
            background: var(--bg-subtle);
            border-bottom: 1px solid var(--border);
            padding: 4px 8px 0;
            gap: 4px;
        }

        .intake-tab-btn {
            background: transparent;
            border: none;
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            display: inline-flex;
            align-items: center;
            gap: 7px;
        }

        .intake-tab-btn.active {
            background: var(--bg-surface);
            color: var(--text-primary);
            border-bottom: 2px solid var(--accent);
            border-radius: 6px 6px 0 0;
        }

        .intake-body {
            padding: 24px;
        }

        .dropzone-box {
            border: 2px dashed var(--border-strong);
            border-radius: 8px;
            background: var(--bg-base);
            padding: 32px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .dropzone-box:hover, .dropzone-box.drag-over {
            border-color: var(--accent);
            background: var(--accent-subtle);
        }

        .dropzone-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 8px;
        }

        .dropzone-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .selected-file-chip {
            background: var(--bg-subtle);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--text-primary);
        }

        .chip-remove {
            color: var(--red);
            font-weight: bold;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 14px;
        }

        .form-input, .form-textarea {
            width: 100%;
            background: var(--bg-base);
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            padding: 10px 12px;
            font-size: 14px;
            color: var(--text-primary);
            outline: none;
            transition: border-color 0.15s ease;
        }

        .form-input:focus, .form-textarea:focus {
            border-color: var(--accent);
            background: #ffffff;
        }

        .intake-footer {
            padding: 16px 24px;
            background: var(--bg-subtle);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .intake-status-text {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* History & Recent Analyses Drawer/Bar */
        .history-strip {
            max-width: 860px;
            width: 100%;
            margin-top: 20px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .history-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Trust & Capability Bar */
        .capability-strip {
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            background: var(--bg-surface);
            padding: 16px 32px;
        }

        .strip-inner {
            max-width: 1100px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .strip-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .strip-item svg {
            width: 16px;
            height: 16px;
            stroke: var(--accent);
            fill: none;
            stroke-width: 2;
        }

        /* Section Layout */
        .section-wrap {
            max-width: 1100px;
            margin: 0 auto;
            padding: 64px 32px;
        }

        .section-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--accent);
            text-transform: uppercase;
            display: block;
            margin-bottom: 8px;
        }

        .section-title {
            font-family: 'Newsreader', Georgia, serif;
            font-size: 32px;
            font-weight: 500;
            color: var(--text-primary);
            letter-spacing: -0.4px;
            margin-bottom: 8px;
        }

        .section-desc {
            font-size: 15px;
            color: var(--text-secondary);
            max-width: 600px;
            line-height: 1.5;
            margin-bottom: 32px;
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
            margin-bottom: 10px;
        }

        .problem-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
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
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 10px;
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
            color: var(--accent);
            background: var(--accent-subtle);
            border: 1px solid var(--accent-border);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .cap-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
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
            background: var(--bg-subtle);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        /* Pipeline Flow */
        .pipeline-flow {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 12px;
        }

        .pipeline-step {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 14px;
        }

        .step-index {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            color: var(--accent);
            display: block;
            margin-bottom: 6px;
        }

        .step-name {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
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
            color: var(--text-primary);
            margin-bottom: 6px;
        }

        .p-rationale {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        /* Footer */
        footer {
            border-top: 1px solid var(--border);
            background: var(--bg-surface);
            padding: 40px 32px 28px;
        }

        .footer-inner {
            max-width: 1100px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 40px;
            padding-bottom: 28px;
        }

        .footer-bottom {
            max-width: 1100px;
            margin: 0 auto;
            border-top: 1px solid var(--border);
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }

        @media (max-width: 800px) {
            .problem-grid, .capabilities-grid { grid-template-columns: 1fr; }
            .pipeline-flow { grid-template-columns: repeat(2, 1fr); }
            .principles-grid { grid-template-columns: 1fr; }
            nav { padding: 0 16px; }
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
            <a href="#intake">Analyse</a>
            <a href="#capabilities">Capabilities</a>
            <a href="#problem">The Challenge</a>
            <a href="#workflow">Investigation Workflow</a>
            <a href="#principles">Epistemic Principles</a>
            <a href="/docs" target="_blank">API Docs</a>
        </div>
        <div style="display: flex; gap: 10px;">
            <a href="/workbench" class="btn-secondary" style="font-size: 12px; padding: 6px 12px;">
                <span>History</span>
            </a>
            <a href="/workbench" class="btn-launch">
                <span>Launch Workbench</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
        </div>
    </nav>

    <!-- CENTERPIECE HERO & UPLOAD -->
    <section class="hero-centerpiece" id="intake">
        <div class="eyebrow">MULTIMODAL INVESTIGATIVE INTELLIGENCE</div>
        <h1 class="hero-title">
            Investigate what you see. <span>Discover what is hidden.</span>
        </h1>
        <p class="hero-desc">
            TRUTHNET investigates suspicious images, videos, audio, claims and URLs by connecting media forensics, historical discovery, claim verification, and source intelligence.
        </p>
        <div class="quote-subtext">
            When digital evidence is manipulated, <b>context becomes intelligence.</b>
        </div>

        <!-- Central Unified Ingestion Component -->
        <div class="intake-console">
            <div class="intake-tabs">
                <button type="button" class="intake-tab-btn active" id="tab-btn-files" onclick="switchIntakeMode('files')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                    Media Files
                </button>
                <button type="button" class="intake-tab-btn" id="tab-btn-text" onclick="switchIntakeMode('text')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line></svg>
                    Text Claim
                </button>
                <button type="button" class="intake-tab-btn" id="tab-btn-url" onclick="switchIntakeMode('url')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                    Source URL
                </button>
            </div>

            <form id="landing-intake-form" onsubmit="handleLandingIntake(event)">
                <div class="intake-body">
                    <!-- Pane 1: Files -->
                    <div id="pane-files">
                        <div class="dropzone-box" id="landing-dropzone" onclick="document.getElementById('landing-files-input').click()">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.8">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="17 8 12 3 7 8"></polyline>
                                <line x1="12" y1="3" x2="12" y2="15"></line>
                            </svg>
                            <div class="dropzone-title">Drop images, video or audio here, or browse files</div>
                            <div class="dropzone-sub">Supports PNG, JPEG, WebP, MP4, WebM, WAV, MP3 &middot; Multiple files supported</div>
                            <input type="file" id="landing-files-input" multiple style="display: none;" onchange="onLandingFilesSelected(this.files)">
                        </div>
                        <div id="landing-selected-files" style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;"></div>
                        
                        <div style="margin-top: 14px;">
                            <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Accompanying claim / post caption (optional)</label>
                            <textarea id="landing-caption" class="form-textarea" rows="2" placeholder="e.g. Breaking footage claiming flash flood damage in Hyderabad today"></textarea>
                        </div>
                    </div>

                    <!-- Pane 2: Text Claim -->
                    <div id="pane-text" style="display: none;">
                        <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Suspicious statement or viral proposition</label>
                        <textarea id="landing-text-claim" class="form-textarea" rows="4" placeholder="Paste the claim text, message, or transcript to evaluate..."></textarea>
                    </div>

                    <!-- Pane 3: Source URL -->
                    <div id="pane-url" style="display: none;">
                        <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Article, post or fact-check link</label>
                        <input type="url" id="landing-url-input" class="form-input" placeholder="https://news.example.com/breaking-report">
                    </div>
                </div>

                <div class="intake-footer">
                    <span class="intake-status-text" id="landing-status-msg">Upload media or enter a claim to begin real-time analysis</span>
                    <button type="submit" id="landing-submit-btn" class="btn-primary" style="padding: 10px 22px; font-size: 14px;">
                        <span>Analyse Content</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </button>
                </div>
            </form>
        </div>

        <!-- History Link -->
        <div class="history-strip">
            <div class="history-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>Recent Investigations & History</span>
            </div>
            <a href="/workbench" class="btn-secondary" style="font-size: 12px; padding: 5px 12px;">
                Open History &rarr;
            </a>
        </div>
    </section>

    <!-- TRUST STRIP -->
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
        <span class="section-tag">THE PROBLEM</span>
        <h2 class="section-title">Misinformation is deeper than synthetic pixels.</h2>
        <p class="section-desc">
            Digital deception extends beyond generative deepfakes. Authentic media is weaponized out-of-context and amplified through syndicated networks.
        </p>

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
        <span class="section-tag">CAPABILITIES SHOWCASE</span>
        <h2 class="section-title">An intelligence workbench built for rigorous verification.</h2>
        <p class="section-desc">
            TRUTHNET AI integrates forensics, deterministic contextual reasoning, live retrieval, and graph lineage into one unified platform.
        </p>

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

        <div style="margin-top: 24px; text-align: center;">
            <a href="#intake" class="btn-primary">
                <span>Start New Analysis</span>
            </a>
            <a href="#capabilities" class="btn-secondary" style="margin-left: 10px;">
                <span>Explore Capabilities</span>
            </a>
        </div>
    </section>

    <!-- INVESTIGATION PIPELINE -->
    <section class="section-wrap" id="workflow">
        <span class="section-tag">INVESTIGATION PIPELINE</span>
        <h2 class="section-title">From unverified signal to intelligence dossier.</h2>
        <p class="section-desc">
            A deterministic, verifiable progression that grounds every claim in observable forensic evidence.
        </p>

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
        <span class="section-tag">CORE METHODOLOGY</span>
        <h2 class="section-title">The Four Epistemic Principles</h2>
        <p class="section-desc">
            TRUTHNET AI enforces rigorous boundaries between observable evidence and analytical inference.
        </p>

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
                    <b style="color: var(--text-primary); font-size: 12px; text-transform: uppercase;">Product</b>
                    <a href="/workbench" style="color: var(--text-secondary);">Workbench</a>
                    <a href="/docs" target="_blank" style="color: var(--text-secondary);">API Documentation</a>
                    <a href="#capabilities" style="color: var(--text-secondary);">Capabilities</a>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <b style="color: var(--text-primary); font-size: 12px; text-transform: uppercase;">Platform</b>
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

    <!-- INTAKE INTERACTION SCRIPT -->
    <script>
        let landingSelectedFiles = [];
        let currentIntakeMode = 'files';

        function switchIntakeMode(mode) {
            currentIntakeMode = mode;
            document.querySelectorAll('.intake-tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`tab-btn-${mode}`).classList.add('active');

            document.getElementById('pane-files').style.display = mode === 'files' ? 'block' : 'none';
            document.getElementById('pane-text').style.display = mode === 'text' ? 'block' : 'none';
            document.getElementById('pane-url').style.display = mode === 'url' ? 'block' : 'none';
        }

        function onLandingFilesSelected(fileList) {
            for (const f of fileList) {
                landingSelectedFiles.push(f);
            }
            renderLandingSelectedFiles();
        }

        function removeLandingFile(idx) {
            landingSelectedFiles.splice(idx, 1);
            renderLandingSelectedFiles();
        }

        function renderLandingSelectedFiles() {
            const container = document.getElementById('landing-selected-files');
            container.innerHTML = landingSelectedFiles.map((f, idx) => `
                <span class="selected-file-chip">
                    ${f.name} (${(f.size / 1024).toFixed(0)} KB)
                    <button type="button" class="chip-remove" onclick="removeLandingFile(${idx})">&times;</button>
                </span>
            `).join('');
        }

        // Setup Drag & Drop
        const dropZone = document.getElementById('landing-dropzone');
        if (dropZone) {
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.add('drag-over');
                }, false);
            });
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.remove('drag-over');
                }, false);
            });
            dropZone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                if (dt.files && dt.files.length > 0) {
                    onLandingFilesSelected(dt.files);
                }
            }, false);
        }

        async function handleLandingIntake(e) {
            e.preventDefault();
            const statusMsg = document.getElementById('landing-status-msg');
            const submitBtn = document.getElementById('landing-submit-btn');

            let rawText = "";
            let sourceUrl = "";
            let caption = "";

            if (currentIntakeMode === 'files') {
                caption = document.getElementById('landing-caption').value.trim();
                if (landingSelectedFiles.length === 0 && !caption) {
                    statusMsg.innerText = "Please select at least one media file or enter a caption.";
                    statusMsg.style.color = "var(--red)";
                    return;
                }
            } else if (currentIntakeMode === 'text') {
                rawText = document.getElementById('landing-text-claim').value.trim();
                if (!rawText) {
                    statusMsg.innerText = "Please enter the claim text to evaluate.";
                    statusMsg.style.color = "var(--red)";
                    return;
                }
            } else if (currentIntakeMode === 'url') {
                sourceUrl = document.getElementById('landing-url-input').value.trim();
                if (!sourceUrl) {
                    statusMsg.innerText = "Please provide an article or fact-check link.";
                    statusMsg.style.color = "var(--red)";
                    return;
                }
            }

            submitBtn.disabled = true;
            submitBtn.innerText = "Initiating Analysis...";
            statusMsg.innerText = "Creating investigation session and dispatching evidence...";
            statusMsg.style.color = "var(--text-secondary)";

            try {
                // 1. Automatically create an investigation record
                const invTitle = landingSelectedFiles.length > 0 
                    ? `Analysis: ${landingSelectedFiles[0].name}` 
                    : rawText 
                        ? `Analysis: ${rawText.slice(0, 40)}...`
                        : `Analysis: ${sourceUrl}`;

                const createRes = await fetch("/api/v1/investigations/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: invTitle,
                        description: "Initiated directly from central intake console.",
                        priority: "HIGH"
                    })
                });

                if (!createRes.ok) {
                    throw new Error("Failed to initialize investigation session.");
                }

                const inv = await createRes.json();
                const invId = inv.id;

                // 2. Dispatch intake
                const formData = new FormData();
                for (const f of landingSelectedFiles) {
                    formData.append("files", f);
                }
                if (rawText) formData.append("raw_text", rawText);
                if (sourceUrl) formData.append("source_url", sourceUrl);
                if (caption) formData.append("caption", caption);

                const intakeRes = await fetch(`/api/v1/investigations/${encodeURIComponent(invId)}/evidence/intake`, {
                    method: "POST",
                    body: formData
                });

                if (!intakeRes.ok) {
                    throw new Error("Failed to dispatch evidence items.");
                }

                statusMsg.innerText = "Analysis dispatched. Forwarding to workbench...";
                statusMsg.style.color = "var(--green)";

                // 3. Forward seamlessly to the Workbench
                window.location.href = `/workbench?investigation_id=${encodeURIComponent(invId)}`;

            } catch (err) {
                console.error("Intake failure:", err);
                statusMsg.innerText = "Intake error: " + err.message;
                statusMsg.style.color = "var(--red)";
                submitBtn.disabled = false;
                submitBtn.innerText = "Analyse Content";
            }
        }
    </script>
</body>
</html>
"""

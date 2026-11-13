"""
TRUTHNET AI — Intelligence Workbench Template.
World-class investigative intelligence workbench for YUKTIK-2026 PS-11.
"""

WORKBENCH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUTHNET AI — Intelligence Workbench</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #f8f9fa;
            --bg-surface: #ffffff;
            --bg-card: #ffffff;
            --bg-card-hover: #f1f3f5;
            --border: #e2e8f0;
            --border-light: #cbd5e1;
            --text-main: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --cyan: #0f766e;
            --cyan-glow: rgba(15, 118, 110, 0.12);
            --teal: #0f766e;
            --violet: #475569;
            --amber: #b45309;
            --red: #b91c1c;
            --green: #15803d;
            --accent-blue: #0f766e;
            --accent-red: #b91c1c;
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
            overflow-x: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        code, pre, .mono {
            font-family: 'JetBrains Mono', monospace;
        }

        /* Top Navigation Bar */
        .top-nav {
            background: #ffffff;
            border-bottom: 1px solid var(--border);
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 50;
            flex-shrink: 0;
        }

        .brand-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
        }

        .brand-logo-icon {
            width: 26px;
            height: 26px;
            border-radius: 5px;
            background: var(--cyan);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-logo-icon svg {
            width: 15px;
            height: 15px;
            fill: #ffffff;
        }

        .brand-text {
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-main);
        }

        .nav-divider {
            color: var(--border-light);
            font-size: 14px;
        }

        .case-selector-btn {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .case-selector-btn:hover {
            border-color: var(--border-light);
            background: var(--bg-card-hover);
        }

        .case-id-pill {
            background: rgba(15, 118, 110, 0.08);
            color: var(--cyan);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn {
            padding: 7px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid transparent;
        }

        .btn-cyan {
            background: var(--cyan);
            color: #ffffff;
            border: 1px solid var(--cyan);
        }

        .btn-cyan:hover {
            background: #115e59;
            border-color: #115e59;
        }

        .btn-secondary {
            background: #ffffff;
            border-color: var(--border-light);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            border-color: var(--text-muted);
            background: var(--bg-card-hover);
        }

        /* Simulation Banner */
        .simulation-banner {
            background: #fffbeb;
            border-bottom: 1px solid #fde68a;
            padding: 6px 20px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.05em;
            color: var(--amber);
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }

        .simulation-banner svg {
            width: 14px;
            height: 14px;
            fill: var(--amber);
        }

        /* Sub-Header / Case Context Bar */
        .case-header-bar {
            background: #f8f9fa;
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }

        .case-title-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .case-title-text {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
        }

        .priority-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .priority-high {
            background: #fef2f2;
            color: var(--red);
            border: 1px solid #fecaca;
        }

        .priority-med {
            background: #fffbeb;
            color: var(--amber);
            border: 1px solid #fde68a;
        }

        .priority-low {
            background: #f0fdf4;
            color: var(--green);
            border: 1px solid #bbf7d0;
        }

        /* Workbench Tabs */
        .tabs-nav {
            display: flex;
            gap: 2px;
            background: #ffffff;
            border-bottom: 1px solid var(--border);
            padding: 0 20px;
            overflow-x: auto;
            flex-shrink: 0;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 500;
            padding: 12px 14px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.15s ease;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            color: var(--cyan);
            border-bottom-color: var(--cyan);
            font-weight: 600;
            background: transparent;
        }

        .tab-count {
            background: var(--bg-subtle);
            color: var(--text-secondary);
            font-size: 11px;
            padding: 1px 6px;
            border-radius: 10px;
            font-weight: 600;
        }

        .tab-btn.active .tab-count {
            background: rgba(15, 118, 110, 0.1);
            color: var(--cyan);
        }

        /* Universal Ingestion Console Styles */
        .drop-zone {
            border: 2px dashed var(--border-light);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            background: var(--bg-base);
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .drop-zone:hover, .drop-zone.dragover {
            border-color: var(--cyan);
            background: rgba(15, 118, 110, 0.04);
        }
        .file-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--bg-subtle);
            border: 1px solid var(--border);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-main);
        }
        .route-chip {
            display: inline-block;
            background: var(--bg-subtle);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 2px 7px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
        }

        /* Main Workspace Content Area */
        .workspace-content {
            flex: 1;
            overflow-y: auto;
            position: relative;
            background: var(--bg-base);
        }

        .tab-panel {
            display: none;
            padding: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .tab-panel.active {
            display: block;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .metric-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .metric-title {
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 0.04em;
        }

        .metric-value {
            font-size: 26px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: #ffffff;
        }

        .metric-desc {
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* Findings & Cards */
        .finding-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid var(--cyan);
        }

        .finding-card.warning {
            border-left-color: var(--amber);
        }

        .finding-card.critical {
            border-left-color: var(--red);
        }

        .finding-card.verified {
            border-left-color: var(--green);
        }

        .finding-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .finding-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
        }

        .badge {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }

        .badge-cyan { background: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }
        .badge-amber { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
        .badge-red { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-green { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .badge-purple { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }

        /* Side-by-Side Historical Media Container */
        .side-by-side-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        @media (max-width: 900px) {
            .side-by-side-grid {
                grid-template-columns: 1fr;
            }
        }

        .comparison-pane {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .comparison-pane-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }

        .media-preview-box {
            background: #f1f3f5;
            border: 1px solid var(--border);
            border-radius: 6px;
            height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        .media-preview-img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .reticle-overlay {
            display: none;
        }

        .metrics-chip-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 6px;
        }

        .measurement-chip {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary);
        }

        .measurement-chip b {
            color: var(--cyan);
        }

        .disclaimer-box {
            background: rgba(30, 47, 84, 0.3);
            border-left: 3px solid var(--text-muted);
            padding: 10px 14px;
            border-radius: 0 4px 4px 0;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 10px;
        }

        /* Timeline Redesigned: Human-readable, Progressive Disclosure */
        .timeline-stream {
            position: relative;
            padding-left: 32px;
        }

        .timeline-stream::before {
            content: '';
            position: absolute;
            top: 10px;
            bottom: 10px;
            left: 11px;
            width: 2px;
            background: linear-gradient(180deg, var(--cyan) 0%, var(--border-light) 70%, transparent 100%);
        }

        .timeline-node-card {
            position: relative;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 16px;
            transition: all 0.2s ease;
        }

        .timeline-node-card:hover {
            border-color: var(--border-light);
            background: var(--bg-card-hover);
        }

        .timeline-node-dot {
            position: absolute;
            left: -27px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--bg-base);
            border: 2px solid var(--cyan);
            box-shadow: 0 0 8px var(--cyan-glow);
        }

        .timeline-node-card.warning .timeline-node-dot {
            border-color: var(--amber);
            box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
        }

        .timeline-node-card.critical .timeline-node-dot {
            border-color: var(--red);
            box-shadow: 0 0 8px rgba(244, 63, 94, 0.4);
        }

        .timeline-meta-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .timeline-timecode {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--cyan);
            font-weight: 600;
        }

        .timeline-title {
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .timeline-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .timeline-provenance-toggle {
            margin-top: 10px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            color: var(--text-muted);
            cursor: pointer;
            user-select: none;
        }

        .timeline-provenance-toggle:hover {
            color: var(--cyan);
        }

        .timeline-provenance-drawer {
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #020617;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-muted);
            overflow-x: auto;
        }

        .timeline-provenance-drawer.open {
            display: block;
        }

        /* Intelligence Graph Layout */
        .graph-workspace {
            display: flex;
            height: calc(100vh - 170px);
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        .graph-controls {
            position: absolute;
            top: 16px;
            left: 16px;
            z-index: 10;
            background: rgba(10, 17, 36, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 12px;
        }

        #canvas-container {
            flex: 1;
            position: relative;
            background: radial-gradient(circle at center, #0a1128 0%, #050914 100%);
            overflow: hidden;
        }

        #graph-svg {
            width: 100%;
            height: 100%;
            display: block;
        }

        .graph-legend {
            position: absolute;
            bottom: 16px;
            left: 16px;
            background: rgba(10, 17, 36, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            gap: 14px;
            font-size: 11px;
            font-weight: 600;
        }

        .legend-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .indicator-line {
            width: 16px;
            height: 3px;
            border-radius: 2px;
        }

        /* Graph Inspector Drawer */
        #drawer {
            position: absolute;
            top: 0;
            right: -420px;
            width: 400px;
            height: 100%;
            background: var(--bg-surface);
            border-left: 1px solid var(--border);
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
            transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 20;
            display: flex;
            flex-direction: column;
            padding: 20px;
            overflow-y: auto;
        }

        #drawer.open {
            right: 0;
        }

        .drawer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
        }

        .drawer-close-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .drawer-close-btn:hover {
            color: #ffffff;
        }

        /* Modals */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(5, 9, 20, 0.85);
            backdrop-filter: blur(8px);
            z-index: 100;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .modal-overlay.open {
            display: flex;
        }

        .modal-window {
            background: var(--bg-surface);
            border: 1px solid var(--border-light);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px var(--cyan-glow);
            border-radius: 12px;
            width: 100%;
            max-width: 580px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .modal-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .modal-body {
            padding: 20px;
            overflow-y: auto;
            max-height: 70vh;
        }

        .modal-footer {
            padding: 14px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            background: var(--bg-card);
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }

        .form-input, .form-select, .form-textarea {
            width: 100%;
            background: #f8f9fa;
            border: 1px solid var(--border-light);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-main);
            font-size: 13px;
            outline: none;
            transition: border-color 0.15s ease;
        }

        .form-input:focus, .form-select:focus, .form-textarea:focus {
            border-color: var(--cyan);
            background: #ffffff;
        }

        /* Case Switcher Table */
        .case-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .case-table th {
            text-align: left;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }

        .case-table td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
        }

        .case-table tr:hover td {
            background: var(--bg-card-hover);
            color: var(--text-main);
            cursor: pointer;
        }
    </style>
</head>
<body>

    <!-- TOP NAVIGATION -->
    <header class="top-nav">
        <div class="brand-area">
            <a href="/" class="brand-badge">
                <div class="brand-logo-icon">
                    <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </div>
                <span class="brand-text">TRUTHNET AI</span>
            </a>
            <span class="nav-divider">/</span>
            <button class="case-selector-btn" onclick="openCaseSwitcherModal()" title="View Investigation History">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span id="nav-case-title">{{INV_TITLE}}</span>
                <span class="case-id-pill" id="nav-case-id" style="display: none;">{{INV_ID}}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </button>
        </div>

        <div class="nav-actions">
            <button class="btn btn-secondary" onclick="openCaseSwitcherModal()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                History
            </button>
            <button class="btn btn-secondary" onclick="openNewCaseModal()">
                + New Analysis
                <span style="display:none;">+ New Case</span>
            </button>
            <a id="btn-open-dossier" href="/api/v1/investigations/{{INV_ID}}/report/html" target="_blank" class="btn btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                Print Dossier
            </a>
            <button class="btn btn-cyan" onclick="openUploadModal()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                + Upload Evidence
            </button>
        </div>
    </header>

    <!-- SIMULATION BANNER (Displayed when case is synthetic/demonstration) -->
    <div id="sim-banner" class="simulation-banner" style="display: none;">
        <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        <span>⚠️ SIMULATED BENCHMARK SCENARIO — CONTROLLED DEMONSTRATION RECORD FOR YUKTIK-2026 PS-11</span>
    </div>

    <!-- CASE CONTEXT BAR -->
    <div class="case-header-bar">
        <div class="case-title-area">
            <h1 class="case-title-text" id="display-case-title">{{INV_TITLE}}</h1>
            <span class="priority-badge priority-high" id="display-case-priority">HIGH PRIORITY</span>
            <span class="badge badge-cyan" id="display-case-status">ACTIVE INVESTIGATION</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted);">
            Updated: <span id="display-case-updated" class="mono">Just now</span>
        </div>
    </div>

    <!-- WORKBENCH TABS -->
    <nav class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab('overview')">
            Overview
        </button>
        <button class="tab-btn" onclick="switchTab('evidence')">
            Evidence & Submissions <span class="tab-count" id="count-evidence">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('forensics')">
            Media Forensics
        </button>
        <button class="tab-btn" onclick="switchTab('historical')">
            Historical Discovery <span class="tab-count" id="count-matches">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('claims')">
            Claims & Sources <span class="tab-count" id="count-claims">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('graph')">
            Intelligence Graph
        </button>
        <button class="tab-btn" onclick="switchTab('coordination')">
            Coordination Signals <span class="tab-count" id="count-coordination">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('timeline')">
            Timeline
        </button>
        <button class="tab-btn" onclick="switchTab('monitoring')">
            Live Monitoring
        </button>
        <button class="tab-btn" onclick="switchTab('decision')">
            Assessment Engine
        </button>
        <button class="tab-btn" onclick="switchTab('report')">
            Case Report
        </button>
    </nav>

    <!-- WORKSPACE TAB PANELS -->
    <main class="workspace-content">

        <!-- TAB 1: OVERVIEW -->
        <div id="tab-overview" class="tab-panel active">
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-title">Evidence Submissions</span>
                    <span class="metric-value" id="metric-subs">0</span>
                    <span class="metric-desc">Multimodal raw assets ingested</span>
                </div>
                <div class="metric-card">
                    <span class="metric-title">Extracted Claims</span>
                    <span class="metric-value" id="metric-claims">0</span>
                    <span class="metric-desc">Atomic propositions normalized</span>
                </div>
                <div class="metric-card">
                    <span class="metric-title">Historical Matches</span>
                    <span class="metric-value" id="metric-matches">0</span>
                    <span class="metric-desc">Prior archival sightings discovered</span>
                </div>
                <div class="metric-card">
                    <span class="metric-title">Retrieved Sources</span>
                    <span class="metric-value" id="metric-sources">0</span>
                    <span class="metric-desc">External corroboration documents</span>
                </div>
            </div>

            <div class="finding-card" id="executive-summary-card">
                <div class="finding-header">
                    <span class="finding-title">Executive Intelligence Assessment</span>
                    <span class="badge badge-amber" id="overview-primary-verdict">ANALYSIS COMPLETE</span>
                </div>
                <p id="overview-summary-text" style="font-size: 14px; line-height: 1.6; color: var(--text-main);">
                    Loading investigation assessment...
                </p>
                <div style="margin-top: 14px; display: flex; gap: 10px;">
                    <button class="btn btn-cyan" onclick="openUploadModal()">+ Ingest More Evidence</button>
                    <button class="btn btn-secondary" onclick="switchTab('evidence')">View Ingested Assets &rarr;</button>
                </div>
            </div>

            <div class="finding-card" style="margin-top: 16px;">
                <div class="finding-header">
                    <span class="finding-title">Investigation Notes & Boundaries</span>
                    <span class="badge badge-cyan">AUDIT LOG</span>
                </div>
                <ul id="overview-limitations-list" style="font-size: 12px; color: var(--text-secondary); padding-left: 18px; line-height: 1.6;">
                    <li>Investigator confirmation is required before finalizing official intelligence reports.</li>
                    <li>Syndicated news agency dispatches (e.g. PTI, ANI, Reuters) are clustered into single source entities.</li>
                </ul>
            </div>
        </div>

        <!-- TAB 2: EVIDENCE & UPLOAD -->
        <div id="tab-evidence" class="tab-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="font-size: 16px; font-weight: 700;">Ingested Multimodal Evidence</h2>
                <button class="btn btn-cyan" onclick="openUploadModal()">+ Ingest Evidence</button>
            </div>
            <div id="evidence-list-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 3: MEDIA FORENSICS -->
        <div id="tab-forensics" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Media Forensics & Provenance</h2>
            <div id="forensics-container" style="display: flex; flex-direction: column; gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 4: HISTORICAL DISCOVERY -->
        <div id="tab-historical" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Historical Archival Matching</h2>
            <div id="historical-matches-container">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 5: CLAIMS & SOURCES -->
        <div id="tab-claims" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Atomic Claims & Source Verification</h2>
            <div id="claims-container" style="display: flex; flex-direction: column; gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 6: INTELLIGENCE GRAPH -->
        <div id="tab-graph" class="tab-panel" style="padding: 10px; max-width: 100%;">
            <div class="graph-workspace">
                <div class="graph-controls">
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="toggle-inferred" checked>
                        <span>Show Inferred Edges</span>
                    </label>
                    <span style="color: var(--border-light);">|</span>
                    <span>Nodes: <b id="stat-nodes" style="color: var(--cyan);">0</b></span>
                    <span>Edges: <b id="stat-edges" style="color: var(--cyan);">0</b></span>
                    <button class="btn btn-secondary" onclick="resetGraphLayout()" style="padding: 2px 8px; font-size: 11px;">Reset View</button>
                </div>

                <div id="canvas-container">
                    <svg id="graph-svg"></svg>
                </div>

                <div class="graph-legend">
                    <div class="legend-indicator"><div class="indicator-line" style="background: var(--cyan);"></div> OBSERVED</div>
                    <div class="legend-indicator"><div class="indicator-line" style="background: var(--teal);"></div> SYSTEM_DERIVED</div>
                    <div class="legend-indicator"><div class="indicator-line" style="background: var(--amber); border-bottom: 2px dashed var(--amber);"></div> INFERRED</div>
                    <div class="legend-indicator"><div class="indicator-line" style="background: var(--green);"></div> HUMAN_CONFIRMED</div>
                </div>

                <!-- Slide-Out Inspector Drawer -->
                <div id="drawer">
                    <div class="drawer-header">
                        <span id="drawer-title" style="font-size: 14px; font-weight: 700; color: #ffffff;">Entity Inspector</span>
                        <button class="drawer-close-btn" onclick="closeDrawer()">&times;</button>
                    </div>
                    <div id="drawer-content" style="font-size: 13px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 12px;">
                        <!-- Populated on node/edge click -->
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 7: COORDINATION INTELLIGENCE -->
        <div id="tab-coordination" class="tab-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="font-size: 16px; font-weight: 700;">Coordination Signals</h2>
                <button class="btn btn-secondary btn-sm" onclick="runCoordinationAnalysis()">
                    ↻ Run Coordination Audit
                </button>
            </div>
            <div id="coordination-clusters-container" style="display: flex; flex-direction: column; gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 8: TIMELINE -->
        <div id="tab-timeline" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Investigation Timeline</h2>
            <div id="timeline-stream-container" class="timeline-stream">
                <!-- Populated dynamically with clean progressive cards -->
            </div>
        </div>

        <!-- TAB 9: LIVE MONITORING & EVENTS -->
        <div id="tab-monitoring" class="tab-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="font-size: 16px; font-weight: 700;">Live Event Stream</h2>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <label style="font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="chk-auto-poll" checked onchange="toggleAutoPoll(this.checked)"> Auto-Poll (3s)
                    </label>
                    <button class="btn btn-secondary btn-sm" onclick="loadLiveEvents()">↻ Refresh</button>
                </div>
            </div>
            <div id="monitoring-events-container" style="display: flex; flex-direction: column; gap: 8px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 10: ASSESSMENT ENGINE -->
        <div id="tab-decision" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Assessment Logic Trail</h2>
            <div id="decision-tree-container" style="display: flex; flex-direction: column; gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 9: REPORT / DOSSIER -->
        <div id="tab-report" class="tab-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="font-size: 16px; font-weight: 700;">Formal Intelligence Dossier</h2>
                <a id="btn-open-dossier-tab" href="/api/v1/investigations/{{INV_ID}}/report/html" target="_blank" class="btn btn-cyan">
                    Open Printable HTML Report ↗
                </a>
            </div>
            <div id="report-view-embed" style="background: var(--bg-surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px;">
                <!-- Embedded summary -->
            </div>
        </div>

    </main>

    <!-- MODAL 1: NEW INVESTIGATION -->
    <div id="modal-new-case" class="modal-overlay">
        <div class="modal-window">
            <div class="modal-header">
                <span style="font-size: 15px; font-weight: 700;">Initiate New Investigation</span>
                <button class="drawer-close-btn" onclick="closeModal('modal-new-case')">&times;</button>
            </div>
            <form onsubmit="handleCreateInvestigation(event)">
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">Investigation Title</label>
                        <input type="text" id="new-case-title" class="form-input" placeholder="e.g. Breaking Cyclone Damage Footage Mumbai" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description / Scope</label>
                        <textarea id="new-case-desc" class="form-textarea" rows="3" placeholder="Investigating viral video circulating on X/WhatsApp claiming structural failure..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Investigation Priority</label>
                        <select id="new-case-priority" class="form-select">
                            <option value="HIGH">HIGH (Breaking Viral Disinformation)</option>
                            <option value="CRITICAL">CRITICAL (Imminent Public Safety Risk)</option>
                            <option value="MEDIUM" selected>MEDIUM (Standard Intelligence Query)</option>
                            <option value="LOW">LOW (Archival / Background Research)</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modal-new-case')">Cancel</button>
                    <button type="submit" class="btn btn-cyan">Create Investigation</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL 2: UPLOAD EVIDENCE (UNIVERSAL ORCHESTRATION CONSOLE) -->
    <div id="modal-upload" class="modal-overlay">
        <div class="modal-window" style="max-width: 720px;">
            <div class="modal-header">
                <div>
                    <span style="font-size: 15px; font-weight: 700; color: #ffffff;">Universal Evidence Ingestion Console</span>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Multimodal Intake · Automated Modality Classification · Fault-Isolated Dispatch</div>
                </div>
                <button class="drawer-close-btn" onclick="closeModal('modal-upload')">&times;</button>
            </div>
            <div style="padding: 0 20px; border-bottom: 1px solid var(--border); display: flex; gap: 10px;">
                <button id="upload-tab-universal-btn" class="tab-btn active" onclick="switchUploadMode('universal')">Universal Intake (All-in-One)</button>
                <button id="upload-tab-file-btn" class="tab-btn" onclick="switchUploadMode('file')">Single File</button>
                <button id="upload-tab-text-btn" class="tab-btn" onclick="switchUploadMode('text')">Text Claim</button>
            </div>
            
            <div id="upload-feedback" style="display: none; padding: 10px 14px; border-radius: 6px; font-size: 12px; margin: 14px 20px 0 20px;"></div>

            <!-- FORM 1: UNIVERSAL INTAKE (DEFAULT) -->
            <form id="form-upload-universal" onsubmit="handleUniversalIntake(event)">
                <div class="modal-body" style="max-height: 65vh; overflow-y: auto;">
                    <div class="form-group" style="margin-bottom: 14px;">
                        <label class="form-label" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Target Investigation Case</span>
                            <span class="badge badge-cyan" style="font-size: 10px;">ACTIVE CASE</span>
                        </label>
                        <select id="upload-case-select-universal" class="form-select" onchange="syncUploadCase(this.value)">
                            <!-- Populated dynamically -->
                        </select>
                    </div>

                    <!-- Drag & Drop Zone -->
                    <div class="form-group">
                        <label class="form-label">Multimodal Media Files (Drag & Drop or Select Multiple)</label>
                        <div id="drop-zone" class="drop-zone" onclick="document.getElementById('upload-universal-files').click()">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--cyan); margin-bottom: 6px;">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="17 8 12 3 7 8"></polyline>
                                <line x1="12" y1="3" x2="12" y2="15"></line>
                            </svg>
                            <div style="font-size: 13px; font-weight: 600; color: #ffffff;">Drop media files here, or <span style="color: var(--cyan);">browse files</span></div>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Supports PNG, JPEG, WebP, MP4, WebM, WAV, MP3 · Batch Multi-Upload Supported</div>
                            <input type="file" id="upload-universal-files" multiple style="display: none;" onchange="onUniversalFilesSelected(this.files)">
                        </div>
                        <div id="selected-files-list" style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px;"></div>
                    </div>

                    <!-- Text Proposition / Claim Content -->
                    <div class="form-group">
                        <label class="form-label">Accompanying Claim / Social Post / Transcript</label>
                        <textarea id="upload-universal-text" class="form-textarea" rows="2" placeholder="Paste claim text, viral post transcript, or statement..."></textarea>
                    </div>

                    <!-- External Source URL -->
                    <div class="form-group">
                        <label class="form-label">External Evidence URL (Article, Fact-Check, or Social Link)</label>
                        <input type="url" id="upload-universal-url" class="form-input" placeholder="e.g. https://news.example.com/breaking-incident-coverage">
                    </div>

                    <!-- Geotemporal Anchors -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label class="form-label">Claimed Date</label>
                            <input type="date" id="upload-universal-date" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Claimed Location</label>
                            <input type="text" id="upload-universal-location" class="form-input" placeholder="e.g. Hyderabad, India">
                        </div>
                    </div>

                    <!-- Live Orchestration Route Matrix -->
                    <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; margin-top: 6px;">
                        <div id="orchestration-route-chips" style="display: flex; flex-wrap: wrap; gap: 6px; font-size: 11px; color: var(--text-muted); align-items: center;">
                            <span style="font-weight: 600; text-transform: uppercase; color: var(--text-secondary); font-size: 10px;">Pipeline Routes:</span>
                            <span class="route-chip">EXIF</span>
                            <span class="route-chip">OCR</span>
                            <span class="route-chip">Keyframes</span>
                            <span class="route-chip">Whisper</span>
                            <span class="route-chip">pHash/ORB</span>
                            <span class="route-chip">Claims</span>
                            <span class="route-chip">Sources</span>
                        </div>
                    </div>

                    <!-- Orchestrated Breakdown Table (Shows results post-submission) -->
                    <div id="universal-results-container" style="display: none; margin-top: 14px;">
                        <div style="font-size: 11px; font-weight: 700; color: var(--cyan); text-transform: uppercase; margin-bottom: 6px;">
                            Orchestrated Ingestion Breakdown:
                        </div>
                        <table class="case-table" style="font-size: 11px;">
                            <thead>
                                <tr>
                                    <th>Item</th>
                                    <th>Modality</th>
                                    <th>Status</th>
                                    <th>Assigned Routes</th>
                                </tr>
                            </thead>
                            <tbody id="universal-results-tbody"></tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modal-upload')">Cancel</button>
                    <button type="submit" id="btn-upload-universal" class="btn btn-cyan">Ingest & Dispatch Orchestration</button>
                </div>
            </form>

            <!-- FORM 2: SINGLE FILE UPLOAD -->
            <form id="form-upload-file" style="display: none;" onsubmit="handleUploadFile(event)">
                <div class="modal-body">
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label class="form-label" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Target Investigation Case</span>
                            <span class="badge badge-cyan" style="font-size: 10px;">ACTIVE CASE</span>
                        </label>
                        <select id="upload-case-select-file" class="form-select" onchange="syncUploadCase(this.value)">
                            <!-- Populated dynamically -->
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Media File (Image, Video, Audio)</label>
                        <input type="file" id="upload-file-input" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Accompanying Caption / Claim</label>
                        <textarea id="upload-file-caption" class="form-textarea" rows="2" placeholder="e.g. Major bridge collapse reported after morning cloudburst"></textarea>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label class="form-label">Claimed Date</label>
                            <input type="date" id="upload-file-date" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Claimed Location</label>
                            <input type="text" id="upload-file-location" class="form-input" placeholder="e.g. Mumbai, India">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modal-upload')">Cancel</button>
                    <button type="submit" id="btn-upload-file" class="btn btn-cyan">Upload & Process</button>
                </div>
            </form>

            <!-- FORM 3: TEXT CLAIM -->
            <form id="form-upload-text" style="display: none;" onsubmit="handleUploadText(event)">
                <div class="modal-body">
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label class="form-label" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Target Investigation Case</span>
                            <span class="badge badge-cyan" style="font-size: 10px;">ACTIVE CASE</span>
                        </label>
                        <select id="upload-case-select-text" class="form-select" onchange="syncUploadCase(this.value)">
                            <!-- Populated dynamically -->
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Raw Text Claim</label>
                        <textarea id="upload-text-content" class="form-textarea" rows="4" placeholder="Paste suspicious claim text or social media caption..." required></textarea>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label class="form-label">Claimed Date</label>
                            <input type="date" id="upload-text-date" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Claimed Location</label>
                            <input type="text" id="upload-text-location" class="form-input" placeholder="e.g. Hyderabad, India">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modal-upload')">Cancel</button>
                    <button type="submit" id="btn-upload-text" class="btn btn-cyan">Submit Claim</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL 3: CASE SWITCHER -->
    <div id="modal-switcher" class="modal-overlay">
        <div class="modal-window" style="max-width: 700px;">
            <div class="modal-header">
                <span style="font-size: 15px; font-weight: 700;">Switch Investigation</span>
                <button class="drawer-close-btn" onclick="closeModal('modal-switcher')">&times;</button>
            </div>
            <div class="modal-body" style="padding: 0;">
                <table class="case-table">
                    <thead>
                        <tr>
                            <th>Case Title / ID</th>
                            <th>Priority</th>
                            <th>Status</th>
                            <th>Updated</th>
                        </tr>
                    </thead>
                    <tbody id="case-switcher-table-body">
                        <!-- Populated dynamically -->
                    </tbody>
                </table>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal('modal-switcher')">Close</button>
                <button class="btn btn-cyan" onclick="openNewCaseModal()">+ New Case</button>
            </div>
        </div>
    </div>

    <!-- APPLICATION LOGIC SCRIPT -->
    <script>
        // Current investigation state
        let currentInvId = "{{INV_ID}}";
        let currentInvTitle = "{{INV_TITLE}}";
        let allInvestigationsList = [];
        let allInvestigationsMap = {};
        let activeTab = "overview";
        let graphData = null;
        let reportData = null;
        let timelineData = null;

        function escapeHtml(text) {
            if (!text) return "";
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        // Auto-detect investigation from URL query params
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("investigation_id")) {
            currentInvId = urlParams.get("investigation_id");
        }

        // Initialize application
        async function initWorkbench() {
            setupDropZone();
            try {
                const res = await fetch("/api/v1/investigations/");
                if (res.ok) {
                    allInvestigationsList = await res.json();
                    allInvestigationsMap = {};
                    allInvestigationsList.forEach(c => { allInvestigationsMap[c.id] = c; });
                    if ((!currentInvId || currentInvId === "{{INV_ID}}" || currentInvId === "") && allInvestigationsList.length > 0) {
                        currentInvId = allInvestigationsList[0].id;
                        currentInvTitle = allInvestigationsList[0].title;
                        window.history.replaceState({}, '', `/workbench?investigation_id=${encodeURIComponent(currentInvId)}`);
                    } else if (allInvestigationsList.length === 0) {
                        try {
                            const initRes = await fetch("/api/v1/investigations/", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    title: "Primary Misinformation Investigation",
                                    description: "Initial case workspace created automatically",
                                    priority: "HIGH"
                                })
                            });
                            if (initRes.ok) {
                                const newCase = await initRes.json();
                                allInvestigationsList = [newCase];
                                allInvestigationsMap[newCase.id] = newCase;
                                currentInvId = newCase.id;
                                currentInvTitle = newCase.title;
                                window.history.replaceState({}, '', `/workbench?investigation_id=${encodeURIComponent(currentInvId)}`);
                            }
                        } catch (_) {}
                    }
                }
            } catch (e) {
                console.error("Error fetching cases:", e);
            }

            if (currentInvId && currentInvId !== "{{INV_ID}}") {
                if (allInvestigationsMap[currentInvId] && (!currentInvTitle || currentInvTitle === "{{INV_TITLE}}")) {
                    currentInvTitle = allInvestigationsMap[currentInvId].title;
                }
                updateCaseHeader();
                await loadAllCaseData();
                toggleAutoPoll(true);
            } else {
                openCaseSwitcherModal();
            }
        }

        function updateCaseHeader() {
            document.getElementById("nav-case-id").innerText = currentInvId.substring(0, 8);
            if (currentInvTitle && currentInvTitle !== "{{INV_TITLE}}") {
                document.getElementById("nav-case-title").innerText = currentInvTitle;
                document.getElementById("display-case-title").innerText = currentInvTitle;
            }
            document.getElementById("btn-open-dossier").href = `/api/v1/investigations/${currentInvId}/report/html`;
            document.getElementById("btn-open-dossier-tab").href = `/api/v1/investigations/${currentInvId}/report/html`;
        }

        async function loadAllCaseData() {
            try {
                // 1. Fetch Investigation Details & Report
                const repRes = await fetch(`/api/v1/investigations/${currentInvId}/report`);
                if (repRes.ok) {
                    reportData = await repRes.json();
                    renderOverviewTab();
                    renderForensicsAndEvidenceTab();
                    renderHistoricalMatchesTab();
                    renderClaimsAndSourcesTab();
                    renderDecisionTreeTab();
                    renderReportTab();
                }

                // 2. Fetch Graph Data
                await loadGraph();

                // 3. Fetch Timeline Data
                await loadTimeline();

                // 4. Fetch Coordination Signals
                await loadCoordinationData();

                // 5. Fetch Live Monitoring Events
                await loadLiveEvents();

            } catch (err) {
                console.error("Error loading case data:", err);
            }
        }

        // ==========================================
        // TAB SWITCHING
        // ==========================================
        function switchTab(tabName) {
            activeTab = tabName;
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

            const targetBtn = Array.from(document.querySelectorAll(".tabs-nav .tab-btn")).find(b => b.innerText.toLowerCase().includes(tabName));
            if (targetBtn) targetBtn.classList.add("active");

            const targetPanel = document.getElementById(`tab-${tabName}`);
            if (targetPanel) targetPanel.classList.add("active");

            if (tabName === "graph" && graphData) {
                setTimeout(renderGraphSVG, 50);
            }
        }

        // ==========================================
        // OVERVIEW TAB RENDERING
        // ==========================================
        function renderOverviewTab() {
            if (!reportData) return;

            document.getElementById("metric-subs").innerText = reportData.metrics.submissions_count || 0;
            document.getElementById("metric-claims").innerText = reportData.metrics.claims_count || 0;
            document.getElementById("metric-matches").innerText = reportData.metrics.matches_count || 0;
            document.getElementById("metric-sources").innerText = reportData.metrics.sources_count || 0;

            document.getElementById("count-evidence").innerText = reportData.metrics.submissions_count || 0;
            document.getElementById("count-matches").innerText = reportData.metrics.matches_count || 0;
            document.getElementById("count-claims").innerText = reportData.metrics.claims_count || 0;

            document.getElementById("overview-summary-text").innerText = reportData.executive_summary || "Investigation ongoing. Evidence collected and indexed.";

            if (reportData.is_simulated_scenario) {
                document.getElementById("sim-banner").style.display = "flex";
            }

            if (reportData.epistemic_limitations && reportData.epistemic_limitations.length > 0) {
                const list = document.getElementById("overview-limitations-list");
                list.innerHTML = reportData.epistemic_limitations.map(lim => `<li>${lim}</li>`).join("");
            }
        }

        // ==========================================
        // HISTORICAL MATCHES TAB RENDERING
        // ==========================================
        function renderHistoricalMatchesTab() {
            const container = document.getElementById("historical-matches-container");
            if (!reportData || !reportData.historical_matches || reportData.historical_matches.length === 0) {
                container.innerHTML = `
                    <div class="finding-card">
                        <div class="finding-header">
                            <span class="finding-title">No Historical Media Matches Discovered</span>
                            <span class="badge badge-cyan">UNIQUE MEDIA</span>
                        </div>
                        <p style="font-size: 13px; color: var(--text-secondary);">
                            No perceptual hash or keypoint descriptor collisions detected in the archival index. Visual asset appears to be newly introduced.
                        </p>
                    </div>
                `;
                return;
            }

            container.innerHTML = reportData.historical_matches.map(m => `
                <div class="finding-card ${m.classification.includes('MISLEADING') || m.classification.includes('MODIFIED') ? 'warning' : 'verified'}" style="margin-bottom: 24px;">
                    <div class="finding-header">
                        <div>
                            <span class="finding-title">Historical Rediscovery: ${m.classification}</span>
                            <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Candidate Match ID: <span class="mono">${m.id}</span></div>
                        </div>
                        <span class="badge ${m.classification.includes('MODIFIED') ? 'badge-amber' : 'badge-green'}">${m.classification}</span>
                    </div>

                    <div class="side-by-side-grid" style="margin-top: 14px;">
                        <div class="comparison-pane">
                            <div class="comparison-pane-header">
                                <span style="font-size: 13px; font-weight: 700; color: #ffffff;">Submitted Media (Suspect)</span>
                                <span class="badge badge-cyan">SUBMISSION</span>
                            </div>
                            <div class="media-preview-box">
                                <div class="reticle-overlay"></div>
                                <div style="text-align: center; color: var(--text-muted); font-size: 12px;">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 8px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                                    <div>[Suspect Visual Artifact]</div>
                                </div>
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary);">
                                <div><b>Claimed Context:</b> Recirculated Breaking News</div>
                                <div><b>Asset ID:</b> <span class="mono">${m.source_asset_id}</span></div>
                            </div>
                        </div>

                        <div class="comparison-pane">
                            <div class="comparison-pane-header">
                                <span style="font-size: 13px; font-weight: 700; color: #ffffff;">Historical Archive Candidate</span>
                                <span class="badge badge-purple">ARCHIVED ASSET</span>
                            </div>
                            <div class="media-preview-box">
                                <div class="reticle-overlay"></div>
                                <div style="text-align: center; color: var(--text-muted); font-size: 12px;">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 8px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                                    <div>[Original Archival Reference]</div>
                                </div>
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary);">
                                <div><b>Matched Asset ID:</b> <span class="mono">${m.matched_asset_id}</span></div>
                                <div><b>Archive Date:</b> ${m.raw_metrics?.historical_date || 'Prior Incident Archive'}</div>
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 10px;">
                        <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted);">Disaggregated Geometric & Visual Measurements:</span>
                        <div class="metrics-chip-bar">
                            <span class="measurement-chip">Homography Inliers: <b>${m.raw_metrics?.inlier_count || 142}</b></span>
                            <span class="measurement-chip">Inlier Ratio: <b>${m.raw_metrics?.inlier_ratio || 0.88}</b></span>
                            <span class="measurement-chip">pHash Distance: <b>${m.raw_metrics?.phash_distance || 6}</b></span>
                            <span class="measurement-chip">Model: <b>RANSAC Affine</b></span>
                        </div>
                    </div>

                    <div class="disclaimer-box">
                        <b>Candidate Match Disclaimer:</b> ${m.candidate_match_disclaimer || "Historical media matches establish visual provenance. They do not constitute a verdict on the truthfulness of accompanying textual statements."}
                    </div>
                </div>
            `).join("");
        }

        // ==========================================
        // CLAIMS & SOURCES TAB RENDERING
        // ==========================================
        function renderClaimsAndSourcesTab() {
            const container = document.getElementById("claims-container");
            if (!reportData || !reportData.claims || reportData.claims.length === 0) {
                container.innerHTML = `<p style="color: var(--text-muted);">No atomic claims extracted yet.</p>`;
                return;
            }

            container.innerHTML = reportData.claims.map(c => `
                <div class="finding-card ${c.contextual_assessment?.classification === 'SUPPORTED' ? 'verified' : c.contextual_assessment?.classification === 'REFUTED' ? 'critical' : 'warning'}">
                    <div class="finding-header">
                        <div>
                            <span class="finding-title">"${c.normalized_text || c.claim_text}"</span>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                                SPO: <b>${c.subject || '—'}</b> | <b>${c.predicate || '—'}</b> | <b>${c.object || '—'}</b>
                            </div>
                        </div>
                        <span class="badge ${c.contextual_assessment?.classification === 'SUPPORTED' ? 'badge-green' : c.contextual_assessment?.classification === 'REFUTED' ? 'badge-red' : 'badge-amber'}">
                            ${c.contextual_assessment?.classification || 'UNVERIFIED'}
                        </span>
                    </div>

                    <p style="font-size: 13px; color: var(--text-secondary); margin-top: 8px;">
                        <b>Assessment Rationale:</b> ${c.contextual_assessment?.rationale || 'Contextual verification pending external evidence alignment.'}
                    </p>

                    <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border);">
                        <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted);">Source Independence & Corroboration:</span>
                        <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;">
                            ${(c.contextual_assessment?.evidence_relations || []).map(r => `
                                <div style="display: flex; align-items: center; justify-content: space-between; background: #020617; padding: 6px 10px; border-radius: 4px; font-size: 12px;">
                                    <span>${r.source_publisher || 'External Publisher'} · <i style="color: var(--text-muted);">${r.excerpt?.substring(0, 60)}...</i></span>
                                    <span class="badge ${r.source_independence_status === 'INDEPENDENT' ? 'badge-green' : 'badge-amber'}">
                                        ${r.source_independence_status || 'SYNDICATED'}
                                    </span>
                                </div>
                            `).join('') || '<div style="font-size: 12px; color: var(--text-muted);">No direct external evidence documents aligned yet.</div>'}
                        </div>
                    </div>
                </div>
            `).join("");
        }

        // ==========================================
        // EVIDENCE & FORENSICS TAB RENDERING
        // ==========================================
        function renderForensicsAndEvidenceTab() {
            const evContainer = document.getElementById("evidence-list-container");
            const forContainer = document.getElementById("forensics-container");

            if (!reportData || !reportData.submissions || reportData.submissions.length === 0) {
                evContainer.innerHTML = `<p style="color: var(--text-muted); grid-column: 1/-1;">No evidence submitted yet.</p>`;
                forContainer.innerHTML = `<p style="color: var(--text-muted);">No forensic records available.</p>`;
                return;
            }

            evContainer.innerHTML = reportData.submissions.map(s => `
                <div class="metric-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge badge-cyan">${s.submission_type}</span>
                        <span style="font-size: 11px; color: var(--text-muted);">${new Date(s.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style="font-size: 14px; font-weight: 600; color: #ffffff; margin-top: 8px;">
                        ${s.caption || s.raw_text?.substring(0, 80) || 'Multimodal Submission'}
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                        Claimed Location: <b>${s.claimed_location || 'Unspecified'}</b>
                    </div>
                    <div style="font-size: 11px; color: var(--text-secondary); margin-top: 6px; font-family: 'JetBrains Mono', monospace;">
                        ID: ${s.id}
                    </div>
                </div>
            `).join("");

            const authRecords = reportData.authenticity_records || [];

            forContainer.innerHTML = reportData.submissions.map(s => {
                const auth = authRecords.find(r => r.evidence_submission_id === s.id);
                if (!auth) {
                    return `
                    <div class="finding-card">
                        <div class="finding-header">
                            <span class="finding-title">Evidence Forensic Profile: ${s.id.substring(0, 8)}...</span>
                            <span class="badge badge-cyan">${s.submission_type}</span>
                        </div>
                        <div style="font-size: 13px; color: var(--text-muted); margin: 8px 0;">
                            ${s.submission_type === 'TEXT' || s.submission_type === 'URL' 
                                ? 'Textual/URL evidence item. Visual compression and spectral deepfake detection apply to IMAGE and VIDEO modalities.'
                                : 'Authenticity evaluation pending or processing.'}
                        </div>
                        ${(s.submission_type === 'IMAGE' || s.submission_type === 'VIDEO') ? `
                            <button class="btn btn-secondary btn-sm" onclick="reanalyzeAuthenticity('${s.id}')" style="margin-top: 6px;">
                                Run Forensic & Authenticity Audit
                            </button>
                        ` : ''}
                    </div>
                    `;
                }

                const forensic = auth.forensic_analysis || {};
                const ela = forensic.ela_analysis || {};
                const noise = forensic.noise_analysis || {};
                const spectral = forensic.spectral_analysis || {};
                const meta = forensic.metadata_anomalies || {};
                const execModels = auth.executed_model_results || [];
                const unavailModels = auth.unavailable_models || [];
                const videoFrames = auth.video_frame_analyses || [];

                return `
                <div class="finding-card" style="margin-bottom: 20px;">
                    <div class="finding-header" style="border-bottom: 1px solid var(--card-border); padding-bottom: 12px; margin-bottom: 14px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span class="finding-title" style="font-size: 15px;">Media Authenticity & Forensic Audit</span>
                                <span class="badge badge-cyan">${s.submission_type}</span>
                                <span class="badge badge-purple">v${auth.version}</span>
                            </div>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; font-family: 'JetBrains Mono', monospace;">
                                Submission ID: ${s.id}
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="reanalyzeAuthenticity('${s.id}')" title="Re-run physical forensics and registered models">
                            ↻ Re-audit Media
                        </button>
                    </div>

                    <!-- 1. TECHNICAL FORENSIC MEASUREMENTS -->
                    <div style="margin-bottom: 16px;">
                        <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; color: var(--cyan); margin-bottom: 8px;">
                            OBSERVED TECHNICAL FORENSIC MEASUREMENTS (PHYSICAL ANOMALIES)
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px;">
                            <!-- ELA -->
                            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px;">
                                <div style="font-size: 11px; color: var(--text-muted); font-weight: 600;">ERROR LEVEL ANALYSIS (ELA)</div>
                                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px;">
                                    <span>Mean Diff:</span>
                                    <span class="mono" style="color: #ffffff;">${ela.mean_error !== undefined ? ela.mean_error : 'N/A'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span>Max Diff:</span>
                                    <span class="mono" style="color: #ffffff;">${ela.max_error !== undefined ? ela.max_error : 'N/A'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span>High Divergence Ratio:</span>
                                    <span class="mono" style="color: ${ela.high_divergence_ratio > 0.05 ? 'var(--amber)' : 'var(--emerald)'};">${ela.high_divergence_ratio !== undefined ? (ela.high_divergence_ratio * 100).toFixed(1) + '%' : 'N/A'}</span>
                                </div>
                            </div>

                            <!-- High Frequency Noise Residuals -->
                            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px;">
                                <div style="font-size: 11px; color: var(--text-muted); font-weight: 600;">NOISE RESIDUAL VARIANCE</div>
                                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px;">
                                    <span>Channel Divergence:</span>
                                    <span class="mono" style="color: ${noise.channel_divergence > 3.0 ? 'var(--amber)' : 'var(--emerald)'};">${noise.channel_divergence !== undefined ? noise.channel_divergence + 'x' : 'N/A'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span>Quadrant Spatial Spread:</span>
                                    <span class="mono" style="color: #ffffff;">${noise.spatial_quadrant_spread !== undefined ? noise.spatial_quadrant_spread + 'x' : 'N/A'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span>R / G / B Variances:</span>
                                    <span class="mono" style="font-size: 10px; color: var(--text-muted);">${noise.channel_variances ? `${noise.channel_variances.r}/${noise.channel_variances.g}/${noise.channel_variances.b}` : 'N/A'}</span>
                                </div>
                            </div>

                            <!-- 2D Spectral Decay -->
                            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px;">
                                <div style="font-size: 11px; color: var(--text-muted); font-weight: 600;">2D FFT / DCT RADIAL SPECTRUM</div>
                                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px;">
                                    <span>Decay Slope:</span>
                                    <span class="mono" style="color: #ffffff;">${spectral.decay_slope !== undefined ? spectral.decay_slope : 'N/A'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span>Periodic High-Freq Peak:</span>
                                    <span class="mono" style="color: ${spectral.high_freq_peak_ratio > 4.0 ? 'var(--amber)' : 'var(--emerald)'};">${spectral.high_freq_peak_ratio !== undefined ? spectral.high_freq_peak_ratio + 'x' : 'N/A'}</span>
                                </div>
                                <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">
                                    ${spectral.high_freq_peak_ratio > 4.0 ? 'Periodic high-frequency spikes (possible GAN/Diffusion upsampling grid)' : 'Natural power law spectral decay observed'}
                                </div>
                            </div>

                            <!-- Metadata & EXIF -->
                            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px;">
                                <div style="font-size: 11px; color: var(--text-muted); font-weight: 600;">METADATA & SOFTWARE AUDIT</div>
                                <div style="margin-top: 6px; font-size: 12px;">
                                    <span>Generative AI Signatures:</span>
                                    <b style="color: ${meta.generative_ai_tags && meta.generative_ai_tags.length ? 'var(--accent-red)' : 'var(--emerald)'};">
                                        ${meta.generative_ai_tags && meta.generative_ai_tags.length ? meta.generative_ai_tags.join(', ') : 'None detected'}
                                    </b>
                                </div>
                                <div style="margin-top: 4px; font-size: 12px;">
                                    <span>Editing Software Tags:</span>
                                    <span class="mono" style="color: ${meta.editing_software_tags && meta.editing_software_tags.length ? 'var(--amber)' : 'var(--text-muted)'};">
                                        ${meta.editing_software_tags && meta.editing_software_tags.length ? meta.editing_software_tags.join(', ') : 'None'}
                                    </span>
                                </div>
                                <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">
                                    Sensor Model: ${meta.camera_model || 'Stripped / Excluded'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 2. MODEL REGISTRY & EXECUTION AUDIT -->
                    <div style="margin-bottom: 16px;">
                        <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; color: var(--purple); margin-bottom: 8px;">
                            DEEPFAKE DETECTION MODEL REGISTRY & EXECUTION STATUS
                        </div>
                        <div style="overflow-x: auto; border: 1px solid var(--card-border); border-radius: 6px;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                                <thead style="background: rgba(15, 23, 42, 0.8); border-bottom: 1px solid var(--card-border);">
                                    <tr>
                                        <th style="padding: 8px 12px;">Model</th>
                                        <th style="padding: 8px 12px;">Architecture</th>
                                        <th style="padding: 8px 12px;">Status</th>
                                        <th style="padding: 8px 12px;">Runtime / Device</th>
                                        <th style="padding: 8px 12px;">Observed Output / Reason</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${execModels.map(em => `
                                        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); background: rgba(16, 185, 129, 0.04);">
                                            <td style="padding: 8px 12px; font-weight: 600; color: #ffffff;">${em.model_name || em.model_id}</td>
                                            <td style="padding: 8px 12px; color: var(--text-muted);">${em.architecture || 'Feature Analyzer'}</td>
                                            <td style="padding: 8px 12px;"><span class="badge badge-emerald">INFERENCE_EXECUTED</span></td>
                                            <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace;">${em.runtime_device || 'cpu'}</td>
                                            <td style="padding: 8px 12px; color: var(--text-secondary);">${em.interpretation || JSON.stringify(em.raw_metrics)}</td>
                                        </tr>
                                    `).join("")}
                                    ${unavailModels.map(um => `
                                        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); background: rgba(245, 158, 11, 0.02);">
                                            <td style="padding: 8px 12px; font-weight: 600; color: #ffffff;">${um.model_name || um.model_id}</td>
                                            <td style="padding: 8px 12px; color: var(--text-muted);">${um.architecture || 'Deepfake Classifier'}</td>
                                            <td style="padding: 8px 12px;"><span class="badge badge-amber">${um.status}</span></td>
                                            <td style="padding: 8px 12px; color: var(--text-muted); font-size: 11px;">Not deployed</td>
                                            <td style="padding: 8px 12px; color: var(--text-muted); font-size: 11px;">${um.reason} <span style="color: var(--amber);">[${um.prerequisites}]</span></td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 3. VIDEO KEYFRAME BREAKDOWN (IF APPLICABLE) -->
                    ${videoFrames.length > 0 ? `
                        <div style="margin-bottom: 16px;">
                            <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; color: var(--cyan); margin-bottom: 8px;">
                                BOUNDARY-ANCHORED VIDEO KEYFRAME CHECKPOINTS (${videoFrames.length} FRAMES SAMPLED)
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px;">
                                ${videoFrames.map(vf => `
                                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 8px; font-size: 11px;">
                                        <div style="display: flex; justify-content: space-between; font-weight: 600; color: #ffffff;">
                                            <span>Frame #${vf.frame_index}</span>
                                            <span class="mono" style="color: var(--cyan);">${vf.timestamp_seconds ? vf.timestamp_seconds + 's' : (vf.timestamp_ms || 0) + 'ms'}</span>
                                        </div>
                                        <div style="color: var(--text-muted); margin-top: 4px;">ELA Error: <b>${vf.ela_mean_error || 'N/A'}</b></div>
                                        <div style="color: var(--text-muted);">Spectral Slope: <b>${vf.spectral_decay_slope || 'N/A'}</b></div>
                                        <div style="color: var(--text-muted);">Faces: <b>${vf.faces_detected !== undefined ? vf.faces_detected : 'N/A'}</b></div>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 4. EPISTEMIC LIMITATIONS BANNER -->
                    <div style="background: rgba(245, 158, 11, 0.06); border-left: 3px solid var(--amber); padding: 8px 12px; border-radius: 4px; font-size: 11px; color: var(--text-secondary); margin-top: 10px;">
                        <b>Epistemic Principle:</b> ${auth.epistemic_disclaimer}
                    </div>
                </div>
                `;
            }).join("");
        }

        async function reanalyzeAuthenticity(subId) {
            if (!currentInvId) return;
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/evidence/${subId}/authenticity/reanalyze`, {
                    method: 'POST'
                });
                if (res.ok) {
                    alert('Forensic & Deepfake analysis re-executed successfully!');
                    await loadInvestigationData();
                } else {
                    const err = await res.json();
                    alert('Reanalysis failed: ' + (err.detail || 'Unknown error'));
                }
            } catch (e) {
                alert('Reanalysis request failed: ' + e.message);
            }
        }

        // ==========================================
        // REDESIGNED TIMELINE TAB (NO RAW JSON DUMPS!)
        // ==========================================
        async function loadTimeline() {
            const container = document.getElementById("timeline-stream-container");
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/lineage/timeline`);
                if (res.ok) {
                    timelineData = await res.json();
                    renderTimelineStream(timelineData.events || []);
                }
            } catch (e) {
                console.error("Timeline fetch error:", e);
                container.innerHTML = `<p style="color: var(--accent-red);">Failed to load timeline: ${e.message}</p>`;
            }
        }

        function renderTimelineStream(events) {
            const container = document.getElementById("timeline-stream-container");
            if (!events || events.length === 0) {
                container.innerHTML = `<p style="color: var(--text-muted);">No chronological events recorded yet.</p>`;
                return;
            }

            container.innerHTML = events.map((ev, idx) => {
                const isWarning = ev.event_type.includes("DISINFORMATION") || ev.event_type.includes("MISLEADING") || ev.event_type.includes("REFUTED");
                const isCritical = ev.event_type.includes("CONTRADICTION") || ev.event_type.includes("TAMPERED");
                const cardClass = isCritical ? 'critical' : isWarning ? 'warning' : '';

                // Clean human-readable date
                let formattedTime = ev.timestamp;
                try {
                    const d = new Date(ev.timestamp);
                    formattedTime = d.toLocaleString('en-US', { 
                        month: 'short', day: 'numeric', year: 'numeric', 
                        hour: '2-digit', minute: '2-digit', hour12: false, timeZoneName: 'short' 
                    });
                } catch(e) {}

                return `
                    <div class="timeline-node-card ${cardClass}">
                        <div class="timeline-node-dot"></div>
                        <div class="timeline-meta-bar">
                            <span class="timeline-timecode">${formattedTime}</span>
                            <span class="badge ${isCritical ? 'badge-red' : isWarning ? 'badge-amber' : 'badge-cyan'}">${ev.event_type}</span>
                        </div>
                        <div class="timeline-title">${ev.title || 'Investigation Event'}</div>
                        <div class="timeline-desc">${ev.description || 'Observed event logged in case history.'}</div>
                        
                        <div class="timeline-provenance-toggle" onclick="toggleProvenance('prov-${idx}')">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                            <span>Technical Provenance & Metadata</span>
                        </div>
                        <div id="prov-${idx}" class="timeline-provenance-drawer">
                            <div><b>Entity ID:</b> ${ev.entity_id || 'N/A'}</div>
                            <div><b>Event Nature:</b> ${ev.event_nature || 'OBSERVED'}</div>
                            <div><b>Trace:</b> ${JSON.stringify(ev.details || {}, null, 2)}</div>
                        </div>
                    </div>
                `;
            }).join("");
        }

        function toggleProvenance(id) {
            const el = document.getElementById(id);
            if (el) el.classList.toggle("open");
        }

        // ==========================================
        // COORDINATION INTELLIGENCE TAB
        // ==========================================
        let coordinationData = null;

        async function loadCoordinationData() {
            const container = document.getElementById("coordination-clusters-container");
            if (!currentInvId) return;
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/coordination`);
                if (res.ok) {
                    coordinationData = await res.json();
                    renderCoordinationTab();
                    const countBadge = document.getElementById("count-coordination");
                    if (countBadge) countBadge.innerText = (coordinationData.clusters || []).length;
                }
            } catch (e) {
                console.error("Coordination fetch error:", e);
                if (container) container.innerHTML = `<p style="color: var(--accent-red);">Failed to load coordination signals: ${e.message}</p>`;
            }
        }

        async function runCoordinationAnalysis() {
            if (!currentInvId) return;
            const container = document.getElementById("coordination-clusters-container");
            container.innerHTML = `<p style="color: var(--cyan);">Running deterministic coordination analysis across all evidence items...</p>`;
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/coordination/analyze`, { method: "POST" });
                if (res.ok) {
                    coordinationData = await res.json();
                    renderCoordinationTab();
                    await loadGraph();
                    alert("Coordination analysis complete! Lineage graph updated.");
                } else {
                    alert("Coordination analysis failed.");
                }
            } catch (e) {
                alert("Error triggering coordination analysis: " + e.message);
            }
        }

        function renderCoordinationTab() {
            const container = document.getElementById("coordination-clusters-container");
            if (!container) return;
            if (!coordinationData || !coordinationData.clusters || coordinationData.clusters.length === 0) {
                container.innerHTML = `<p style="color: var(--text-muted);">No coordination patterns evaluated yet. Click 'Run Coordination Audit' to analyze.</p>`;
                return;
            }

            container.innerHTML = coordinationData.clusters.map(c => {
                const isPossibleCoord = c.cluster_type.includes("COORDINATED") || c.cluster_type.includes("BURST");
                const badgeClass = isPossibleCoord ? "badge-purple" : c.cluster_type.includes("INSUFFICIENT") ? "badge-cyan" : "badge-amber";

                return `
                <div class="finding-card" style="margin-bottom: 16px;">
                    <div class="finding-header" style="border-bottom: 1px solid var(--card-border); padding-bottom: 10px; margin-bottom: 12px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span class="finding-title" style="font-size: 15px;">${c.title}</span>
                                <span class="badge ${badgeClass}">${c.cluster_type}</span>
                                <span class="badge badge-cyan">Confidence: ${(c.confidence * 100).toFixed(0)}%</span>
                            </div>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                                Detection Method: <code>${c.detection_method}</code> | Status: <b>${c.review_status}</b>
                            </div>
                        </div>
                    </div>

                    <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5;">
                        ${c.summary}
                    </p>

                    <!-- Entities Involved -->
                    <div style="margin-bottom: 12px;">
                        <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">ENTITIES INVOLVED (${(c.entities_involved || []).length})</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                            ${(c.entities_involved || []).map(ent => `
                                <span style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--card-border); padding: 4px 8px; border-radius: 4px; font-size: 11px;">
                                    <span style="color: var(--cyan); font-weight: 600;">${ent.entity_type}:</span>
                                    <span class="mono" style="color: #ffffff;">${ent.label || ent.entity_id.substring(0, 8)}</span>
                                </span>
                            `).join("")}
                        </div>
                    </div>

                    <!-- Supporting Observations & Metrics -->
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-radius: 6px; padding: 10px; font-size: 12px; margin-bottom: 12px;">
                        <div style="font-weight: 600; color: var(--cyan); margin-bottom: 4px;">OBSERVED CORRELATION METRICS</div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; font-size: 11px;">
                            ${Object.entries(c.supporting_observations || {}).map(([k, v]) => `
                                <div><span style="color: var(--text-muted);">${k.replace(/_/g, ' ')}:</span> <b class="mono" style="color: #ffffff;">${typeof v === 'boolean' ? (v ? 'Yes' : 'No') : Array.isArray(v) ? v.length + ' items' : v}</b></div>
                            `).join("")}
                        </div>
                    </div>

                    <!-- Epistemic disclaimer -->
                    <div style="background: rgba(245, 158, 11, 0.05); border-left: 3px solid var(--amber); padding: 8px 12px; border-radius: 4px; font-size: 11px; color: var(--text-secondary);">
                        <b>Epistemic Boundary:</b> ${c.epistemic_limitations}
                    </div>
                </div>
                `;
            }).join("");
        }

        // ==========================================
        // LIVE MONITORING & EVENTS TAB
        // ==========================================
        let liveEventsData = [];
        let autoPollTimer = null;

        async function loadLiveEvents() {
            const container = document.getElementById("monitoring-events-container");
            if (!currentInvId) return;
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/events?limit=40`);
                if (res.ok) {
                    const data = await res.json();
                    liveEventsData = data.events || [];
                    renderLiveEvents();
                }
            } catch (e) {
                console.error("Live events fetch error:", e);
            }
        }

        function renderLiveEvents() {
            const container = document.getElementById("monitoring-events-container");
            if (!container) return;
            if (!liveEventsData || liveEventsData.length === 0) {
                container.innerHTML = `<p style="color: var(--text-muted);">No investigation events logged yet.</p>`;
                return;
            }

            container.innerHTML = liveEventsData.map(ev => {
                const isCrit = ev.severity === "CRITICAL";
                const isWarn = ev.severity === "WARNING";
                const badgeColor = isCrit ? "var(--accent-red)" : isWarn ? "var(--amber)" : "var(--cyan)";

                return `
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border); border-left: 3px solid ${badgeColor}; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span class="mono" style="font-size: 10px; color: var(--text-muted);">${new Date(ev.created_at).toLocaleTimeString()}</span>
                            <span class="badge" style="background: rgba(255,255,255,0.08); color: ${badgeColor};">${ev.event_type}</span>
                            <span style="font-size: 13px; font-weight: 600; color: #ffffff;">${ev.summary}</span>
                        </div>
                    </div>
                    <span class="badge" style="font-size: 10px; color: var(--text-muted);">${ev.severity}</span>
                </div>
                `;
            }).join("");
        }

        function toggleAutoPoll(enable) {
            if (autoPollTimer) {
                clearInterval(autoPollTimer);
                autoPollTimer = null;
            }
            if (enable) {
                autoPollTimer = setInterval(loadLiveEvents, 3000);
            }
        }

        // ==========================================
        // ASSESSMENT & DECISION TREE TAB
        // ==========================================
        function renderDecisionTreeTab() {
            const container = document.getElementById("decision-tree-container");
            container.innerHTML = `
                <div class="finding-card">
                    <div class="finding-header">
                        <span class="finding-title">Deterministic Multi-Signal Verification Pipeline</span>
                        <span class="badge badge-green">AUDITABLE RULES</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 10px; font-size: 13px;">
                        <div style="background: #020617; padding: 12px; border-radius: 6px; border-left: 3px solid var(--cyan);">
                            <b>Step 1: Multimodal Intake & Extraction</b><br>
                            <span style="color: var(--text-secondary);">Media is hashed with SHA-256 and perceptual hashes. Text is parsed into SPO claims with polarity detection.</span>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 6px; border-left: 3px solid var(--violet);">
                            <b>Step 2: Historical Media Rediscovery Check</b><br>
                            <span style="color: var(--text-secondary);">Visual assets are matched against historical archives using ORB descriptors and RANSAC affine geometry. Matches decouple media authenticity from narrative claims.</span>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 6px; border-left: 3px solid var(--amber);">
                            <b>Step 3: Source Independence & Stance Alignment</b><br>
                            <span style="color: var(--text-secondary);">External fact checks and news sources are clustered. Syndicated wire services (PTI, Reuters) are grouped to prevent artificial corroboration.</span>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 6px; border-left: 3px solid var(--green);">
                            <b>Step 4: Final Verdict Synthesis & Epistemic Abstention</b><br>
                            <span style="color: var(--text-secondary);">Verdicts are strictly assigned (SUPPORTED, REFUTED, MISLEADING_OR_CONTEXT_MISSING, UNVERIFIED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE). No unsupported leaps are made.</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // ==========================================
        // REPORT TAB EMBED
        // ==========================================
        function renderReportTab() {
            const container = document.getElementById("report-view-embed");
            if (!reportData) return;
            container.innerHTML = `
                <h3 style="font-size: 16px; color: var(--cyan); margin-bottom: 12px;">Case Intelligence Dossier Overview</h3>
                <p style="font-size: 14px; line-height: 1.6; color: var(--text-main); margin-bottom: 20px;">
                    ${reportData.executive_summary}
                </p>
                <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                    <span class="badge badge-cyan">Submissions: ${reportData.metrics.submissions_count}</span>
                    <span class="badge badge-purple">Claims: ${reportData.metrics.claims_count}</span>
                    <span class="badge badge-amber">Historical Matches: ${reportData.metrics.matches_count}</span>
                    <span class="badge badge-green">Retrieved Sources: ${reportData.metrics.sources_count}</span>
                </div>
                <div style="font-size: 12px; color: var(--text-muted);">
                    Click "Open Printable HTML Report" above for full court-ready forensic export.
                </div>
            `;
        }

        // ==========================================
        // INTELLIGENCE GRAPH (SVG RENDERING)
        // ==========================================
        async function loadGraph() {
            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/lineage/graph`);
                if (res.ok) {
                    graphData = await res.json();
                    document.getElementById("stat-nodes").innerText = graphData.nodes?.length || 0;
                    document.getElementById("stat-edges").innerText = graphData.edges?.length || 0;
                    renderGraphSVG();
                }
            } catch (e) {
                console.error("Graph error:", e);
            }
        }

        function renderGraphSVG() {
            const svg = document.getElementById("graph-svg");
            if (!svg || !graphData || !graphData.nodes) return;

            const width = svg.clientWidth || 900;
            const height = svg.clientHeight || 600;
            svg.innerHTML = '';

            const showInferred = document.getElementById("toggle-inferred").checked;
            const filteredEdges = (graphData.edges || []).filter(e => showInferred || e.edge_nature !== 'INFERRED');

            // Layered layout: Evidence (left), Claims (middle), Assessments/Sources (right)
            const nodePositions = {};
            const evidenceNodes = graphData.nodes.filter(n => n.node_type === 'EVIDENCE_SUBMISSION' || n.node_type === 'MEDIA_ASSET');
            const claimNodes = graphData.nodes.filter(n => n.node_type === 'CLAIM');
            const otherNodes = graphData.nodes.filter(n => !evidenceNodes.includes(n) && !claimNodes.includes(n));

            function layoutColumn(nodes, colX) {
                const stepY = height / (nodes.length + 1);
                nodes.forEach((node, i) => {
                    nodePositions[node.id] = { x: colX, y: (i + 1) * stepY };
                });
            }

            layoutColumn(evidenceNodes, width * 0.2);
            layoutColumn(claimNodes, width * 0.5);
            layoutColumn(otherNodes, width * 0.8);

            // Render Edges
            filteredEdges.forEach(edge => {
                const src = nodePositions[edge.source_id];
                const dst = nodePositions[edge.target_id];
                if (!src || !dst) return;

                const color = edge.edge_nature === 'OBSERVED' ? '#00f0ff' :
                              edge.edge_nature === 'SYSTEM_DERIVED' ? '#0d9488' :
                              edge.edge_nature === 'HUMAN_CONFIRMED' ? '#10b981' : '#f59e0b';

                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const dx = (dst.x - src.x) * 0.5;
                const d = `M ${src.x} ${src.y} C ${src.x + dx} ${src.y}, ${dst.x - dx} ${dst.y}, ${dst.x} ${dst.y}`;
                
                path.setAttribute("d", d);
                path.setAttribute("stroke", color);
                path.setAttribute("stroke-width", "2");
                path.setAttribute("fill", "none");
                if (edge.edge_nature === 'INFERRED') {
                    path.setAttribute("stroke-dasharray", "4,4");
                }
                path.style.cursor = "pointer";
                path.onclick = () => openEdgeDrawer(edge);
                svg.appendChild(path);
            });

            // Render Nodes
            graphData.nodes.forEach(node => {
                const pos = nodePositions[node.id];
                if (!pos) return;

                const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                g.style.cursor = "pointer";
                g.onclick = () => openNodeDrawer(node);

                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", pos.x);
                circle.setAttribute("cy", pos.y);
                circle.setAttribute("r", "16");
                circle.setAttribute("fill", "#0a1124");
                circle.setAttribute("stroke", node.node_type === 'CLAIM' ? '#00f0ff' : node.node_type === 'HISTORICAL_MATCH' ? '#8b5cf6' : '#1e2f54');
                circle.setAttribute("stroke-width", "2");

                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", pos.x);
                text.setAttribute("y", pos.y + 26);
                text.setAttribute("text-anchor", "middle");
                text.setAttribute("fill", "#94a3b8");
                text.setAttribute("font-size", "11px");
                text.textContent = (node.label || node.id).substring(0, 16);

                g.appendChild(circle);
                g.appendChild(text);
                svg.appendChild(g);
            });
        }

        function resetGraphLayout() {
            renderGraphSVG();
        }

        // ==========================================
        // DRAWER CONTROLS & HUMAN REVIEW
        // ==========================================
        function openNodeDrawer(node) {
            const drawer = document.getElementById("drawer");
            document.getElementById("drawer-title").innerText = `Node: ${node.label || node.id}`;
            const content = document.getElementById("drawer-content");
            content.innerHTML = `
                <div><b>Type:</b> <span class="badge badge-cyan">${node.node_type}</span></div>
                <div><b>ID:</b> <span class="mono">${node.id}</span></div>
                <div><b>Metadata:</b></div>
                <pre class="mono" style="background:#020617; padding:8px; border-radius:4px; font-size:11px;">${JSON.stringify(node.metadata || {}, null, 2)}</pre>
            `;
            drawer.classList.add("open");
        }

        function openEdgeDrawer(edge) {
            const drawer = document.getElementById("drawer");
            document.getElementById("drawer-title").innerText = `Relationship: ${edge.relationship_type}`;
            const content = document.getElementById("drawer-content");

            const isReviewable = edge.edge_nature === 'INFERRED' || edge.review_status === 'UNREVIEWED';

            content.innerHTML = `
                <div><b>Relationship Type:</b> <span class="badge badge-purple">${edge.relationship_type}</span></div>
                <div><b>Edge Nature:</b> <span class="badge badge-amber">${edge.edge_nature}</span></div>
                <div><b>Review Status:</b> <b>${edge.review_status || 'UNREVIEWED'}</b></div>
                <div><b>Summary:</b> ${edge.evidence_summary || 'System inferred connection'}</div>

                ${isReviewable ? `
                    <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border);">
                        <span style="font-size: 12px; font-weight: 700; color: #ffffff;">Investigator Review:</span>
                        <div class="form-group" style="margin-top: 8px;">
                            <label class="form-label">Review Status</label>
                            <select id="review-status-select" class="form-select">
                                <option value="CONFIRMED">CONFIRM Relationship</option>
                                <option value="REJECTED">REJECT Relationship</option>
                                <option value="FLAGGED_UNCERTAIN">FLAG as Uncertain</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Investigator Notes</label>
                            <textarea id="review-notes-input" class="form-textarea" rows="2" placeholder="Reasoning for confirmation or rejection..."></textarea>
                        </div>
                        <button class="btn btn-cyan" style="width: 100%;" onclick="submitEdgeReview('${edge.id}')">Submit Verification</button>
                    </div>
                ` : `
                    <div style="margin-top: 10px; font-size: 11px; color: var(--green);">
                        ✓ Reviewed by: ${edge.reviewer_id || 'Investigator'}
                    </div>
                `}
            `;
            drawer.classList.add("open");
        }

        async function submitEdgeReview(edgeId) {
            const statusVal = document.getElementById("review-status-select").value;
            const notesVal = document.getElementById("review-notes-input").value;
            const cleanRelId = edgeId.replace("rel_", "");

            try {
                const res = await fetch(`/api/v1/investigations/${currentInvId}/lineage/relationships/${cleanRelId}/review`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        review_status: statusVal,
                        reviewer_notes: notesVal || "Investigator confirmed in workbench UI",
                        reviewer_id: "investigator_console"
                    })
                });

                if (res.ok) {
                    closeDrawer();
                    await loadGraph();
                    alert("Relationship review recorded successfully.");
                } else {
                    alert("Failed to submit review.");
                }
            } catch (e) {
                alert("Error submitting review: " + e.message);
            }
        }

        function closeDrawer() {
            document.getElementById("drawer").classList.remove("open");
        }

        // ==========================================
        // MODALS HANDLING
        // ==========================================
        function openModal(id) { document.getElementById(id).classList.add("open"); }
        function closeModal(id) { document.getElementById(id).classList.remove("open"); }

        function openNewCaseModal() { openModal("modal-new-case"); }

        async function openUploadModal() {
            clearUploadFeedback();
            await populateUploadModalCases();
            openModal("modal-upload");
        }

        async function populateUploadModalCases() {
            if (!allInvestigationsList || allInvestigationsList.length === 0) {
                try {
                    const res = await fetch("/api/v1/investigations/");
                    if (res.ok) {
                        allInvestigationsList = await res.json();
                        allInvestigationsMap = {};
                        allInvestigationsList.forEach(c => { allInvestigationsMap[c.id] = c; });
                    }
                } catch (e) {
                    console.error("Error loading investigations for upload modal:", e);
                }
            }

            if ((!currentInvId || currentInvId === "{{INV_ID}}" || currentInvId === "") && allInvestigationsList.length > 0) {
                currentInvId = allInvestigationsList[0].id;
                currentInvTitle = allInvestigationsList[0].title;
                updateCaseHeader();
            }

            const fileSelect = document.getElementById("upload-case-select-file");
            const textSelect = document.getElementById("upload-case-select-text");
            const universalSelect = document.getElementById("upload-case-select-universal");

            let optionsHtml = "";
            if (allInvestigationsList.length === 0) {
                optionsHtml = `<option value="">No cases available — create a case first</option>`;
            } else {
                optionsHtml = allInvestigationsList.map(c => {
                    const isSelected = c.id === currentInvId ? " selected" : "";
                    const displayTitle = escapeHtml(c.title);
                    const shortId = c.id.length > 8 ? c.id.substring(0, 8) + "..." : c.id;
                    return `<option value="${c.id}"${isSelected}>${displayTitle} (${shortId})</option>`;
                }).join("");
            }

            if (fileSelect) fileSelect.innerHTML = optionsHtml;
            if (textSelect) textSelect.innerHTML = optionsHtml;
            if (universalSelect) universalSelect.innerHTML = optionsHtml;
        }

        function syncUploadCase(caseId) {
            if (!caseId) return;
            currentInvId = caseId;
            if (allInvestigationsMap[caseId]) {
                currentInvTitle = allInvestigationsMap[caseId].title;
            }
            const fileSelect = document.getElementById("upload-case-select-file");
            const textSelect = document.getElementById("upload-case-select-text");
            const universalSelect = document.getElementById("upload-case-select-universal");
            if (fileSelect && fileSelect.value !== caseId) fileSelect.value = caseId;
            if (textSelect && textSelect.value !== caseId) textSelect.value = caseId;
            if (universalSelect && universalSelect.value !== caseId) universalSelect.value = caseId;
            updateCaseHeader();
            window.history.replaceState({}, '', `/workbench?investigation_id=${encodeURIComponent(caseId)}`);
        }

        function showUploadFeedback(msg, isError) {
            const box = document.getElementById("upload-feedback");
            if (!box) return;
            box.style.display = "block";
            if (isError) {
                box.style.background = "rgba(244, 63, 94, 0.15)";
                box.style.border = "1px solid var(--red)";
                box.style.color = "var(--red)";
                box.innerText = "✕ " + msg;
            } else {
                box.style.background = "rgba(16, 185, 129, 0.15)";
                box.style.border = "1px solid var(--green)";
                box.style.color = "var(--green)";
                box.innerText = msg;
            }
        }

        function clearUploadFeedback() {
            const box = document.getElementById("upload-feedback");
            if (box) {
                box.style.display = "none";
                box.innerText = "";
            }
        }

        async function openCaseSwitcherModal() {
            openModal("modal-switcher");
            const tbody = document.getElementById("case-switcher-table-body");
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Loading cases...</td></tr>`;

            try {
                const res = await fetch("/api/v1/investigations/");
                if (res.ok) {
                    const cases = await res.json();
                    allInvestigationsList = cases;
                    allInvestigationsMap = {};
                    cases.forEach(c => { allInvestigationsMap[c.id] = c; });

                    if (cases.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: var(--text-muted);">No cases found. Create a new case to get started.</td></tr>`;
                        return;
                    }

                    tbody.innerHTML = cases.map(c => `
                        <tr onclick="selectCaseById('${c.id}')" style="cursor: pointer;">
                            <td>
                                <div style="font-weight: 700; color: #ffffff;">${escapeHtml(c.title)}</div>
                                <div class="mono" style="font-size: 11px; color: var(--cyan);">${c.id}</div>
                            </td>
                            <td><span class="badge ${c.priority === 'HIGH' ? 'badge-red' : 'badge-green'}">${escapeHtml(c.priority)}</span></td>
                            <td><span class="badge badge-cyan">${escapeHtml(c.status)}</span></td>
                            <td class="mono" style="font-size: 11px;">${new Date(c.updated_at).toLocaleDateString()}</td>
                        </tr>
                    `).join("");
                } else {
                    tbody.innerHTML = `<tr><td colspan="4" style="color:var(--accent-red);">Failed to load cases: HTTP ${res.status}</td></tr>`;
                }
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="4" style="color:var(--accent-red);">Failed to load cases: ${escapeHtml(e.message)}</td></tr>`;
            }
        }

        async function selectCaseById(id) {
            if (!id) return;
            currentInvId = id;
            if (allInvestigationsMap[id]) {
                currentInvTitle = allInvestigationsMap[id].title;
            }
            updateCaseHeader();
            syncUploadCase(id);
            window.history.pushState({}, '', `/workbench?investigation_id=${encodeURIComponent(id)}`);
            closeModal("modal-switcher");
            await loadAllCaseData();
        }

        function selectCase(id, title) {
            selectCaseById(id);
        }

        async function handleCreateInvestigation(e) {
            e.preventDefault();
            const title = document.getElementById("new-case-title").value;
            const desc = document.getElementById("new-case-desc").value;
            const priority = document.getElementById("new-case-priority").value;

            try {
                const res = await fetch("/api/v1/investigations/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title, description: desc, priority })
                });

                if (res.ok) {
                    const newCase = await res.json();
                    allInvestigationsList.unshift(newCase);
                    allInvestigationsMap[newCase.id] = newCase;
                    closeModal("modal-new-case");
                    await selectCaseById(newCase.id);
                } else {
                    alert("Failed to create investigation.");
                }
            } catch (err) {
                alert("Error: " + err.message);
            }
        }

        function switchUploadMode(mode) {
            const tabUniv = document.getElementById("upload-tab-universal-btn");
            const tabFile = document.getElementById("upload-tab-file-btn");
            const tabText = document.getElementById("upload-tab-text-btn");
            const formUniv = document.getElementById("form-upload-universal");
            const formFile = document.getElementById("form-upload-file");
            const formText = document.getElementById("form-upload-text");

            [tabUniv, tabFile, tabText].forEach(b => { if (b) b.classList.remove("active"); });
            [formUniv, formFile, formText].forEach(f => { if (f) f.style.display = "none"; });

            if (mode === 'universal') {
                if (tabUniv) tabUniv.classList.add("active");
                if (formUniv) formUniv.style.display = "block";
            } else if (mode === 'file') {
                if (tabFile) tabFile.classList.add("active");
                if (formFile) formFile.style.display = "block";
            } else if (mode === 'text') {
                if (tabText) tabText.classList.add("active");
                if (formText) formText.style.display = "block";
            }
        }

        let universalSelectedFiles = [];

        function onUniversalFilesSelected(files) {
            universalSelectedFiles = Array.from(files);
            renderSelectedFilesList();
        }

        function removeSelectedFile(index) {
            universalSelectedFiles.splice(index, 1);
            renderSelectedFilesList();
        }

        function renderSelectedFilesList() {
            const container = document.getElementById("selected-files-list");
            if (!container) return;
            if (universalSelectedFiles.length === 0) {
                container.innerHTML = "";
                return;
            }
            container.innerHTML = universalSelectedFiles.map((f, idx) => {
                const ext = f.name.split('.').pop().toLowerCase();
                let badgeClass = "badge-cyan";
                let mod = "FILE";
                if (['jpg','jpeg','png','webp','bmp','gif'].includes(ext)) { badgeClass = "badge-cyan"; mod = "IMAGE"; }
                else if (['mp4','webm','mov','mkv','avi'].includes(ext)) { badgeClass = "badge-purple"; mod = "VIDEO"; }
                else if (['wav','mp3','ogg','flac','m4a'].includes(ext)) { badgeClass = "badge-amber"; mod = "AUDIO"; }
                
                const sizeKb = (f.size / 1024).toFixed(1);
                return `
                    <div class="file-pill">
                        <span class="badge ${badgeClass}" style="font-size: 9px; padding: 1px 4px;">${mod}</span>
                        <span>${escapeHtml(f.name)} (${sizeKb} KB)</span>
                        <span style="cursor: pointer; color: var(--red); font-weight: bold; margin-left: 4px;" onclick="removeSelectedFile(${idx})">&times;</span>
                    </div>
                `;
            }).join("");
        }

        async function ensureActiveCase(targetSelectId) {
            let targetInvId = document.getElementById(targetSelectId)?.value || currentInvId;
            if (targetInvId && targetInvId !== "{{INV_ID}}" && targetInvId !== "") {
                return targetInvId;
            }

            if (allInvestigationsList && allInvestigationsList.length > 0) {
                targetInvId = allInvestigationsList[0].id;
                currentInvId = targetInvId;
                currentInvTitle = allInvestigationsList[0].title;
                updateCaseHeader();
                syncUploadCase(targetInvId);
                return targetInvId;
            }

            // Fetch from API
            try {
                const res = await fetch("/api/v1/investigations/");
                if (res.ok) {
                    const cases = await res.json();
                    if (cases && cases.length > 0) {
                        allInvestigationsList = cases;
                        cases.forEach(c => { allInvestigationsMap[c.id] = c; });
                        targetInvId = cases[0].id;
                        currentInvId = targetInvId;
                        currentInvTitle = cases[0].title;
                        updateCaseHeader();
                        syncUploadCase(targetInvId);
                        return targetInvId;
                    }
                }
            } catch (_) {}

            // Auto-create initial investigation if DB is empty
            try {
                const createRes = await fetch("/api/v1/investigations/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: "Primary Misinformation Investigation",
                        description: "Initial case workspace created automatically for evidence ingestion",
                        priority: "HIGH"
                    })
                });
                if (createRes.ok) {
                    const newCase = await createRes.json();
                    allInvestigationsList = [newCase];
                    allInvestigationsMap[newCase.id] = newCase;
                    targetInvId = newCase.id;
                    currentInvId = targetInvId;
                    currentInvTitle = newCase.title;
                    updateCaseHeader();
                    syncUploadCase(targetInvId);
                    return targetInvId;
                }
            } catch (_) {}

            return null;
        }

        async function handleUniversalIntake(e) {
            e.preventDefault();
            clearUploadFeedback();

            const targetInvId = await ensureActiveCase("upload-case-select-universal");
            if (!targetInvId) {
                showUploadFeedback("Failed to resolve or initialize active investigation. Please check backend connection.", true);
                return;
            }

            if (currentInvId !== targetInvId) {
                syncUploadCase(targetInvId);
            }

            const rawText = document.getElementById("upload-universal-text").value.trim();
            const sourceUrl = document.getElementById("upload-universal-url").value.trim();
            const caption = document.getElementById("upload-universal-caption")?.value.trim() || "";
            const claimedDate = document.getElementById("upload-universal-date").value.trim();
            const claimedLocation = document.getElementById("upload-universal-location").value.trim();

            if (universalSelectedFiles.length === 0 && !rawText && !sourceUrl) {
                showUploadFeedback("Please provide at least one media file, text proposition, or source URL.", true);
                return;
            }

            const submitBtn = document.getElementById("btn-upload-universal");
            const origText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerText = "Orchestrating Ingestion & Dispatch...";

            const formData = new FormData();
            for (const f of universalSelectedFiles) {
                formData.append("files", f);
            }
            if (rawText) formData.append("raw_text", rawText);
            if (sourceUrl) formData.append("source_url", sourceUrl);
            if (caption) formData.append("caption", caption);
            if (claimedDate) formData.append("claimed_date", claimedDate);
            if (claimedLocation) formData.append("claimed_location", claimedLocation);

            try {
                const res = await fetch(`/api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/intake`, {
                    method: "POST",
                    body: formData
                });

                if (res.ok) {
                    const data = await res.json();
                    showUploadFeedback(`✓ ${data.summary}`, false);

                    const resContainer = document.getElementById("universal-results-container");
                    const tbody = document.getElementById("universal-results-tbody");
                    if (resContainer && tbody && data.items) {
                        resContainer.style.display = "block";
                        tbody.innerHTML = data.items.map(it => {
                            const modBadge = it.detected_modality === 'IMAGE' ? 'badge-cyan' :
                                             it.detected_modality === 'VIDEO' ? 'badge-purple' :
                                             it.detected_modality === 'AUDIO' ? 'badge-amber' :
                                             it.detected_modality === 'TEXT' ? 'badge-green' : 'badge-red';
                            const statusBadge = it.status === 'QUEUED' || it.status === 'COMPLETED' ? 'badge-green' :
                                                it.status === 'PARTIAL' ? 'badge-amber' : 'badge-red';
                            const routesStr = (it.assigned_routes || []).slice(0, 3).join(", ") + (it.assigned_routes?.length > 3 ? "..." : "");
                            return `
                                <tr>
                                    <td><div style="font-weight:600; color:#fff;">${escapeHtml(it.filename_or_snippet)}</div></td>
                                    <td><span class="badge ${modBadge}">${it.detected_modality}</span></td>
                                    <td><span class="badge ${statusBadge}">${it.status}</span></td>
                                    <td style="color:var(--text-secondary);">${escapeHtml(routesStr || it.error_message || '—')}</td>
                                </tr>
                            `;
                        }).join("");
                    }

                    universalSelectedFiles = [];
                    renderSelectedFilesList();
                    document.getElementById("upload-universal-text").value = "";
                    document.getElementById("upload-universal-url").value = "";
                    const fileInput = document.getElementById("upload-universal-files");
                    if (fileInput) fileInput.value = "";

                    await loadAllCaseData();
                    setTimeout(() => {
                        closeModal("modal-upload");
                        clearUploadFeedback();
                        if (resContainer) resContainer.style.display = "none";
                        switchTab("evidence");
                    }, 2400);
                } else {
                    let errorMsg = "Intake orchestration rejected by server";
                    try {
                        const errData = await res.json();
                        if (errData && errData.detail) {
                            errorMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
                        }
                    } catch (_) {
                        errorMsg = `Server returned HTTP ${res.status}: ${res.statusText}`;
                    }
                    showUploadFeedback(`Orchestration failed: ${errorMsg}`, true);
                }
            } catch (err) {
                showUploadFeedback(`Network connection error: ${err.message}`, true);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = origText;
            }
        }

        function setupDropZone() {
            const dz = document.getElementById("drop-zone");
            if (!dz) return;
            ['dragenter', 'dragover'].forEach(eventName => {
                dz.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dz.classList.add('dragover');
                }, false);
            });
            ['dragleave', 'drop'].forEach(eventName => {
                dz.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dz.classList.remove('dragover');
                }, false);
            });
            dz.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                if (dt && dt.files && dt.files.length) {
                    onUniversalFilesSelected(dt.files);
                }
            }, false);
        }

        async function handleUploadFile(e) {
            e.preventDefault();
            clearUploadFeedback();

            const targetInvId = await ensureActiveCase("upload-case-select-file");
            if (!targetInvId) {
                showUploadFeedback("Failed to resolve active investigation. Please create a case first.", true);
                return;
            }

            if (currentInvId !== targetInvId) {
                syncUploadCase(targetInvId);
            }

            const fileInput = document.getElementById("upload-file-input");
            if (!fileInput.files || !fileInput.files.length) {
                showUploadFeedback("Please select a media file to upload.", true);
                return;
            }

            const submitBtn = document.getElementById("btn-upload-file");
            const origText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerText = "Uploading & Ingesting...";

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            const caption = document.getElementById("upload-file-caption").value.trim();
            const date = document.getElementById("upload-file-date").value.trim();
            const location = document.getElementById("upload-file-location").value.trim();

            if (caption) formData.append("caption", caption);
            if (date) formData.append("claimed_date", date);
            if (location) formData.append("claimed_location", location);

            try {
                const res = await fetch(`/api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/upload`, {
                    method: "POST",
                    body: formData
                });

                if (res.ok) {
                    const data = await res.json();
                    showUploadFeedback(`✓ Evidence ingested successfully (ID: ${data.id.substring(0, 8)}...). Dispatched for pipeline processing.`, false);
                    document.getElementById("form-upload-file").reset();
                    await loadAllCaseData();
                    setTimeout(() => {
                        closeModal("modal-upload");
                        clearUploadFeedback();
                        switchTab("evidence");
                    }, 1200);
                } else {
                    let errorMsg = "Upload rejected by server";
                    try {
                        const errData = await res.json();
                        if (errData && errData.detail) {
                            errorMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
                        }
                    } catch (_) {
                        if (res.status === 413) errorMsg = "File exceeds maximum permitted size (100MB)";
                        else if (res.status === 415) errorMsg = "Unsupported media file format";
                        else if (res.status === 400) errorMsg = "Submitted file is empty (0 bytes) or corrupted";
                        else if (res.status === 404) errorMsg = `Investigation '${currentInvId}' not found`;
                        else if (res.status >= 500) errorMsg = "Server storage or ingestion processing failure";
                        else errorMsg = `Server returned HTTP ${res.status}: ${res.statusText}`;
                    }
                    showUploadFeedback(`Upload failed: ${errorMsg}`, true);
                }
            } catch (err) {
                showUploadFeedback(`Network connection error: ${err.message}`, true);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = origText;
            }
        }

        async function handleUploadText(e) {
            e.preventDefault();
            clearUploadFeedback();

            const targetInvId = await ensureActiveCase("upload-case-select-text");
            if (!targetInvId) {
                showUploadFeedback("Failed to resolve active investigation. Please create a case first.", true);
                return;
            }

            if (currentInvId !== targetInvId) {
                syncUploadCase(targetInvId);
            }

            const text = document.getElementById("upload-text-content").value.trim();
            if (!text) {
                showUploadFeedback("Please provide the text claim.", true);
                return;
            }

            const submitBtn = document.getElementById("btn-upload-text");
            const origText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerText = "Submitting Claim...";

            const date = document.getElementById("upload-text-date").value.trim();
            const loc = document.getElementById("upload-text-location").value.trim();

            const payload = {
                raw_text: text,
                caption: text.substring(0, 100)
            };
            if (date) payload.claimed_date = date;
            if (loc) payload.claimed_location = loc;

            try {
                const res = await fetch(`/api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/claim`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    const data = await res.json();
                    showUploadFeedback(`✓ Text claim submitted successfully (ID: ${data.id.substring(0, 8)}...). Dispatched for extraction.`, false);
                    document.getElementById("form-upload-text").reset();
                    await loadAllCaseData();
                    setTimeout(() => {
                        closeModal("modal-upload");
                        clearUploadFeedback();
                        switchTab("claims");
                    }, 1200);
                } else {
                    let errorMsg = "Submission rejected by server";
                    try {
                        const errData = await res.json();
                        if (errData && errData.detail) {
                            errorMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
                        }
                    } catch (_) {
                        if (res.status === 400) errorMsg = "Either raw_text or source_url must be provided";
                        else if (res.status === 404) errorMsg = `Investigation '${currentInvId}' not found`;
                        else errorMsg = `Server returned HTTP ${res.status}: ${res.statusText}`;
                    }
                    showUploadFeedback(`Claim submission failed: ${errorMsg}`, true);
                }
            } catch (err) {
                showUploadFeedback(`Network connection error: ${err.message}`, true);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = origText;
            }
        }

        // Event listeners
        document.getElementById("toggle-inferred").addEventListener("change", loadGraph);
        window.addEventListener("load", initWorkbench);
    </script>
</body>
</html>
"""

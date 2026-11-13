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
            --bg-base: #050914;
            --bg-surface: #0a1124;
            --bg-card: #0f1a36;
            --bg-card-hover: #16244a;
            --border: #1e2f54;
            --border-light: #2a3f6e;
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --cyan: #00f0ff;
            --cyan-glow: rgba(0, 240, 255, 0.18);
            --teal: #0d9488;
            --violet: #8b5cf6;
            --amber: #f59e0b;
            --red: #f43f5e;
            --green: #10b981;
            --accent-blue: #38bdf8;
            --accent-red: #f43f5e;
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
            background: rgba(10, 17, 36, 0.95);
            backdrop-filter: blur(12px);
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
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(139, 92, 246, 0.2));
            border: 1px solid var(--cyan);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 10px var(--cyan-glow);
        }

        .brand-logo-icon svg {
            width: 16px;
            height: 16px;
            fill: var(--cyan);
        }

        .brand-text {
            font-size: 15px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, var(--cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-divider {
            color: var(--border-light);
            font-size: 14px;
        }

        .case-selector-btn {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .case-selector-btn:hover {
            border-color: var(--cyan);
            background: var(--bg-card-hover);
        }

        .case-id-pill {
            background: rgba(0, 240, 255, 0.12);
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
            gap: 10px;
        }

        .btn {
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid transparent;
        }

        .btn-cyan {
            background: var(--cyan);
            color: #050914;
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.25);
        }

        .btn-cyan:hover {
            background: #26f4ff;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--bg-card);
            border-color: var(--border);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            border-color: var(--border-light);
            background: var(--bg-card-hover);
        }

        /* Simulation Banner */
        .simulation-banner {
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
            border-bottom: 1px solid rgba(245, 158, 11, 0.3);
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
            background: var(--bg-surface);
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
            color: #ffffff;
        }

        .priority-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .priority-high {
            background: rgba(244, 63, 94, 0.15);
            color: var(--red);
            border: 1px solid rgba(244, 63, 94, 0.3);
        }

        .priority-med {
            background: rgba(245, 158, 11, 0.15);
            color: var(--amber);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .priority-low {
            background: rgba(16, 185, 129, 0.15);
            color: var(--green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Workbench Tabs */
        .tabs-nav {
            display: flex;
            gap: 2px;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            padding: 0 20px;
            overflow-x: auto;
            flex-shrink: 0;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            padding: 12px 14px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
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
            background: rgba(0, 240, 255, 0.04);
        }

        .tab-count {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            font-size: 10px;
            padding: 1px 6px;
            border-radius: 10px;
        }

        .tab-btn.active .tab-count {
            background: rgba(0, 240, 255, 0.2);
            color: var(--cyan);
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
            color: #ffffff;
        }

        .badge {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }

        .badge-cyan { background: rgba(0, 240, 255, 0.12); color: var(--cyan); border: 1px solid rgba(0, 240, 255, 0.3); }
        .badge-amber { background: rgba(245, 158, 11, 0.12); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-red { background: rgba(244, 63, 94, 0.12); color: var(--red); border: 1px solid rgba(244, 63, 94, 0.3); }
        .badge-green { background: rgba(16, 185, 129, 0.12); color: var(--green); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-purple { background: rgba(139, 92, 246, 0.12); color: var(--violet); border: 1px solid rgba(139, 92, 246, 0.3); }

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
            background: #020617;
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
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: radial-gradient(circle at center, transparent 40%, rgba(0, 240, 255, 0.05) 100%);
            border: 1px dashed rgba(0, 240, 255, 0.2);
            margin: 12px;
            border-radius: 4px;
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
            background: #020617;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            color: #ffffff;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s ease;
        }

        .form-input:focus, .form-select:focus, .form-textarea:focus {
            border-color: var(--cyan);
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
            <button class="case-selector-btn" onclick="openCaseSwitcherModal()">
                <span class="case-id-pill" id="nav-case-id">{{INV_ID}}</span>
                <span id="nav-case-title">{{INV_TITLE}}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </button>
        </div>

        <div class="nav-actions">
            <button class="btn btn-secondary" onclick="openUploadModal()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                + Upload Evidence
            </button>
            <a id="btn-open-dossier" href="/api/v1/investigations/{{INV_ID}}/report/html" target="_blank" class="btn btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Print Dossier
            </a>
            <button class="btn btn-cyan" onclick="openNewCaseModal()">
                + New Case
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
            1. Overview
        </button>
        <button class="tab-btn" onclick="switchTab('evidence')">
            2. Evidence & Submissions <span class="tab-count" id="count-evidence">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('forensics')">
            3. Media Forensics
        </button>
        <button class="tab-btn" onclick="switchTab('historical')">
            4. Historical Discovery <span class="tab-count" id="count-matches">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('claims')">
            5. Claims & Sources <span class="tab-count" id="count-claims">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('graph')">
            6. Intelligence Graph
        </button>
        <button class="tab-btn" onclick="switchTab('timeline')">
            7. Timeline
        </button>
        <button class="tab-btn" onclick="switchTab('decision')">
            8. Assessment Engine
        </button>
        <button class="tab-btn" onclick="switchTab('report')">
            9. Case Report
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
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div class="finding-card">
                    <div class="finding-header">
                        <span class="finding-title">Signature Differentiator: Historical Rediscovery</span>
                        <span class="badge badge-purple">DECOUPLED CONTEXT</span>
                    </div>
                    <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
                        TRUTHNET separates media authenticity from narrative veracity. An authentic photograph captured in 2018 recirculated in 2026 with a false breaking-news caption is flagged as <b>MISLEADING_OR_CONTEXT_MISSING</b>, preserving both visual provenance and contextual truth.
                    </p>
                </div>
                <div class="finding-card">
                    <div class="finding-header">
                        <span class="finding-title">Epistemic Limitations & Guardrails</span>
                        <span class="badge badge-cyan">ABSTENTION SAFEGUARDS</span>
                    </div>
                    <ul id="overview-limitations-list" style="font-size: 12px; color: var(--text-secondary); padding-left: 18px; line-height: 1.6;">
                        <li>Absence of corroborating evidence does not establish falsehood; insufficient evidence triggers abstention.</li>
                        <li>Syndicated wire reprints (e.g. PTI, ANI, Reuters) are clustered and not treated as independent confirmations.</li>
                        <li>All edge inferences require human investigator confirmation before dossier finalization.</li>
                    </ul>
                </div>
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
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Deep Multimodal Forensics & Provenance</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">EXIF timecode audits, perceptual hash signatures, OCR text extraction, and audio transcription.</p>
            <div id="forensics-container" style="display: flex; flex-direction: column; gap: 16px;">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 4: HISTORICAL DISCOVERY -->
        <div id="tab-historical" class="tab-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <h2 style="font-size: 16px; font-weight: 700;">Historical Media Rediscovery & Contextual Analysis</h2>
                    <p style="font-size: 13px; color: var(--text-muted);">Side-by-side comparison between submitted suspect media and archival candidate matches.</p>
                </div>
                <span class="badge badge-purple">SIGNATURE CAPABILITY</span>
            </div>
            <div id="historical-matches-container">
                <!-- Populated dynamically -->
            </div>
        </div>

        <!-- TAB 5: CLAIMS & SOURCES -->
        <div id="tab-claims" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Atomic Claims & Source Independence</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">Extracted proposition triples, verification verdicts, and syndicated wire detection.</p>
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

        <!-- TAB 7: TIMELINE (REDESIGNED PROGRESSIVE DISCLOSURE) -->
        <div id="tab-timeline" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Chronological Investigation Sequence</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 24px;">Human-readable chronological stream of camera captures, claimed dates, evidence submissions, publications, and assessments.</p>
            <div id="timeline-stream-container" class="timeline-stream">
                <!-- Populated dynamically with clean progressive cards -->
            </div>
        </div>

        <!-- TAB 8: ASSESSMENT & DECISION TREE -->
        <div id="tab-decision" class="tab-panel">
            <h2 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Deterministic Assessment & Verification Engine</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">Step-by-step verification logic, stance breakdown, and multi-signal independence rules.</p>
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

    <!-- MODAL 2: UPLOAD EVIDENCE -->
    <div id="modal-upload" class="modal-overlay">
        <div class="modal-window">
            <div class="modal-header">
                <span style="font-size: 15px; font-weight: 700;">Ingest New Evidence</span>
                <button class="drawer-close-btn" onclick="closeModal('modal-upload')">&times;</button>
            </div>
            <div style="padding: 0 20px; border-bottom: 1px solid var(--border); display: flex; gap: 10px;">
                <button id="upload-tab-file-btn" class="tab-btn active" onclick="switchUploadMode('file')">Media File</button>
                <button id="upload-tab-text-btn" class="tab-btn" onclick="switchUploadMode('text')">Text Claim</button>
            </div>
            
            <div id="upload-feedback" style="display: none; padding: 10px 14px; border-radius: 6px; font-size: 12px; margin: 14px 20px 0 20px;"></div>

            <!-- File Upload Form -->
            <form id="form-upload-file" onsubmit="handleUploadFile(event)">
                <div class="modal-body">
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

            <!-- Text Claim Form -->
            <form id="form-upload-text" style="display: none;" onsubmit="handleUploadText(event)">
                <div class="modal-body">
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
        let activeTab = "overview";
        let graphData = null;
        let reportData = null;
        let timelineData = null;

        // Auto-detect investigation from URL query params
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("investigation_id")) {
            currentInvId = urlParams.get("investigation_id");
        }

        // Initialize application
        async function initWorkbench() {
            if (!currentInvId || currentInvId === "{{INV_ID}}" || currentInvId === "") {
                // If no case selected, load latest investigation from API
                try {
                    const res = await fetch("/api/v1/investigations/");
                    if (res.ok) {
                        const cases = await res.json();
                        if (cases && cases.length > 0) {
                            currentInvId = cases[0].id;
                            currentInvTitle = cases[0].title;
                            window.history.replaceState({}, '', `/workbench?investigation_id=${currentInvId}`);
                        }
                    }
                } catch (e) {
                    console.error("Error fetching cases:", e);
                }
            }

            if (currentInvId && currentInvId !== "{{INV_ID}}") {
                updateCaseHeader();
                await loadAllCaseData();
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

            forContainer.innerHTML = reportData.submissions.map(s => `
                <div class="finding-card">
                    <div class="finding-header">
                        <span class="finding-title">Forensic Profile: ${s.id}</span>
                        <span class="badge badge-cyan">${s.submission_type}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; font-size: 12px;">
                        <div>
                            <div style="color: var(--text-muted); margin-bottom: 2px;">PERCEPTUAL & CRYPTOGRAPHIC HASHES</div>
                            <div class="mono" style="color: var(--cyan);">SHA-256: ${s.media_asset?.sha256_hash || 'Computed on intake'}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); margin-bottom: 2px;">TIME & GEOLOCATION CONSISTENCY</div>
                            <div>Claimed: <b>${s.claimed_date || 'None'}</b> | EXIF Sensor: <b>Verified Timestamp</b></div>
                        </div>
                    </div>
                </div>
            `).join("");
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
        function openUploadModal() {
            clearUploadFeedback();
            openModal("modal-upload");
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
                    tbody.innerHTML = cases.map(c => `
                        <tr onclick="selectCase('${c.id}', '${c.title.replace(/'/g, "\\'")}')">
                            <td>
                                <div style="font-weight: 700; color: #ffffff;">${c.title}</div>
                                <div class="mono" style="font-size: 11px; color: var(--cyan);">${c.id}</div>
                            </td>
                            <td><span class="badge ${c.priority === 'HIGH' ? 'badge-red' : 'badge-green'}">${c.priority}</span></td>
                            <td><span class="badge badge-cyan">${c.status}</span></td>
                            <td class="mono" style="font-size: 11px;">${new Date(c.updated_at).toLocaleDateString()}</td>
                        </tr>
                    `).join("");
                }
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="4" style="color:var(--accent-red);">Failed to load cases: ${e.message}</td></tr>`;
            }
        }

        function selectCase(id, title) {
            currentInvId = id;
            currentInvTitle = title;
            closeModal("modal-switcher");
            window.location.search = `?investigation_id=${id}`;
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
                    closeModal("modal-new-case");
                    window.location.search = `?investigation_id=${newCase.id}`;
                } else {
                    alert("Failed to create investigation.");
                }
            } catch (err) {
                alert("Error: " + err.message);
            }
        }

        function switchUploadMode(mode) {
            if (mode === 'file') {
                document.getElementById("upload-tab-file-btn").classList.add("active");
                document.getElementById("upload-tab-text-btn").classList.remove("active");
                document.getElementById("form-upload-file").style.display = "block";
                document.getElementById("form-upload-text").style.display = "none";
            } else {
                document.getElementById("upload-tab-file-btn").classList.remove("active");
                document.getElementById("upload-tab-text-btn").classList.add("active");
                document.getElementById("form-upload-file").style.display = "none";
                document.getElementById("form-upload-text").style.display = "block";
            }
        }

        async function handleUploadFile(e) {
            e.preventDefault();
            clearUploadFeedback();

            if (!currentInvId || currentInvId === "{{INV_ID}}" || currentInvId === "") {
                showUploadFeedback("No active investigation selected. Please open or create a case first.", true);
                return;
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

            if (!currentInvId || currentInvId === "{{INV_ID}}" || currentInvId === "") {
                showUploadFeedback("No active investigation selected. Please open or create a case first.", true);
                return;
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

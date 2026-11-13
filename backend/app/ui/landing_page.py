"""
TRUTHNET AI — Public Landing Page Template.
World-class product landing page for YUKTIK-2026 PS-11.
"""

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUTHNET AI — Multimodal Misinformation Intelligence Platform</title>
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
            --violet-glow: rgba(139, 92, 246, 0.2);
            --amber: #f59e0b;
            --red: #f43f5e;
            --green: #10b981;
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
            line-height: 1.6;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        /* Ambient Glow & Background Atmosphere */
        .ambient-glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 0;
            background: 
                radial-gradient(circle at 80% 20%, rgba(0, 240, 255, 0.06) 0%, transparent 45%),
                radial-gradient(circle at 15% 55%, rgba(139, 92, 246, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 50% 85%, rgba(13, 148, 136, 0.04) 0%, transparent 50%);
        }

        /* Navigation Bar */
        nav {
            position: sticky;
            top: 0;
            width: 100%;
            height: 70px;
            background: rgba(5, 9, 20, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(30, 47, 84, 0.6);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 48px;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            font-size: 17px;
            letter-spacing: 0.8px;
            color: var(--text-main);
        }

        .brand-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--cyan), var(--violet));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 16px var(--cyan-glow);
        }

        .brand-icon svg {
            width: 18px;
            height: 18px;
            fill: #050914;
        }

        .brand-badge {
            background: rgba(0, 240, 255, 0.1);
            color: var(--cyan);
            border: 1px solid rgba(0, 240, 255, 0.3);
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 12px;
            letter-spacing: 0.5px;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 32px;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .nav-links a:hover {
            color: var(--cyan);
            transition: color 0.15s ease;
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .btn-launch {
            background: linear-gradient(135deg, var(--cyan), #00b4d8);
            color: #050914;
            font-weight: 700;
            font-size: 13px;
            padding: 9px 20px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.25);
            transition: all 0.2s ease;
        }

        .btn-launch:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 28px rgba(0, 240, 255, 0.4);
            filter: brightness(1.08);
        }

        /* Hero Section */
        .hero {
            position: relative;
            z-index: 1;
            padding: 90px 48px 100px;
            max-width: 1360px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1.15fr 0.95fr;
            align-items: center;
            gap: 40px;
            min-height: calc(100vh - 70px);
        }

        .hero-left {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1.5px;
            color: var(--cyan);
            text-transform: uppercase;
        }

        .eyebrow::before {
            content: "";
            width: 8px;
            height: 8px;
            background: var(--cyan);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--cyan);
            animation: pulse-dot 2s infinite ease-in-out;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.8); }
        }

        .hero-title {
            font-size: 52px;
            font-weight: 800;
            line-height: 1.12;
            letter-spacing: -1.2px;
            color: #ffffff;
        }

        .hero-title span {
            background: linear-gradient(135deg, #ffffff 40%, var(--cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-desc {
            font-size: 17px;
            color: var(--text-secondary);
            line-height: 1.65;
            max-width: 560px;
            font-weight: 400;
        }

        .hero-actions {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-top: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--cyan), #00a8cc);
            color: #050914;
            font-weight: 700;
            font-size: 14px;
            padding: 14px 28px;
            border-radius: 8px;
            box-shadow: 0 0 24px rgba(0, 240, 255, 0.3);
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 32px rgba(0, 240, 255, 0.45);
        }

        .btn-secondary {
            background: rgba(15, 26, 54, 0.8);
            border: 1px solid var(--border-light);
            color: var(--text-main);
            font-weight: 600;
            font-size: 14px;
            padding: 14px 24px;
            border-radius: 8px;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--cyan);
            color: var(--cyan);
        }

        .hero-capabilities-bar {
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid rgba(30, 47, 84, 0.5);
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }

        .hero-capabilities-bar b {
            color: var(--text-secondary);
        }

        /* Integrated Right-Side Hero Visual */
        .hero-right {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 520px;
        }

        .forensic-scene {
            position: relative;
            width: 100%;
            max-width: 540px;
            height: 480px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* Central Media Viewport */
        .central-media-canvas {
            position: relative;
            width: 320px;
            height: 220px;
            background: 
                linear-gradient(rgba(5, 9, 20, 0.4), rgba(5, 9, 20, 0.8)),
                radial-gradient(circle at 50% 50%, rgba(13, 148, 136, 0.3) 0%, transparent 80%),
                repeating-linear-gradient(0deg, transparent, transparent 20px, rgba(0, 240, 255, 0.05) 21px, transparent 22px),
                repeating-linear-gradient(90deg, transparent, transparent 20px, rgba(0, 240, 255, 0.05) 21px, transparent 22px);
            border: 1px solid rgba(0, 240, 255, 0.4);
            border-radius: 12px;
            box-shadow: 
                0 0 50px rgba(0, 240, 255, 0.15),
                inset 0 0 30px rgba(0, 240, 255, 0.08);
            overflow: hidden;
            z-index: 5;
        }

        /* Reticle & Crosshairs */
        .reticle-corner {
            position: absolute;
            width: 14px;
            height: 14px;
            border-color: var(--cyan);
            border-style: solid;
        }
        .rc-tl { top: 8px; left: 8px; border-width: 2px 0 0 2px; }
        .rc-tr { top: 8px; right: 8px; border-width: 2px 2px 0 0; }
        .rc-bl { bottom: 8px; left: 8px; border-width: 0 0 2px 2px; }
        .rc-br { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }

        .reticle-center {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 44px;
            height: 44px;
            border: 1px dashed rgba(0, 240, 255, 0.5);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .reticle-center::after {
            content: "";
            width: 6px;
            height: 6px;
            background: var(--cyan);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--cyan);
        }

        .scan-beam {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--cyan), transparent);
            box-shadow: 0 0 12px var(--cyan);
            animation: scan-vertical 3.5s infinite ease-in-out;
        }

        @keyframes scan-vertical {
            0% { top: 0%; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
        }

        .media-caption-overlay {
            position: absolute;
            bottom: 12px;
            left: 14px;
            right: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: var(--cyan);
        }

        /* Floating Analytical Nodes (Integrated Convergence) */
        .floating-node {
            position: absolute;
            background: rgba(10, 17, 36, 0.92);
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 10px 14px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px var(--cyan-glow);
            z-index: 10;
            backdrop-filter: blur(12px);
            font-size: 11px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: all 0.3s ease;
        }

        .floating-node:hover {
            transform: scale(1.04);
            border-color: var(--cyan);
        }

        .fn-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .fn-val {
            font-weight: 600;
            color: var(--text-main);
        }

        .node-exif {
            top: 15px;
            left: 10px;
        }
        .node-exif .fn-badge { color: var(--amber); }

        .node-orb {
            top: 30px;
            right: 5px;
        }
        .node-orb .fn-badge { color: var(--cyan); }

        .node-wire {
            bottom: 25px;
            left: 15px;
        }
        .node-wire .fn-badge { color: var(--violet); }

        .node-verdict {
            bottom: 20px;
            right: 10px;
        }
        .node-verdict .fn-badge { color: var(--amber); }

        /* Fine SVG Network Convergence Lines */
        .convergence-svg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 4;
        }

        /* SECTION B: Capability Strip */
        .capability-strip {
            position: relative;
            z-index: 1;
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            background: rgba(10, 17, 36, 0.6);
            padding: 24px 48px;
        }

        .strip-inner {
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .strip-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            letter-spacing: 0.3px;
        }

        .strip-item svg {
            width: 18px;
            height: 18px;
            fill: var(--cyan);
        }

        /* Section Container */
        .section-wrap {
            position: relative;
            z-index: 1;
            padding: 100px 48px;
            max-width: 1280px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            max-width: 760px;
            margin: 0 auto 60px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .section-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            color: var(--cyan);
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }

        .section-title {
            font-size: 36px;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.8px;
            color: #ffffff;
        }

        .section-desc {
            font-size: 16px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* SECTION C: The Problem */
        .problem-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 28px;
        }

        .problem-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px 28px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            position: relative;
            overflow: hidden;
            transition: all 0.25s ease;
        }

        .problem-card:hover {
            border-color: var(--border-light);
            transform: translateY(-4px);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
        }

        .problem-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
        }

        .pc-red::before { background: var(--red); }
        .pc-amber::before { background: var(--amber); }
        .pc-purple::before { background: var(--violet); }

        .problem-num {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            letter-spacing: 1px;
        }

        .problem-title {
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
        }

        .problem-desc {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* SECTION D: Complete 9-Capability Showcase */
        .capabilities-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }

        .cap-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 26px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            transition: all 0.2s ease;
        }

        .cap-card:hover {
            border-color: var(--cyan);
            background: var(--bg-card);
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.08);
        }

        .cap-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .cap-icon-box {
            width: 40px;
            height: 40px;
            background: rgba(0, 240, 255, 0.08);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cap-icon-box svg {
            width: 20px;
            height: 20px;
            fill: var(--cyan);
        }

        .cap-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(148, 163, 184, 0.1);
            color: var(--text-secondary);
        }

        .cap-title {
            font-size: 17px;
            font-weight: 700;
            color: #ffffff;
        }

        .cap-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.55;
            flex: 1;
        }

        .cap-bullets {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 8px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-muted);
        }

        .cap-bullets li {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .cap-bullets li::before {
            content: "•";
            color: var(--cyan);
            font-weight: bold;
        }

        /* 6 Verdict Showcase Inside Claim Intelligence */
        .verdicts-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
        }

        .v-pill {
            font-family: 'JetBrains Mono', monospace;
            font-size: 9px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .v-supported { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
        .v-contradicted { background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.3); }
        .v-misleading { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .v-unverified { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }
        .v-insufficient { background: rgba(100, 116, 139, 0.15); color: #cbd5e1; border: 1px solid rgba(100, 116, 139, 0.3); }
        .v-conflicting { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

        /* SECTION E: How It Works Pipeline */
        .pipeline-flow {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 16px;
            position: relative;
        }

        .pipeline-step {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 24px 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            text-align: center;
            position: relative;
        }

        .step-index {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            color: var(--cyan);
            background: rgba(0, 240, 255, 0.1);
            border-radius: 12px;
            padding: 2px 8px;
            display: inline-block;
            margin: 0 auto;
        }

        .step-name {
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
        }

        .step-desc {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.45;
        }

        /* SECTION F: Epistemic Principles */
        .principles-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }

        .principle-box {
            background: linear-gradient(135deg, rgba(10, 17, 36, 0.9), rgba(15, 26, 54, 0.6));
            border: 1px solid var(--border);
            border-left: 4px solid var(--cyan);
            border-radius: 8px;
            padding: 24px 28px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .p-law {
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.2px;
        }

        .p-rationale {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* SECTION G: Final CTA */
        .cta-banner {
            background: linear-gradient(135deg, #091329 0%, #0d1e3d 100%);
            border: 1px solid var(--border-light);
            border-radius: 16px;
            padding: 70px 48px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 80px rgba(0, 240, 255, 0.08);
        }

        .cta-banner::before {
            content: "";
            position: absolute;
            top: -50%;
            left: 50%;
            transform: translateX(-50%);
            width: 600px;
            height: 300px;
            background: radial-gradient(ellipse, rgba(0, 240, 255, 0.15), transparent 70%);
            pointer-events: none;
        }

        .cta-title {
            font-size: 40px;
            font-weight: 800;
            letter-spacing: -1px;
            color: #ffffff;
        }

        .cta-desc {
            font-size: 17px;
            color: var(--text-secondary);
            max-width: 600px;
            line-height: 1.6;
        }

        /* Footer */
        footer {
            border-top: 1px solid var(--border);
            background: #03060d;
            padding: 50px 48px 30px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .footer-inner {
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 24px;
            padding-bottom: 30px;
            border-bottom: 1px solid rgba(30, 47, 84, 0.4);
        }

        .footer-bottom {
            max-width: 1280px;
            margin: 24px auto 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-muted);
        }

        /* Responsive Breakpoints */
        @media (max-width: 1024px) {
            .hero { grid-template-columns: 1fr; padding-top: 40px; }
            .problem-grid, .capabilities-grid { grid-template-columns: repeat(2, 1fr); }
            .pipeline-flow { grid-template-columns: repeat(3, 1fr); }
            nav { padding: 0 24px; }
            .section-wrap { padding: 60px 24px; }
        }

        @media (max-width: 768px) {
            .hero-title { font-size: 38px; }
            .problem-grid, .capabilities-grid, .principles-grid { grid-template-columns: 1fr; }
            .pipeline-flow { grid-template-columns: repeat(2, 1fr); }
            .nav-links { display: none; }
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>

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
        <div class="nav-actions">
            <a href="/workbench" class="btn-launch">
                <span>Launch Workbench</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
        </div>
    </nav>

    <!-- SECTION A: HERO -->
    <section class="hero">
        <div class="hero-left">
            <div class="eyebrow">MULTIMODAL INVESTIGATIVE INTELLIGENCE</div>
            <h1 class="hero-title">
                When digital evidence is manipulated, <span>context becomes intelligence.</span>
            </h1>
            <p class="hero-desc">
                TRUTHNET AI connects media forensics, historical discovery, claim verification and source intelligence to help investigators understand what happened, what is being claimed and what the evidence actually supports.
            </p>
            <div class="hero-actions">
                <a href="/workbench" class="btn-primary">
                    <span>Launch Workbench</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
                <a href="#capabilities" class="btn-secondary">
                    <span>Explore Capabilities</span>
                </a>
            </div>
            <div class="hero-capabilities-bar">
                <b>Core Architecture:</b> Media Forensics &middot; Claim Intelligence &middot; Historical Discovery &middot; Network Analysis
            </div>
        </div>

        <!-- Integrated Right-Side Hero Visual (No Box, Blends Seamlessly) -->
        <div class="hero-right">
            <div class="forensic-scene">
                <!-- SVG Convergence Circuit Lines -->
                <svg class="convergence-svg" viewBox="0 0 540 480">
                    <!-- Line to EXIF Node -->
                    <path d="M 270 200 C 200 170, 160 120, 110 75" fill="none" stroke="rgba(245, 158, 11, 0.5)" stroke-width="1.5" stroke-dasharray="4,4"/>
                    <!-- Line to ORB Node -->
                    <path d="M 270 200 C 340 160, 390 120, 430 85" fill="none" stroke="rgba(0, 240, 255, 0.6)" stroke-width="1.5" stroke-dasharray="4,4"/>
                    <!-- Line to Wire Node -->
                    <path d="M 270 280 C 200 320, 160 370, 115 415" fill="none" stroke="rgba(139, 92, 246, 0.5)" stroke-width="1.5" stroke-dasharray="4,4"/>
                    <!-- Line to Verdict Node -->
                    <path d="M 270 280 C 350 330, 400 380, 440 410" fill="none" stroke="rgba(245, 158, 11, 0.6)" stroke-width="1.5" stroke-dasharray="4,4"/>
                </svg>

                <!-- Floating Analytical Node: EXIF Timecode -->
                <div class="floating-node node-exif">
                    <span class="fn-badge"><span style="width:6px;height:6px;background:var(--amber);border-radius:50%;"></span> EXIF TIMECODE</span>
                    <span class="fn-val">2020-10-14 17:42:09 UTC</span>
                    <span style="font-size:10px;color:var(--text-muted);">True Camera Timestamp</span>
                </div>

                <!-- Floating Analytical Node: ORB Keypoints -->
                <div class="floating-node node-orb">
                    <span class="fn-badge"><span style="width:6px;height:6px;background:var(--cyan);border-radius:50%;"></span> ORB GEOMETRY</span>
                    <span class="fn-val">142 Inliers (Ratio 0.88)</span>
                    <span style="font-size:10px;color:var(--text-muted);">Homography Converged</span>
                </div>

                <!-- Central Media Artifact Viewport -->
                <div class="central-media-canvas">
                    <div class="scan-beam"></div>
                    <div class="reticle-corner rc-tl"></div>
                    <div class="reticle-corner rc-tr"></div>
                    <div class="reticle-corner rc-bl"></div>
                    <div class="reticle-corner rc-br"></div>
                    <div class="reticle-center"></div>

                    <!-- Subtle forensic HUD content inside canvas -->
                    <div style="position: absolute; top: 12px; left: 14px; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--cyan); letter-spacing: 0.5px;">
                        FINGERPRINT: SHA-256 f1d2d2f9...
                    </div>
                    <div style="position: absolute; top: 28px; left: 14px; font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--text-muted);">
                        pHash: 6 | dHash: 4 | RANSAC: PASS
                    </div>
                    <div class="media-caption-overlay">
                        <span>SUSPECT VIRAL MEDIA</span>
                        <span style="color: var(--amber);">REUSED CONTEXT</span>
                    </div>
                </div>

                <!-- Floating Analytical Node: Wire Service Attribution -->
                <div class="floating-node node-wire">
                    <span class="fn-badge"><span style="width:6px;height:6px;background:var(--violet);border-radius:50%;"></span> SOURCE INDEPENDENCE</span>
                    <span class="fn-val">PTI Byline Syndication</span>
                    <span style="font-size:10px;color:var(--text-muted);">Single Shared Wire Copy</span>
                </div>

                <!-- Floating Analytical Node: Lineage Verdict -->
                <div class="floating-node node-verdict">
                    <span class="fn-badge"><span style="width:6px;height:6px;background:var(--amber);border-radius:50%;"></span> CONTEXTUAL VERDICT</span>
                    <span class="fn-val">Misleading Context</span>
                    <span style="font-size:10px;color:var(--text-muted);">2020 Deluge Recirculated</span>
                </div>
            </div>
        </div>
    </section>

    <!-- SECTION B: TRUST & CAPABILITY STRIP -->
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

    <!-- SECTION C: THE INVESTIGATION PROBLEM -->
    <section class="section-wrap" id="problem">
        <div class="section-header">
            <span class="section-tag">THE PROBLEM</span>
            <h2 class="section-title">Misinformation is deeper than synthetic pixels.</h2>
            <p class="section-desc">
                Digital deception has evolved beyond simple generative deepfakes. Investigators face layered attacks where genuine historical assets are weaponized out-of-context and amplified through syndicated networks.
            </p>
        </div>

        <div class="problem-grid">
            <div class="problem-card pc-red">
                <span class="problem-num">01 / FORGERY</span>
                <h3 class="problem-title">Manipulated Media</h3>
                <p class="problem-desc">
                    Images, videos, and speech can be altered, face-swapped, voice-cloned, or synthetically generated. Without technical metadata, keyframe analysis, and perceptual hashing, fabricated visual assets fool standard content moderation filters.
                </p>
            </div>

            <div class="problem-card pc-amber">
                <span class="problem-num">02 / DISPLACEMENT</span>
                <h3 class="problem-title">Misleading Context</h3>
                <p class="problem-desc">
                    Authentic media is routinely recirculated with fabricated dates, locations, or provocative captions. A genuine photograph from 2018 or 2020 presented as "breaking news today" passes binary authenticity checks while spreading massive falsehood.
                </p>
            </div>

            <div class="problem-card pc-purple">
                <span class="problem-num">03 / AMPLIFICATION</span>
                <h3 class="problem-title">Coordinated Narratives</h3>
                <p class="problem-desc">
                    Identical claims and recycled media spread synchronously across hundreds of channels. Ten different URLs citing the same single syndicated wire dispatch do not constitute ten independent confirmations—they represent a single source dependency.
                </p>
            </div>
        </div>
    </section>

    <!-- SECTION D: COMPLETE 9-CAPABILITY SHOWCASE -->
    <section class="section-wrap" id="capabilities">
        <div class="section-header">
            <span class="section-tag">CAPABILITIES SHOWCASE</span>
            <h2 class="section-title">An intelligence workbench built for rigorous verification.</h2>
            <p class="section-desc">
                TRUTHNET AI integrates media forensics, deterministic contextual reasoning, live web retrieval, and graph lineage into one unified platform.
            </p>
        </div>

        <div class="capabilities-grid">
            <!-- 1. Multimodal Media Forensics -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                    </div>
                    <span class="cap-badge">FORENSICS</span>
                </div>
                <h3 class="cap-title">Multimodal Media Forensics</h3>
                <p class="cap-desc">
                    Deconstructs evidence into forensic artifacts. Extracts camera EXIF parameters, demuxes video keyframes, performs OCR text recognition, and transcribes speech while strictly isolating corrupt binaries.
                </p>
                <ul class="cap-bullets">
                    <li>Camera model & original EXIF capture timestamp</li>
                    <li>Boundary-anchored video keyframe demuxing</li>
                    <li>OCR inference & Whisper speech transcription</li>
                </ul>
            </div>

            <!-- 2. Historical Media Rediscovery -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                    </div>
                    <span class="cap-badge">SIGNATURE FEATURE</span>
                </div>
                <h3 class="cap-title">Historical Media Rediscovery</h3>
                <p class="cap-desc">
                    Matches submitted suspect media against historical event repositories using two-tier indexing: lightning-fast pHash/dHash filtering followed by OpenCV ORB keypoints and RANSAC homography verification.
                </p>
                <ul class="cap-bullets">
                    <li>Exact SHA-256 and near-duplicate perceptual hashing</li>
                    <li>ORB feature inlier count & geometric ratio</li>
                    <li>Distinguishes archival reuse from claim truth</li>
                </ul>
            </div>

            <!-- 3. Claim Intelligence -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    </div>
                    <span class="cap-badge">SEMANTICS</span>
                </div>
                <h3 class="cap-title">Claim Intelligence & Polarity</h3>
                <p class="cap-desc">
                    Extracts syntactic propositions into structured Subject-Predicate-Object triples. Identifies grammatical surface polarity, handles negations, and maps claims to six distinct deterministic assessment verdicts.
                </p>
                <div class="verdicts-pill-row">
                    <span class="v-pill v-supported">SUPPORTED</span>
                    <span class="v-pill v-contradicted">CONTRADICTED</span>
                    <span class="v-pill v-misleading">MISLEADING_OR_CONTEXT_MISSING</span>
                    <span class="v-pill v-unverified">UNVERIFIED</span>
                    <span class="v-pill v-insufficient">INSUFFICIENT_EVIDENCE</span>
                    <span class="v-pill v-conflicting">CONFLICTING_EVIDENCE</span>
                </div>
            </div>

            <!-- 4. Real-Time Source Retrieval -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z"/></svg>
                    </div>
                    <span class="cap-badge">RETRIEVAL</span>
                </div>
                <h3 class="cap-title">Real-Time Evidence Retrieval</h3>
                <p class="cap-desc">
                    Searches public sources and extracts canonical articles with SSRF guards and DNS rebinding prevention. Automatically parses schema.org `ClaimReview` LD-JSON structured fact-check records.
                </p>
                <ul class="cap-bullets">
                    <li>SSRF & private network isolation safeguards</li>
                    <li>Automated ClaimReview JSON-LD extraction</li>
                    <li>Graceful provider degradation (Tavily/Google/Wiki)</li>
                </ul>
            </div>

            <!-- 5. Source Independence Intelligence -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
                    </div>
                    <span class="cap-badge">SOURCE GRAPH</span>
                </div>
                <h3 class="cap-title">Source Independence Intelligence</h3>
                <p class="cap-desc">
                    Prevents circular confirmation by detecting syndicated wire agency dispatches (PTI, ANI, Reuters) and shared verbatim press releases. Distinct URLs repeating the same wire copy are grouped into a single entity.
                </p>
                <ul class="cap-bullets">
                    <li>Syndicated wire agency byline detection</li>
                    <li>Shared official press release clustering</li>
                    <li>Multi-signal independent corroboration counting</li>
                </ul>
            </div>

            <!-- 6. Claim Lineage & Graph Intelligence -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                    </div>
                    <span class="cap-badge">LINEAGE</span>
                </div>
                <h3 class="cap-title">Claim Lineage & Graph Analytics</h3>
                <p class="cap-desc">
                    Constructs an interactive directed lineage graph connecting submissions, media assets, claims, and assessments. Employs a 4-state edge taxonomy: Observed, System-Derived, Inferred, and Human-Confirmed.
                </p>
                <ul class="cap-bullets">
                    <li>NetworkX MultiDiGraph relationship engine</li>
                    <li>Four-state edge nature transparency</li>
                    <li>Zero unpersisted ghost nodes</li>
                </ul>
            </div>

            <!-- 7. Timeline & Historical Context -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    </div>
                    <span class="cap-badge">TEMPORAL</span>
                </div>
                <h3 class="cap-title">Timeline & Temporal Context</h3>
                <p class="cap-desc">
                    Strictly decouples and maps multiple distinct temporal timestamps: Observed EXIF Capture Date, Claimed Event Date, Platform Submission Date, External Publication Date, and Assessment Date.
                </p>
                <ul class="cap-bullets">
                    <li>Chronological sequence reconstruction</li>
                    <li>Instant detection of multi-year temporal gaps</li>
                    <li>Clean, expandable timeline entries without raw JSON</li>
                </ul>
            </div>

            <!-- 8. Coordination Intelligence Signals -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    </div>
                    <span class="cap-badge">COORDINATION</span>
                </div>
                <h3 class="cap-title">Coordination Intelligence Signals</h3>
                <p class="cap-desc">
                    Surfaces explainable behavioral signals across related posts: identical captions, co-temporal bursts, near-duplicate text variants, and shared asset distribution without relying on black-box opacity.
                </p>
                <ul class="cap-bullets">
                    <li>Shared caption and text similarity clustering</li>
                    <li>Cross-submission distribution pattern analysis</li>
                    <li>Explainable relationship evidence summaries</li>
                </ul>
            </div>

            <!-- 9. Human Review & Dossier Reporting -->
            <div class="cap-card">
                <div class="cap-header">
                    <div class="cap-icon-box">
                        <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                    </div>
                    <span class="cap-badge">GOVERNANCE</span>
                </div>
                <h3 class="cap-title">Human Review & Dossier Reporting</h3>
                <p class="cap-desc">
                    Keeps human investigators firmly in control. Allows recording Confirmed, Disputed, or Modified determinations with audit logs, and outputs comprehensive, printable investigation dossiers.
                </p>
                <ul class="cap-bullets">
                    <li>Interactive investigator review & audit logging</li>
                    <li>Decision-tree explanation traceability</li>
                    <li>Printable investigation dossier report</li>
                </ul>
            </div>
        </div>
    </section>

    <!-- SECTION E: HOW IT WORKS PIPELINE -->
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
                <span class="step-index">STEP 01</span>
                <h4 class="step-name">SUBMIT</h4>
                <p class="step-desc">Ingest images, videos, audio, or text claims with claimed dates and locations.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">STEP 02</span>
                <h4 class="step-name">EXTRACT</h4>
                <p class="step-desc">Derive camera metadata, OCR text, audio transcripts, and syntactic claim triples.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">STEP 03</span>
                <h4 class="step-name">DISCOVER</h4>
                <p class="step-desc">Perform perceptual hash and ORB geometric rediscovery against historical archives.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">STEP 04</span>
                <h4 class="step-name">VERIFY</h4>
                <p class="step-desc">Retrieve external authoritative sources and verify source independence.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">STEP 05</span>
                <h4 class="step-name">CONNECT</h4>
                <p class="step-desc">Generate directed Claim Lineage graph linking entities, media, and evidence.</p>
            </div>
            <div class="pipeline-step">
                <span class="step-index">STEP 06</span>
                <h4 class="step-name">REVIEW</h4>
                <p class="step-desc">Human investigator records determination and compiles printable case dossier.</p>
            </div>
        </div>
    </section>

    <!-- SECTION F: EPISTEMIC PRINCIPLES -->
    <section class="section-wrap" id="principles">
        <div class="section-header">
            <span class="section-tag">CORE METHODOLOGY</span>
            <h2 class="section-title">The Four Epistemic Principles</h2>
            <p class="section-desc">
                TRUTHNET AI is built on rigorous epistemological boundaries. We never confuse statistical similarity with verified ground truth.
            </p>
        </div>

        <div class="principles-grid">
            <div class="principle-box">
                <h4 class="p-law">1. Media authenticity does not establish claim truth.</h4>
                <p class="p-rationale">
                    A completely authentic, unaltered photograph can be shared with a false date or misleading location. Proving an image is unmanipulated does not verify the caption.
                </p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">2. Historical reuse does not automatically prove misinformation.</h4>
                <p class="p-rationale">
                    Legitimate news articles frequently reuse archival file photos to illustrate current events. Historical rediscovery provides contextual evidence, not an automatic verdict.
                </p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">3. Similar reporting does not equal independent corroboration.</h4>
                <p class="p-rationale">
                    Multiple news outlets publishing identical syndicated wire dispatches (PTI, Reuters) represent a single source dependency, not multiple independent witnesses.
                </p>
            </div>
            <div class="principle-box">
                <h4 class="p-law">4. Insufficient evidence is never proof of falsehood.</h4>
                <p class="p-rationale">
                    When public evidence is absent or inconclusive, TRUTHNET maintains an explicit INSUFFICIENT_EVIDENCE or UNVERIFIED status. Absence of proof is not proof of absence.
                </p>
            </div>
        </div>
    </section>

    <!-- SECTION G: FINAL CTA -->
    <section class="section-wrap">
        <div class="cta-banner">
            <h2 class="cta-title">Investigate beyond the surface.</h2>
            <p class="cta-desc">
                Connect media, claims, sources and historical context in one evidence-led investigation. Explore our interactive demonstration case or launch a new investigation now.
            </p>
            <a href="/workbench" class="btn-primary" style="padding: 16px 36px; font-size: 15px;">
                <span>Open TRUTHNET Workbench</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
        </div>
    </section>

    <!-- SECTION H: FOOTER -->
    <footer>
        <div class="footer-inner">
            <div>
                <div class="brand" style="margin-bottom: 8px;">
                    <div class="brand-icon" style="width: 24px; height: 24px;">
                        <svg viewBox="0 0 24 24" style="width: 14px; height: 14px;"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                    </div>
                    <span>TRUTHNET AI</span>
                </div>
                <p style="max-width: 380px; font-size: 12px; line-height: 1.6;">
                    Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform. Built for YUKTIK-2026 Problem Statement PS-11.
                </p>
            </div>

            <div style="display: flex; gap: 48px; font-size: 13px;">
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <b style="color: var(--text-main); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Product</b>
                    <a href="/workbench" style="color: var(--text-secondary);">Workbench</a>
                    <a href="/docs" target="_blank" style="color: var(--text-secondary);">API Documentation</a>
                    <a href="#capabilities" style="color: var(--text-secondary);">Capabilities</a>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <b style="color: var(--text-main); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Architecture</b>
                    <a href="#workflow" style="color: var(--text-secondary);">Pipeline</a>
                    <a href="#principles" style="color: var(--text-secondary);">Epistemics</a>
                    <a href="/health" style="color: var(--text-secondary);">System Health</a>
                </div>
            </div>
        </div>

        <div class="footer-bottom">
            <span>&copy; 2026 TRUTHNET AI &middot; Evidence-Led Intelligence</span>
            <span>YUKTIK-2026 &middot; PS-11 National Hackathon</span>
        </div>
    </footer>
</body>
</html>
"""

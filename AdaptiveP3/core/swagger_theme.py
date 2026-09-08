"""
AP3 — Custom Swagger UI Theme & Guided Navigation Banner
=========================================================
Injects a clean, modern, executive light-mode UI into Swagger docs with
an interactive first-time user guidance banner, architecture walkthrough,
and direct link to the Visual Playground.
"""

def get_custom_swagger_css() -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-body: #f8fafc;
        --bg-card: #ffffff;
        --bg-card-hover: #f1f5f9;
        --border-color: #e2e8f0;
        --accent-indigo: #4f46e5;
        --accent-cyan: #0284c7;
        --accent-emerald: #059669;
        --accent-amber: #d97706;
        --accent-rose: #e11d48;
        --text-primary: #0f172a;
        --text-muted: #64748b;
    }

    body {
        font-family: 'Outfit', sans-serif !important;
        background-color: var(--bg-body) !important;
        color: var(--text-primary) !important;
        margin: 0;
        padding: 0;
    }

    .swagger-ui {
        font-family: 'Outfit', sans-serif !important;
        color: #334155 !important;
    }

    /* Top Navigation Guided Banner */
    .ap3-guide-banner {
        background: #ffffff;
        border-bottom: 1px solid var(--border-color);
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
        padding: 24px 32px;
    }

    .ap3-banner-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 20px;
    }

    .ap3-title-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .ap3-logo-badge {
        background: linear-gradient(135deg, #4f46e5, #8b5cf6);
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 800;
        padding: 6px 14px;
        border-radius: 10px;
        letter-spacing: 0.05em;
        box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
    }

    .ap3-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.02em;
    }

    .ap3-action-btn {
        background: linear-gradient(135deg, #0284c7, #4f46e5);
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 10px 20px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
        transition: all 0.2s ease;
    }

    .ap3-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
        color: #ffffff;
    }

    /* Steps Ribbon */
    .ap3-steps-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin-top: 16px;
    }

    .ap3-step-card {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        transition: all 0.2s ease;
    }

    .ap3-step-card:hover {
        border-color: var(--accent-indigo);
        background: #f8fafc;
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.1);
    }

    .ap3-step-num {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--accent-indigo);
        margin-bottom: 6px;
        letter-spacing: 0.05em;
    }

    .ap3-step-heading {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 4px;
    }

    .ap3-step-desc {
        font-size: 0.82rem;
        color: var(--text-muted);
        line-height: 1.4;
    }

    .ap3-formula-pill {
        display: inline-block;
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        color: #4338ca;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        padding: 4px 8px;
        border-radius: 6px;
        margin-top: 8px;
    }

    /* Swagger UI Elements Styling */
    .swagger-ui .topbar { display: none !important; }
    .swagger-ui .info { margin: 25px 0 !important; }
    .swagger-ui .info .title { color: #0f172a !important; font-weight: 800 !important; }
    .swagger-ui .info p, .swagger-ui .info li { color: #475569 !important; }
    .swagger-ui .scheme-container { background: transparent !important; box-shadow: none !important; }
    
    /* Operations */
    .swagger-ui .opblock {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
        margin-bottom: 16px !important;
        overflow: hidden;
    }

    .swagger-ui .opblock .opblock-summary {
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 12px 18px !important;
    }

    .swagger-ui .opblock .opblock-summary-path {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    .swagger-ui .opblock .opblock-summary-description {
        color: #64748b !important;
    }

    .swagger-ui .opblock.opblock-post { border-left: 4px solid var(--accent-emerald) !important; }
    .swagger-ui .opblock.opblock-get { border-left: 4px solid var(--accent-indigo) !important; }

    .swagger-ui .opblock .opblock-summary-method {
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace !important;
        padding: 6px 12px !important;
    }

    .swagger-ui .opblock-body {
        background: #f8fafc !important;
    }

    .swagger-ui input[type=text], .swagger-ui textarea {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 6px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .swagger-ui .btn.execute {
        background: linear-gradient(135deg, #4f46e5, #3730a3) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    }

    .swagger-ui .btn.try-out__btn {
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
        border-radius: 6px !important;
        background: #ffffff !important;
    }

    .swagger-ui table thead tr th, .swagger-ui table thead tr td {
        color: #334155 !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }

    .swagger-ui .model-box, .swagger-ui .responses-inner {
        background: transparent !important;
    }

    .swagger-ui select {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }
    """


def get_custom_swagger_html(openapi_url: str, title: str) -> str:
    css = get_custom_swagger_css()
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
        <style>
            {css}
        </style>
    </head>
    <body>
        <!-- Top Guidance Banner for First-Time Users -->
        <header class="ap3-guide-banner">
            <div class="ap3-banner-header">
                <div class="ap3-title-group">
                    <span class="ap3-logo-badge">AP3</span>
                    <span class="ap3-title">Adaptive Privacy-Preserving Proxy</span>
                    <span class="ap3-formula-pill">ε_eff = ε_role · (1 - r)^γ</span>
                </div>
                <div>
                    <a href="/" class="ap3-action-btn" target="_self">
                        <span>🚀 Launch Interactive Playground UI</span>
                    </a>
                </div>
            </div>

            <div style="font-size: 0.9rem; color: #475569; margin-bottom: 8px;">
                <strong>First-time Explorer Guide:</strong> Test the four security & privacy pillars in 4 simple steps:
            </div>

            <div class="ap3-steps-container">
                <div class="ap3-step-card">
                    <span class="ap3-step-num">Step 1 • Register</span>
                    <div class="ap3-step-heading">POST /register</div>
                    <div class="ap3-step-desc">Register a user with role <code>researcher</code> (10.0 budget) or <code>guest</code> (2.0).</div>
                </div>

                <div class="ap3-step-card">
                    <span class="ap3-step-num">Step 2 • Broad Query</span>
                    <div class="ap3-step-heading">POST /query (Broad)</div>
                    <div class="ap3-step-desc">Run <code>SELECT AVG(salary) FROM employees WHERE department='Engineering'</code>. Risk r = 0.0, low noise.</div>
                </div>

                <div class="ap3-step-card">
                    <span class="ap3-step-num">Step 3 • Triangulation</span>
                    <div class="ap3-step-heading">POST /query (Narrow)</div>
                    <div class="ap3-step-desc">Narrow with <code>AND name='Alice'</code>. Notice risk r spikes and ε_eff automatically decreases!</div>
                </div>

                <div class="ap3-step-card">
                    <span class="ap3-step-num">Step 4 • Audit & Degradation</span>
                    <div class="ap3-step-heading">GET /audit/{'{username}'}</div>
                    <div class="ap3-step-desc">Inspect past predicates and risk scores. Observe non-leaking graceful degradation schedule.</div>
                </div>
            </div>
        </header>

        <!-- Swagger UI Container -->
        <div id="swagger-ui"></div>

        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {{
                window.ui = SwaggerUIBundle({{
                    url: '{openapi_url}',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    defaultModelsExpandDepth: -1,
                    docExpansion: "list"
                }});
            }};
        </script>
    </body>
    </html>
    """

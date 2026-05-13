import html
import json
import logging
import os
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from process_pdfs import (
    archive_root_folder,
    input_folder,
    output_folder,
    run_invoice_processing,
)

st.set_page_config(
    page_title="Invoice helper",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {
        --surface: #ffffff;
        --surface-border: #e5e7eb;
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text-main: #111827;
        --text-subtle: #6b7280;
        /*
         * Dashboard hierarchy (universal): higher importance = larger type, darker ink, more air.
         * Each step down uses a smaller step on the type scale and one lighter ink, with spacing
         * tightening between related pairs (label→value) and loosening around primary outcomes.
         */
        --dash-fs-hero: clamp(1.2rem, 2.8vw, 1.55rem);
        --dash-fs-hero-metric: clamp(1.35rem, 3.2vw, 1.85rem);
        --dash-fs-hero-tail: clamp(0.9rem, 2.1vw, 1.05rem);
        --dash-fs-data: 1.2rem;
        --dash-fs-body: 0.9rem;
        --dash-fs-label: 0.78rem;
        --dash-fs-caption: 0.72rem;
        --dash-fs-micro: 0.68rem;
        /* Tech detail log (sidebar code): smaller than body micro */
        --dash-fs-code-log: 0.55rem;
        --dash-ink-strong: #0f172a;
        --dash-ink: #334155;
        --dash-ink-muted: #64748b;
        --dash-ink-faint: #94a3b8;
        --dash-space-xs: 4px;
        --dash-space-sm: 8px;
        --dash-space-md: 12px;
        --dash-space-lg: 16px;
        --dash-space-xl: 20px;
        --dash-space-2xl: 28px;
    }
    .stApp {
        background: linear-gradient(165deg, #f8fafc 0%, #eef2ff 48%, #f8fafc 100%);
        /* Align Streamlit tokens with our light surface (avoids white headings on light bg). */
        --text-color: #0f172a;
        --text-color-secondary: #475569;
    }
    [data-testid="stHeader"] { background: transparent; }
    /* Main column headings (st.title / st.header) — force dark ink */
    div.block-container [data-testid="stHeading"] h1,
    div.block-container [data-testid="stHeading"] h2,
    div.block-container [data-testid="stHeading"] h3,
    div.block-container h1,
    div.block-container h2 {
        color: var(--dash-ink-strong) !important;
        -webkit-text-fill-color: currentColor !important;
    }
    div.block-container {
        padding-top: 0.75rem;
        padding-bottom: 0.55rem;
        max-width: 1120px;
    }
    /* Default page captions follow “quietest” tier */
    div.block-container [data-testid="stCaption"] {
        font-size: var(--dash-fs-caption) !important;
        color: var(--dash-ink-faint) !important;
    }
    .section-card {
        border: 1px solid var(--surface-border);
        background: var(--surface);
        border-radius: 12px;
        padding: 10px 10px 8px 10px;
        margin-bottom: 8px;
    }
    /* Process heading only — avoid split <div class="section-card"> across Streamlit blocks (empty white strip). */
    .section-process {
        margin: var(--dash-space-xs) 0 var(--dash-space-xs) 0;
    }
    /* Upload dropzone contrast and hierarchy */
    [data-testid="stFileUploaderDropzone"] {
        background: #f9fafb;
        border: 1.5px dashed #cbd5e1;
        border-radius: 12px;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        background: #f3f6ff;
        border-color: #93c5fd;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        color: #334155;
    }
    .section-title {
        font-size: var(--dash-fs-body);
        font-weight: 650;
        color: var(--dash-ink-strong);
        margin-bottom: var(--dash-space-xs);
    }
    .section-subtle {
        font-size: var(--dash-fs-label);
        color: var(--dash-ink-muted);
        margin-bottom: var(--dash-space-sm);
    }
    .stButton > button[kind="primary"] {
        background: var(--primary);
        border: 1px solid var(--primary);
        color: #ffffff;
        font-weight: 600;
        border-radius: 10px;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--primary-hover);
        border: 1px solid var(--primary-hover);
        color: #ffffff;
    }
    /* Secondary/utility buttons are neutral and less prominent */
    .stButton > button[kind="secondary"] {
        border: 1px solid var(--surface-border);
        color: #374151;
        background: #ffffff;
        border-radius: 10px;
    }
    .stButton > button[kind="secondary"]:hover {
        border: 1px solid #d1d5db;
        background: #f9fafb;
        color: #111827;
    }
    .stProgress > div > div > div {
        height: 10px;
        border-radius: 999px;
        background: #e5e7eb;
        overflow: hidden;
    }
    .stProgress > div > div > div > div {
        background: var(--primary);
        border-radius: 999px;
        box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.15) inset;
    }
    /*
     * Sidebar: methodology + tech logs — title = body tier + strong ink;
     * actions = label tier; expander copy = label; captions/code = micro + faint.
     */
    section[data-testid="stSidebar"] {
        font-size: var(--dash-fs-label);
        color: var(--dash-ink);
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding-top: var(--dash-space-sm);
        padding-bottom: var(--dash-space-lg);
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        font-size: var(--dash-fs-body);
        font-weight: 650;
        color: var(--dash-ink-strong);
        letter-spacing: -0.02em;
        margin: 0 0 var(--dash-space-sm) 0;
        padding-bottom: var(--dash-space-sm);
        border-bottom: 1px solid rgba(203, 213, 225, 0.65);
    }
    section[data-testid="stSidebar"] hr {
        margin: var(--dash-space-md) 0;
        border: none;
        border-top: 1px solid rgba(203, 213, 225, 0.75);
    }
    section[data-testid="stSidebar"] .stButton > button {
        font-size: var(--dash-fs-label);
        font-weight: 600;
        border-radius: 10px;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        color: var(--dash-ink);
        border-color: rgba(203, 213, 225, 0.95);
        background: rgba(255, 255, 255, 0.92);
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        color: var(--dash-ink-strong);
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        font-size: var(--dash-fs-label);
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] details > summary {
        font-size: var(--dash-fs-label);
        font-weight: 650;
        color: var(--dash-ink);
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] details > summary:hover {
        color: var(--dash-ink-strong);
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
        font-size: var(--dash-fs-label);
        color: var(--dash-ink);
        line-height: 1.55;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
        color: var(--dash-ink-strong);
        font-weight: 650;
    }
    section[data-testid="stSidebar"] details {
        font-size: var(--dash-fs-label);
        color: var(--dash-ink);
    }
    section[data-testid="stSidebar"] [data-testid="stCaption"] {
        font-size: var(--dash-fs-micro) !important;
        color: var(--dash-ink-faint) !important;
        line-height: 1.35 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCodeBlock"] pre {
        font-size: var(--dash-fs-code-log) !important;
        color: var(--dash-ink-muted) !important;
        line-height: 1.2;
        max-height: 140px !important;
        min-height: 140px !important;
        overflow-y: auto !important;
        overflow-x: auto !important;
        padding: var(--dash-space-sm) var(--dash-space-sm) var(--dash-space-sm) var(--dash-space-sm) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCodeBlock"] code {
        font-size: var(--dash-fs-code-log) !important;
        color: var(--dash-ink-muted) !important;
    }
    .processing-line {
        display: inline-flex;
        align-items: center;
        gap: var(--dash-space-sm);
        font-size: var(--dash-fs-label);
        font-weight: 650;
        color: var(--dash-ink-strong) !important;
        margin: var(--dash-space-xs) 0 var(--dash-space-sm) 0;
    }
    .walker {
        display: inline-block;
        animation: walker-bob 0.9s ease-in-out infinite;
        transform-origin: center;
        filter: none !important;
        -webkit-text-fill-color: initial !important;
        font-style: normal;
        line-height: 1;
        /* Slight edge so emoji stays visible on pale backgrounds across OS fonts */
        text-shadow: 0 0 0.5px rgba(15, 23, 42, 0.25), 0 1px 0 rgba(255, 255, 255, 0.9);
    }
    @keyframes walker-bob {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-2px); }
        100% { transform: translateY(0px); }
    }
    /* Right column: invisible placeholder while Run is working (panel appears only after) */
    .impact-column-hold {
        min-height: 220px;
        pointer-events: none;
        position: relative;
    }
    .impact-column-hold .impact-sr-only,
    .impact-panel-shell .impact-sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    @media (prefers-reduced-motion: reduce) {
        .fun-fact-reveal { animation: none; }
    }
    @keyframes fun-fact-reveal {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fun-fact-reveal {
        animation: fun-fact-reveal 0.42s ease-out both;
    }
    /* Time back — hierarchy: hero metric (peak) → tail (support) → compare (data) → labels (meta) */
    .tb-panel {
        text-align: center;
        margin: var(--dash-space-xs) 0 var(--dash-space-md) 0;
    }
    .tb-panel--run .tb-hero {
        margin-bottom: var(--dash-space-lg);
    }
    .tb-hero {
        font-size: var(--dash-fs-hero);
        font-weight: 800;
        color: var(--dash-ink-strong);
        line-height: 1.28;
        letter-spacing: -0.03em;
        margin: 0 0 var(--dash-space-xl) 0;
    }
    .tb-hero-num {
        display: inline-block;
        font-weight: 900;
        font-size: var(--dash-fs-hero-metric);
        background: linear-gradient(120deg, #4f46e5, #7c3aed, #a855f7);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
    }
    .tb-hero-tail {
        font-weight: 700;
        font-size: var(--dash-fs-hero-tail);
        color: var(--dash-ink-muted);
        letter-spacing: -0.02em;
    }
    .tb-compare-row {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: stretch;
        gap: 0;
        max-width: min(100%, 380px);
        margin: 0 auto var(--dash-space-md) auto;
        padding: var(--dash-space-md) 10px;
        border-radius: 16px;
        background: rgba(248, 250, 252, 0.72);
        border: none;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.85);
    }
    .tb-col {
        padding: var(--dash-space-xs) var(--dash-space-sm);
        text-align: center;
    }
    .tb-col-label {
        font-size: var(--dash-fs-label);
        font-weight: 700;
        color: var(--dash-ink-muted);
        margin-bottom: var(--dash-space-sm);
        letter-spacing: 0.02em;
    }
    .tb-col-val {
        font-size: var(--dash-fs-data);
        font-weight: 800;
        color: var(--dash-ink-strong);
        letter-spacing: -0.02em;
    }
    .tb-col-val--app {
        color: #4f46e5;
    }
    .tb-col-div {
        width: 1px;
        background: linear-gradient(180deg, transparent, #cbd5e1 15%, #cbd5e1 85%, transparent);
        margin: 4px 0;
    }
    .impact-panel-processing-banner {
        font-size: var(--dash-fs-label);
        line-height: 1.45;
        color: #3730a3;
        text-align: center;
        padding: var(--dash-space-sm) var(--dash-space-md);
        margin: 0 0 var(--dash-space-md) 0;
        border-radius: 14px;
        background: linear-gradient(105deg, rgba(238, 242, 255, 0.95), rgba(250, 245, 255, 0.92));
        border: 1px solid rgba(199, 210, 254, 0.55);
    }
    .impact-panel-processing-banner strong {
        color: #4f46e5;
    }
    .impact-panel-shell--updating {
        opacity: 0.93;
    }
    .impact-panel-shell--processing {
        min-height: 200px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--dash-space-2xl) var(--dash-space-xl);
        text-align: center;
    }
    .impact-panel-processing-message {
        font-size: var(--dash-fs-body);
        font-weight: 650;
        color: var(--dash-ink);
        margin: 0;
        line-height: 1.45;
        max-width: 19rem;
    }
    /* One continuous panel surface (replaces stacked “cards”) */
    .impact-panel-shell {
        border: none;
        background: linear-gradient(
            168deg,
            rgba(255, 255, 255, 0.96) 0%,
            #f8fafc 36%,
            rgba(237, 242, 255, 0.52) 100%
        );
        border-radius: 20px;
        padding: var(--dash-space-lg) var(--dash-space-lg) var(--dash-space-lg) var(--dash-space-lg);
        margin-bottom: var(--dash-space-sm);
        box-shadow:
            0 1px 0 rgba(255, 255, 255, 0.9) inset,
            0 22px 56px -36px rgba(79, 70, 229, 0.24),
            0 4px 20px -10px rgba(15, 23, 42, 0.06);
    }
    /* Fun block: rhythm + divider, not a second boxed card */
    .impact-panel-fun {
        margin-top: 0;
        padding-top: var(--dash-space-md);
        border-top: 1px solid rgba(203, 213, 225, 0.45);
    }
    .fun-fact-sub {
        font-size: var(--dash-fs-label);
        font-weight: 700;
        color: var(--dash-ink-muted);
        margin: 0 0 var(--dash-space-sm) 0;
    }
    .fun-fact-sub--carousel {
        margin-bottom: var(--dash-space-sm);
        letter-spacing: 0.02em;
    }
    .fun-fact-sub-metric {
        font-weight: 800;
        color: var(--dash-ink);
    }
    .fun-fact-sub-kick {
        font-weight: 600;
        color: var(--dash-ink-muted);
    }
    .tb-hero-run-pill {
        display: block;
        font-size: var(--dash-fs-micro);
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7c3aed;
        margin-bottom: var(--dash-space-sm);
    }
    .impact-panel-run-empty {
        text-align: center;
        color: var(--dash-ink-muted);
        font-size: var(--dash-fs-body);
        padding: var(--dash-space-2xl) var(--dash-space-md);
        line-height: 1.5;
        max-width: 20rem;
        margin: 0 auto;
    }
    .fun-carousel-wrap {
        margin: 4px 0 6px 0;
    }
    .fun-carousel--auto {
        margin: 0 -2px;
    }
    /* Viewport: clips the marquee; soft edge fade suggests motion beyond the frame */
    .fun-carousel-viewport {
        overflow: hidden;
        padding: 10px 0 14px 0;
        margin: 0 -2px;
        -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 5%, #000 95%, transparent 100%);
        mask-image: linear-gradient(90deg, transparent 0%, #000 5%, #000 95%, transparent 100%);
    }
    @keyframes fun-marquee-scroll {
        from {
            transform: translate3d(0, 0, 0);
        }
        to {
            transform: translate3d(-50%, 0, 0);
        }
    }
    @keyframes fun-emoji-breathe {
        0%,
        100% {
            transform: translateY(0) scale(1);
        }
        50% {
            transform: translateY(-4px) scale(1.06);
        }
    }
    .fun-carousel-track--marquee {
        display: flex;
        gap: 16px;
        width: max-content;
        will-change: transform;
        animation: fun-marquee-scroll var(--fun-marquee-sec, 28s) linear infinite;
    }
    .fun-carousel--auto:hover .fun-carousel-track--marquee,
    .fun-carousel--auto:focus-within .fun-carousel-track--marquee {
        animation-play-state: paused;
    }
    .fun-carousel-track--marquee .fun-card {
        flex: 0 0 clamp(210px, 74vw, 272px);
        border-radius: 18px;
        background: linear-gradient(155deg, #ffffff 0%, #faf7ff 42%, #f0f9ff 100%);
        border: 1px solid rgba(199, 210, 254, 0.55);
        box-shadow:
            0 0 0 1px rgba(255, 255, 255, 0.65) inset,
            0 10px 36px -16px rgba(99, 102, 241, 0.35),
            0 4px 14px -8px rgba(15, 23, 42, 0.08);
        transition: transform 0.35s ease, box-shadow 0.35s ease;
    }
    .fun-carousel-track--marquee .fun-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow:
            0 0 0 1px rgba(255, 255, 255, 0.75) inset,
            0 16px 44px -14px rgba(124, 58, 237, 0.38),
            0 6px 18px -8px rgba(15, 23, 42, 0.1);
    }
    .fun-carousel-track--marquee .fun-card-emoji {
        animation: fun-emoji-breathe 2.6s ease-in-out infinite;
        filter: drop-shadow(0 3px 8px rgba(124, 58, 237, 0.2));
    }
    .fun-carousel-track--marquee .fun-card:nth-child(3n + 1) .fun-card-emoji {
        animation-delay: 0s;
    }
    .fun-carousel-track--marquee .fun-card:nth-child(3n + 2) .fun-card-emoji {
        animation-delay: 0.25s;
    }
    .fun-carousel-track--marquee .fun-card:nth-child(3n + 3) .fun-card-emoji {
        animation-delay: 0.5s;
    }
    .fun-carousel-viewport::-webkit-scrollbar {
        height: 5px;
    }
    .fun-carousel-viewport::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 999px;
    }
    .fun-card {
        flex: 0 0 min(86%, 300px);
        scroll-snap-align: start;
        border-radius: 16px;
        padding: 16px 16px 18px 16px;
        text-align: center;
        background: linear-gradient(165deg, rgba(255, 255, 255, 0.92) 0%, #faf8ff 50%, #f8fafc 100%);
        border: 1px solid rgba(226, 232, 240, 0.75);
        box-shadow: 0 2px 14px -10px rgba(99, 102, 241, 0.12);
    }
    @media (min-width: 520px) {
        .fun-card {
            flex: 0 0 calc(50% - 10px);
            min-width: 0;
            max-width: 320px;
        }
        .fun-carousel-track--marquee .fun-card {
            flex: 0 0 clamp(232px, 36vw, 288px);
            max-width: none;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .fun-carousel-track--marquee {
            animation: none !important;
        }
        .fun-carousel-viewport {
            -webkit-mask-image: none;
            mask-image: none;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
        }
        .fun-carousel-track--marquee .fun-card {
            scroll-snap-align: start;
        }
        .fun-carousel-track--marquee .fun-card-emoji {
            animation: none;
        }
    }
    .fun-card-emoji {
        font-size: 2.15rem;
        line-height: 1;
        margin-bottom: var(--dash-space-sm);
        filter: drop-shadow(0 2px 4px rgba(15, 23, 42, 0.08));
    }
    .fun-card-text {
        font-size: var(--dash-fs-body);
        font-weight: 600;
        color: var(--dash-ink);
        line-height: 1.45;
    }
    .fun-fact-whisper {
        font-size: var(--dash-fs-caption);
        color: var(--dash-ink-faint);
        margin: var(--dash-space-md) 0 0 0;
        line-height: 1.45;
    }
    .fun-fact-whisper--alltime {
        text-align: center;
        margin-top: var(--dash-space-sm);
    }
    .fun-alltime-num {
        font-weight: 800;
        color: var(--dash-ink-muted);
        font-size: var(--dash-fs-caption);
        letter-spacing: -0.02em;
    }
    .fun-alltime-k {
        font-weight: 600;
        font-size: var(--dash-fs-micro);
        color: var(--dash-ink-faint);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-left: var(--dash-space-xs);
    }
    /* Achievement chips — progress badges, not a report line */
    .stat-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: var(--dash-space-sm);
        margin-top: var(--dash-space-lg);
        margin-bottom: var(--dash-space-xs);
        justify-content: center;
    }
    .stat-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: var(--dash-space-sm) 15px var(--dash-space-sm) 11px;
        border-radius: 999px;
        font-size: var(--dash-fs-caption);
        font-weight: 650;
        letter-spacing: 0.01em;
        color: var(--dash-ink);
        background: rgba(248, 250, 252, 0.95);
        border: 1px solid rgba(226, 232, 240, 0.85);
        box-shadow: none;
    }
    .stat-chip-ico {
        font-size: var(--dash-fs-body);
        line-height: 1;
        opacity: 0.85;
    }
    /* Tabs: unselected = label tier; selected = body tier + strong ink */
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: var(--dash-fs-label) !important;
        color: var(--dash-ink-muted) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
        color: var(--dash-ink-strong) !important;
        font-weight: 650 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

input_dir = Path(input_folder)
output_dir = Path(output_folder)
archive_dir = Path(archive_root_folder)
input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)
archive_dir.mkdir(parents=True, exist_ok=True)


def _replace_input_dir_with_uploaded_pdfs(uploaded_list) -> None:
    """
    Make input/ match the current uploader selection only.

    Stale PDFs (e.g. left after a crashed run, removed from the widget, or dropped
    in the folder manually) would otherwise still be picked up by batch processing,
    inflating counts beyond len(uploaded_list).
    """
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() == ".pdf":
            try:
                path.unlink()
            except OSError:
                pass
    for uploaded in uploaded_list:
        with open(input_dir / uploaded.name, "wb") as f:
            f.write(uploaded.getbuffer())


# --- Productivity Impact (local stats, no cloud) ---
PRODUCTIVITY_STATS_PATH = Path(__file__).resolve().parent / ".streamlit_productivity_stats.json"

# --- Manual-time model (office worker → Excel) ---------------------------------
# Imagine: open PDF, read layout, find each value on the page, type it into the
# spreadsheet, quick check, then move on. One row in `rows` = one invoice/PDF.
#
# Per invoice (minutes):
#   T_manual = max(T_FLOOR, T_READ_SKIM + T_ROW_WRAP + n_filled_fields * T_FIELD)
#
#   T_READ_SKIM  — open PDF, scroll, map where vendor / dates / amounts live.
#   T_FIELD      — per cell actually filled: locate on invoice + type in Excel + glance verify.
#   T_ROW_WRAP   — finish row, next row, light sanity pass on that invoice.
#   T_FLOOR      — minimum even for sparse/OCR-weird docs (still opened and handled).
#
# Batch: sum T_manual over all rows.  minutes_saved = max(0, batch_manual − tool_run_minutes).
MANUAL_READ_SKIM_MINUTES_PER_INVOICE = 3.5
MANUAL_MINUTES_PER_FIELD_TYPED = 0.85
MANUAL_ROW_WRAP_MINUTES_PER_INVOICE = 0.55
MANUAL_MINUTES_FLOOR_PER_INVOICE = 2.75


def format_duration_hm(total_minutes: float) -> str:
    total_minutes = max(0, total_minutes)
    h = int(total_minutes // 60)
    m = int(round(total_minutes % 60))
    if m == 60:
        h += 1
        m = 0
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def format_app_runtime_display(tool_minutes: float) -> str:
    """Short label for app wall-clock time (sub-minute shows as &lt;1m when non-zero)."""
    t = max(0.0, tool_minutes)
    if t <= 0:
        return "0m"
    label = format_duration_hm(t)
    if label == "0m" and t > 0:
        return "<1m"
    return label


# Same breakpoints as static “how it feels” tiers — keep wildcard whimsy in the same scale.
_OFFICE_FUN_MINUTE_BOUNDS: tuple[float, ...] = (0.0, 10.0, 28.0, 60.0, 120.0, float("inf"))


def _office_fun_tier_index(m: float) -> int:
    """Index 0..4 for tier pools / wildcard bands from minutes saved."""
    m = max(0.0, float(m))
    bounds = _OFFICE_FUN_MINUTE_BOUNDS
    for i in range(len(bounds) - 1):
        if bounds[i] <= m < bounds[i + 1]:
            return i
    return max(0, len(bounds) - 2)


def _office_fun_static_tier_pools() -> list[list[tuple[str, str]]]:
    """Ordered from smallest to largest time tiers (minutes)."""
    return [
        [
            ("☕", "You skipped a coffee you could’ve actually finished hot"),
            ("💬", "A “quick sync” that miraculously stayed quick"),
            ("🪴", "Watering the desk plant without rushing it"),
            ("📝", "Closing that one tab row you’ve been “saving for later”"),
        ],
        [
            ("🎧", "One juicy podcast — intro ads included"),
            ("🚶", "A lunch walk long enough to forget your inbox"),
            ("📺", "A heavy episode with full emotional investment"),
            ("🎮", "A ranked match you didn’t rage-quit"),
        ],
        [
            ("🧘", "Two yoga classes — shavasana non-negotiable"),
            ("🍿", "A full movie: credits, bloopers, snack refill"),
            ("🎳", "Bowling + fries + regrettable shoes"),
            ("🛋", "An honest couch reset with zero guilt"),
        ],
        [
            ("🚗", "You skipped a full LA commute arc (traffic is character development)"),
            ("🧘", "That’s like two yoga classes, savasana included"),
            ("🍿", "A whole movie night — previews count"),
            ("🎧", "A deep-dive playlist rabbit hole"),
        ],
        [
            ("✈️", "You skipped 2 hours of “are we boarding yet?” airport brain"),
            ("🚗", "That’s like driving across LA… twice"),
            ("🎢", "Half a theme park day back 🎟"),
            ("🍿", "Director’s cut energy — plus commentary snacks"),
            ("🛫", "The “we still have two hours” gate wait, twice"),
        ],
    ]


def _office_fun_parametric_cards(m: float) -> list[tuple[str, str]]:
    """
    Scale-aware lines so very large savings are not stuck repeating the same 2h+ jokes.
    Kept short for carousel cards.
    """
    if m < 4:
        return []
    out: list[tuple[str, str]] = []
    hm = format_duration_hm(m)

    n25 = max(1, round(m / 25))
    if n25 <= 24:
        out.append(("🍅", f"About {n25} uninterrupted 25-minute stretches"))

    n45 = max(1, round(m / 45))
    if 2 <= n45 <= 16 and abs(n45 - n25) >= 1:
        out.append(("🧱", f"Roughly {n45} deep-work blocks the length of a class period"))

    n30 = max(1, round(m / 30))
    if 3 <= n30 <= 36:
        out.append(("📆", f"Almost {n30} calendar half-hours you didn’t burn"))

    n22 = max(1, round(m / 22))
    if 4 <= n22 <= 40:
        out.append(("📺", f"Call it {n22} sitcom-length chunks you didn’t sit through"))

    if m >= 75:
        out.append(("🕰️", f"Stacked up, about {hm} you didn’t donate to grunt work"))

    if m >= 150:
        out.append(("🌅", f"Enough breathing room to feel like a {hm} morning you got back"))

    return out


# Wildcard lines are tier-banded to minutes saved (same breakpoints as static pools) so
# a “grocery run” vibe doesn’t show up on a 6-minute win, and sock-tier whimsy doesn’t
# headline a 3-hour batch. rng_key still perturbs which line within the band.
_OFFICE_FUN_WILDCARDS_BY_TIER: list[list[tuple[str, str]]] = [
    # ~0–10m: tiny desk / micro-break wins
    [
        ("🧦", "Finding matching socks on the first try"),
        ("💺", "Rolling your chair without hitting the desk edge"),
        ("🥤", "A cold drink that stayed cold the whole way through"),
        ("🧴", "Hand lotion that actually absorbed"),
        ("🎹", "Tapping a keyboard rhythm that wasn’t stress typing"),
        ("🌿", "Remembering to stretch before your neck complained"),
        ("🧵", "A thread that didn’t snag when you pulled it"),
        ("🔧", "Adjusting the chair height once and leaving it"),
        ("🪟", "Closing the blinds for focus, not doom"),
        ("🧠", "One thought you finished instead of tab-hopping"),
        ("🧊", "Ice that didn’t immediately water down the drink"),
        ("🎵", "A song stuck in your head you still like"),
    ],
    # ~10–28m: coffee-break / short errand scale
    [
        ("🥪", "Lunch where you actually tasted the sandwich"),
        ("🐕", "A dog walk without checking email once"),
        ("🧹", "The ‘inbox zero’ fantasy — briefly believable"),
        ("🌧️", "Staring out the window during drizzle, guilt-free"),
        ("🛎️", "Someone else answered the door"),
        ("🧃", "Hydration you didn’t have to rush between meetings"),
        ("🛏️", "Making the bed even though nobody’s visiting"),
        ("🍪", "Cookies from the office kitchen — still warm"),
        ("🌤️", "Checking the weather without spiraling into news"),
        ("🎟️", "A calendar reminder you were happy to see"),
        ("🧸", "Putting something back where it actually belongs"),
        ("📬", "An empty ‘unread’ badge for a real stretch of focus"),
    ],
    # ~28–60m: half-hour to “one solid block” scale
    [
        ("🧽", "Dishes done the same day you cooked"),
        ("🚿", "A shower long enough to have a subplot"),
        ("📬", "Inbox quiet long enough you forgot what you were avoiding"),
        ("🧘", "A reset long enough that your shoulders unclench"),
        ("🎧", "A playlist deep enough to forget you were “just taking a break”"),
        ("🚶", "A walk where you didn’t once think about the spreadsheet"),
        ("🧺", "Laundry folded while it was still warm"),
        ("📞", "A catch-up call where nobody said “real quick”"),
        ("🍳", "Cooking something that wasn’t “whatever’s fastest”"),
        ("🌆", "Golden-hour light you noticed on purpose"),
    ],
    # ~60–120m: movie / errand / long-session scale
    [
        ("🛒", "A grocery run with zero forgotten-aisle U-turns"),
        ("🎬", "Enough time to actually watch the movie, not just the trailer"),
        ("📚", "That “I’ll read tonight” stack finally got opened"),
        ("🛋", "A slow evening where the couch isn’t doing emergency rescue duty"),
        ("🧳", "Weekend-errand energy without the Sunday panic"),
        ("🚗", "The gap between “I should leave” and “I’m late” — generously spared"),
        ("🍿", "Snacks chosen on purpose, not stress-grabbed on the way out"),
        ("🎮", "One game session where you weren’t clock-watching"),
    ],
    # 120m+: multi-hour / “big chunk of life back” scale
    [
        ("✈️", "Enough runway that travel prep isn’t your whole personality"),
        ("🌅", "A whole morning margin — not just coffee between meetings"),
        ("🎢", "Half a theme park day’s worth of standing in the wrong line — skipped"),
        ("🛫", "Gate-wait brain you didn’t have to donate to the airline"),
        ("🧭", "A day chunk big enough to change the plan, not just survive it"),
        ("🎟", "Director’s-cut energy — plus commentary snacks"),
        ("🌌", "An evening that feels wide instead of wedged between tasks"),
        ("🏠", "Home early enough that takeout is a choice, not a crisis"),
    ],
]


def _card_text_key(text: str) -> str:
    """Normalize carousel line text for dedupe / cross-tab exclusion."""
    return (text or "").strip()


def _exclude_text_set(exclude: frozenset[str] | None) -> set[str]:
    if not exclude:
        return set()
    return {k for t in exclude if (k := _card_text_key(t))}


def _pick_wildcard_card(
    rng_key: str,
    minutes_saved: float,
    exclude_text_keys: set[str] | None = None,
) -> tuple[str, str]:
    ex = exclude_text_keys or set()
    tier_idx = _office_fun_tier_index(minutes_saved)
    bands = _OFFICE_FUN_WILDCARDS_BY_TIER
    pool: list[tuple[str, str]] = list(bands[tier_idx])
    if len(pool) < 4:
        for delta in (-1, 1, -2, 2):
            j = tier_idx + delta
            if 0 <= j < len(bands):
                pool.extend(x for x in bands[j] if x not in pool)
            if len(pool) >= 8:
                break
    if not pool:
        pool = [("✨", "A little time back that’s yours again")]
    filtered = [x for x in pool if _card_text_key(x[1]) not in ex]
    use = filtered if filtered else pool
    r = random.Random(f"wildcard::{rng_key}::t{tier_idx}")
    return r.choice(use)


def _wildcard_pad_candidates(minutes_saved: float) -> list[tuple[str, str]]:
    """Padding lines for the carousel — same tier first, then one neighbor band."""
    tier_idx = _office_fun_tier_index(minutes_saved)
    bands = _OFFICE_FUN_WILDCARDS_BY_TIER
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for j in (tier_idx, tier_idx - 1, tier_idx + 1):
        if 0 <= j < len(bands):
            for x in bands[j]:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
    return out


def _finalize_distinct_cards(
    ordered: list[tuple[str, str]],
    *,
    spare_pool: list[tuple[str, str]],
    rng: random.Random,
    external_exclude_keys: set[str],
    k: int = 3,
) -> list[tuple[str, str]]:
    """Up to k cards with unique lines; skips external_exclude_keys (e.g. other tab’s lines)."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for em, t in ordered:
        key = _card_text_key(t)
        if not key or key in seen or key in external_exclude_keys:
            continue
        out.append((em, t))
        seen.add(key)
        if len(out) >= k:
            return out
    spare = list(spare_pool)
    rng.shuffle(spare)
    for em, t in spare:
        key = _card_text_key(t)
        if not key or key in seen or key in external_exclude_keys:
            continue
        out.append((em, t))
        seen.add(key)
        if len(out) >= k:
            break
    return out[:k]


def office_fun_cards(
    minutes_saved: float,
    rng_key: str,
    *,
    exclude_card_texts: frozenset[str] | None = None,
) -> list[tuple[str, str]]:
    """Three (emoji, line) pairs: wildcard + tier/parametric, all lines unique; optional cross-tab exclude."""
    rng = random.Random(f"{rng_key}_{int(max(0.0, minutes_saved))}")
    m = max(0.0, minutes_saved)
    ex_keys = _exclude_text_set(exclude_card_texts)
    tiers = _office_fun_static_tier_pools()

    tier_idx = _office_fun_tier_index(m)

    combined: list[tuple[str, str]] = list(tiers[tier_idx])

    # Blend a couple of lines from the tier below for variety (skip lowest tier).
    if tier_idx > 0:
        lower = list(tiers[tier_idx - 1])
        rng.shuffle(lower)
        combined.extend(lower[:2])

    # Mega tier: also sprinkle mid-tier color so the pool is not only “airport + LA”.
    if tier_idx == len(tiers) - 1:
        mid = list(tiers[2]) + list(tiers[3])
        rng.shuffle(mid)
        combined.extend(mid[:2])

    combined.extend(_office_fun_parametric_cards(m))

    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for em, txt in combined:
        key = _card_text_key(txt)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append((em, txt))

    rng.shuffle(deduped)

    wild = _pick_wildcard_card(rng_key, m, ex_keys)
    wild_key = _card_text_key(wild[1])
    rest = [
        (e, t)
        for e, t in deduped
        if _card_text_key(t) != wild_key and _card_text_key(t) not in ex_keys
    ]
    rng.shuffle(rest)
    others: list[tuple[str, str]] = list(rest[:2])
    if len(others) < 2:
        r_pad = random.Random(f"wildcard_pad::{rng_key}")
        pad_pool = [
            w
            for w in _wildcard_pad_candidates(m)
            if _card_text_key(w[1]) != wild_key
            and _card_text_key(w[1]) not in ex_keys
            and all(_card_text_key(w[1]) != _card_text_key(o[1]) for o in others)
        ]
        r_pad.shuffle(pad_pool)
        for w in pad_pool:
            if len(others) >= 2:
                break
            others.append(w)

    base = [wild] + others[:2]
    base = base[:3]
    if not base:
        return []
    if len(base) == 1:
        return _finalize_distinct_cards(
            base,
            spare_pool=deduped + _wildcard_pad_candidates(m) + _office_fun_parametric_cards(m),
            rng=rng,
            external_exclude_keys=ex_keys,
            k=3,
        )
    pos_rng = random.Random(f"wildcard_pos::{rng_key}")
    pos = pos_rng.randint(0, len(base) - 1)
    wild_idx = next(i for i, x in enumerate(base) if _card_text_key(x[1]) == wild_key)
    rot = (pos - wild_idx) % len(base)
    rotated = [base[(i + rot) % len(base)] for i in range(len(base))]
    spare_seen: set[str] = set()
    spare_unique: list[tuple[str, str]] = []
    for em, t in deduped + _wildcard_pad_candidates(m) + _office_fun_parametric_cards(m):
        k2 = _card_text_key(t)
        if not k2 or k2 in spare_seen:
            continue
        spare_seen.add(k2)
        spare_unique.append((em, t))
    return _finalize_distinct_cards(
        rotated,
        spare_pool=spare_unique,
        rng=rng,
        external_exclude_keys=ex_keys,
        k=3,
    )


def _impact_carousel_html(
    mins_for_cards: float,
    rng_key: str,
    *,
    exclude_card_texts: frozenset[str] | None = None,
    register_card_texts: set[str] | None = None,
) -> str:
    """
    Label + auto carousel, only when there is real time back to anchor the copy.
    (No generic “how it feels” carousel before any PDFs / zero savings.)
    """
    m = max(0.0, float(mins_for_cards or 0.0))
    if m <= 0:
        return ""
    hm = html.escape(format_duration_hm(m))
    sub = (
        f'<div class="fun-fact-sub fun-fact-sub--carousel">'
        f'<span aria-hidden="true">⏱️ </span>About <span class="fun-fact-sub-metric">{hm}</span> back '
        f'<span class="fun-fact-sub-kick">— how it feels</span></div>'
    )
    cards = office_fun_cards(m, rng_key, exclude_card_texts=exclude_card_texts)
    if register_card_texts is not None:
        register_card_texts.update(_card_text_key(t) for _, t in cards)
    return sub + build_fun_carousel_html(cards)


def build_fun_carousel_html(cards: list[tuple[str, str]]) -> str:
    def one_card(em: str, txt: str) -> str:
        return (
            f'<article class="fun-card">'
            f'<div class="fun-card-emoji" aria-hidden="true">{html.escape(em)}</div>'
            f'<div class="fun-card-text">{html.escape(txt)}</div>'
            "</article>"
        )

    inner_cards = "".join(one_card(em, txt) for em, txt in cards)
    # Duplicated set for a seamless CSS marquee (translate -50% = one lap).
    inner = inner_cards + inner_cards
    n = max(len(cards), 1)
    dur_sec = max(20, min(46, 8 * n + 10))

    return (
        '<div class="fun-carousel-wrap">'
        '<div class="fun-carousel fun-carousel--auto" role="region" aria-roledescription="carousel" '
        'aria-label="What your time back feels like. Auto-scrolls; hover to pause." aria-live="off">'
        '<div class="fun-carousel-viewport">'
        f'<div class="fun-carousel-track fun-carousel-track--marquee" style="--fun-marquee-sec: {dur_sec}s">'
        f"{inner}</div></div></div></div>"
    )


def _iso_week_key(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _backfill_lifetime_from_weeks(data: dict) -> None:
    """Older JSON had no lifetime tool/manual totals — sum week buckets when missing."""
    weeks = data.get("weeks") or {}
    if float(data.get("lifetime_tool_seconds_total", 0) or 0) <= 0:
        tsum = sum(
            float(wd.get("tool_seconds_total", 0) or 0) for wd in weeks.values() if isinstance(wd, dict)
        )
        if tsum > 0:
            data["lifetime_tool_seconds_total"] = tsum
    if float(data.get("lifetime_manual_minutes_est", 0) or 0) <= 0:
        msum = sum(
            float(wd.get("manual_minutes_est", 0) or 0) for wd in weeks.values() if isinstance(wd, dict)
        )
        if msum > 0:
            data["lifetime_manual_minutes_est"] = msum


def load_productivity_stats() -> dict:
    if not PRODUCTIVITY_STATS_PATH.is_file():
        return {
            "weeks": {},
            "days": {},
            "lifetime_minutes_saved": 0.0,
            "lifetime_manual_minutes_est": 0.0,
            "lifetime_tool_seconds_total": 0.0,
        }
    try:
        raw = json.loads(PRODUCTIVITY_STATS_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {
                "weeks": {},
                "days": {},
                "lifetime_minutes_saved": 0.0,
                "lifetime_manual_minutes_est": 0.0,
                "lifetime_tool_seconds_total": 0.0,
            }
        raw.setdefault("weeks", {})
        raw.setdefault("days", {})
        raw.setdefault("lifetime_minutes_saved", 0.0)
        raw.setdefault("lifetime_manual_minutes_est", 0.0)
        raw.setdefault("lifetime_tool_seconds_total", 0.0)
        _backfill_lifetime_from_weeks(raw)
        return raw
    except Exception:
        return {
            "weeks": {},
            "days": {},
            "lifetime_minutes_saved": 0.0,
            "lifetime_manual_minutes_est": 0.0,
            "lifetime_tool_seconds_total": 0.0,
        }


def save_productivity_stats(data: dict) -> None:
    try:
        PRODUCTIVITY_STATS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def week_model_minutes(cur: dict) -> tuple[float, float, float]:
    """
    (manual_minutes_est, tool_minutes, minutes_saved) for display.
    Older stats files only stored minutes_saved + tool time — infer manual as saved + tool.
    """
    saved = float(cur.get("minutes_saved", 0) or 0)
    tool_sec = float(cur.get("tool_seconds_total", 0) or 0)
    tool_min = tool_sec / 60.0
    manual = float(cur.get("manual_minutes_est", 0) or 0)
    if manual <= 0 and (saved > 0 or tool_min > 0):
        manual = saved + tool_min
    return (manual, tool_min, saved)


def lifetime_model_minutes(data: dict) -> tuple[float, float, float]:
    """Same logic as week_model_minutes for all-time aggregates."""
    saved = float(data.get("lifetime_minutes_saved", 0) or 0)
    tool_sec = float(data.get("lifetime_tool_seconds_total", 0) or 0)
    tool_min = tool_sec / 60.0
    manual = float(data.get("lifetime_manual_minutes_est", 0) or 0)
    if manual <= 0 and (saved > 0 or tool_min > 0):
        manual = saved + tool_min
    return (manual, tool_min, saved)


def today_calendar_key(d: datetime | None = None) -> str:
    return (d or datetime.now()).strftime("%Y-%m-%d")


def today_saved_minutes(data: dict, d: datetime | None = None) -> float:
    """Minutes saved today (local calendar day), same manual − tool model as weeks."""
    day = (data.get("days") or {}).get(today_calendar_key(d)) or {}
    manual, tool, _ = week_model_minutes(day)
    return max(0.0, manual - tool)


def count_filled_fields_in_row(row: dict) -> int:
    """How many non-empty Excel cells this invoice row would need a human to handle."""
    n = 0
    for v in row.values():
        if v is None or v == "" or v == "未识别":
            continue
        n += 1
    return n


def count_filled_fields(rows: list) -> int:
    return sum(count_filled_fields_in_row(r) if isinstance(r, dict) else 0 for r in rows)


def estimate_manual_invoice_reentry_minutes(rows: list) -> float:
    """
    Total estimated minutes if a worker manually processed the same set of invoices
    into Excel (read PDF → find values → type → quick verify per field).
    """
    total = 0.0
    for row in rows:
        if not isinstance(row, dict):
            continue
        n_fields = count_filled_fields_in_row(row)
        per_doc = (
            MANUAL_READ_SKIM_MINUTES_PER_INVOICE
            + MANUAL_ROW_WRAP_MINUTES_PER_INVOICE
            + n_fields * MANUAL_MINUTES_PER_FIELD_TYPED
        )
        total += max(MANUAL_MINUTES_FLOOR_PER_INVOICE, per_doc)
    return total


def compute_batch_productivity_metrics(rows: list, run_seconds: float) -> dict:
    """Per-batch manual estimate, app time, and time back (same basis as week stats)."""
    if not rows:
        return {
            "docs": 0,
            "fields": 0,
            "manual_minutes_est": 0.0,
            "tool_minutes": 0.0,
            "minutes_saved": 0.0,
        }
    manual_est = estimate_manual_invoice_reentry_minutes(rows)
    tool_minutes = max(run_seconds / 60.0, 0.25)
    minutes_saved = max(0.0, manual_est - tool_minutes)
    return {
        "docs": len(rows),
        "fields": count_filled_fields(rows),
        "manual_minutes_est": manual_est,
        "tool_minutes": tool_minutes,
        "minutes_saved": minutes_saved,
    }


def record_productivity_from_run(rows: list, run_seconds: float) -> None:
    """After a successful batch, fold estimates into this ISO week + lifetime."""
    if not rows:
        return
    m = compute_batch_productivity_metrics(rows, run_seconds)
    now = datetime.now()
    wk = _iso_week_key(now)
    docs = m["docs"]
    fields = m["fields"]
    manual_est = m["manual_minutes_est"]
    minutes_saved = m["minutes_saved"]

    data = load_productivity_stats()
    weeks = data["weeks"]
    cur = weeks.get(wk) or {
        "docs": 0,
        "fields_filled": 0,
        "minutes_saved": 0.0,
        "manual_minutes_est": 0.0,
        "tool_seconds_total": 0.0,
        "runs": 0,
    }
    cur.setdefault("manual_minutes_est", 0.0)
    cur["docs"] = int(cur.get("docs", 0)) + docs
    cur["fields_filled"] = int(cur.get("fields_filled", 0)) + fields
    cur["minutes_saved"] = float(cur.get("minutes_saved", 0)) + minutes_saved
    cur["manual_minutes_est"] = float(cur.get("manual_minutes_est", 0)) + manual_est
    cur["tool_seconds_total"] = float(cur.get("tool_seconds_total", 0)) + run_seconds
    cur["runs"] = int(cur.get("runs", 0)) + 1
    weeks[wk] = cur
    data["lifetime_minutes_saved"] = float(data.get("lifetime_minutes_saved", 0)) + minutes_saved
    data["lifetime_manual_minutes_est"] = float(data.get("lifetime_manual_minutes_est", 0)) + manual_est
    data["lifetime_tool_seconds_total"] = float(data.get("lifetime_tool_seconds_total", 0)) + run_seconds

    day_key = today_calendar_key(now)
    days = data.setdefault("days", {})
    day = days.get(day_key) or {
        "minutes_saved": 0.0,
        "manual_minutes_est": 0.0,
        "tool_seconds_total": 0.0,
        "runs": 0,
    }
    day.setdefault("manual_minutes_est", 0.0)
    day["minutes_saved"] = float(day.get("minutes_saved", 0)) + minutes_saved
    day["manual_minutes_est"] = float(day.get("manual_minutes_est", 0)) + manual_est
    day["tool_seconds_total"] = float(day.get("tool_seconds_total", 0)) + run_seconds
    day["runs"] = int(day.get("runs", 0)) + 1
    days[day_key] = day

    save_productivity_stats(data)


def _compose_impact_run_tab_html(
    *,
    last_run: dict | None,
    processing: bool,
    carousel_quote_bucket: set[str] | None = None,
) -> str:
    """Last completed batch: manual estimate vs app time, time back, carousel, chips."""
    banner = ""
    if processing:
        banner = (
            '<div class="impact-panel-processing-banner" role="status" aria-live="polite">'
            '<span aria-hidden="true">⏳ </span><strong>Updating…</strong>'
            '<span class="impact-sr-only">This tab will refresh when the run completes.</span>'
            "</div>"
        )

    if not last_run:
        return (
            f'<div class="impact-panel-shell fun-fact-reveal">{banner}'
            '<p class="impact-panel-run-empty"><span aria-hidden="true">⏱️ </span>'
            "This tab shows how much time you got back from repetitive work.</p></div>"
        )

    m = last_run
    saved = float(m.get("minutes_saved", 0) or 0)
    manual_est = float(m.get("manual_minutes_est", 0) or 0)
    tool_m = float(m.get("tool_minutes", 0) or 0)
    docs = int(m.get("docs", 0) or 0)
    fields = int(m.get("fields", 0) or 0)

    saved_label = format_duration_hm(saved)
    saved_h = html.escape(saved_label)
    manual_h = html.escape(format_duration_hm(manual_est))
    app_h = html.escape(format_app_runtime_display(tool_m))
    hero_a11y = html.escape(
        f"This run: about {format_duration_hm(manual_est)} estimated manual minutes, "
        f"{saved_label} time back; app ran about {format_app_runtime_display(tool_m)}."
    )
    rng_key = f"run::{docs}_{fields}_{int(max(0.0, saved) * 10)}"
    carousel = _impact_carousel_html(
        saved,
        rng_key,
        exclude_card_texts=frozenset(carousel_quote_bucket) if carousel_quote_bucket is not None else None,
        register_card_texts=carousel_quote_bucket,
    )
    fun_block = f'<div class="impact-panel-fun">{carousel}</div>' if carousel else ""

    inv_word = "invoice" if docs == 1 else "invoices"
    field_word = "field" if fields == 1 else "fields"
    chips_html = f"""
<div class="stat-chip-row" aria-label="This run progress">
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">📄</span> {html.escape(str(docs))} {inv_word}</span>
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">📊</span> {html.escape(str(fields))} {field_word}</span>
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">⚡</span> 1 run</span>
</div>
"""

    shell_classes = "impact-panel-shell fun-fact-reveal"
    if processing:
        shell_classes += " impact-panel-shell--updating"

    contrast_html = f"""
<div class="tb-panel tb-panel--run">
  <span class="tb-hero-run-pill">This run</span>
  <p class="tb-hero">
    <span class="impact-sr-only">{hero_a11y}</span>
    <span aria-hidden="true">⏱ </span><span class="tb-hero-num">{saved_h}</span><span class="tb-hero-tail" aria-hidden="true"> time back</span>
  </p>
  <div class="tb-compare-row">
    <div class="tb-col">
      <div class="tb-col-label">🧍 Typist pace</div>
      <div class="tb-col-val">{manual_h}</div>
    </div>
    <div class="tb-col-div" aria-hidden="true"></div>
    <div class="tb-col">
      <div class="tb-col-label">⚙️ App time</div>
      <div class="tb-col-val tb-col-val--app">{app_h}</div>
    </div>
  </div>
</div>
"""

    return f"""
<div class="{shell_classes}">
{banner}{contrast_html}
{fun_block}
{chips_html}
</div>
"""


def _compose_impact_week_tab_html(
    *,
    cur: dict,
    wk: str,
    data: dict,
    processing: bool,
    carousel_quote_bucket: set[str] | None = None,
) -> str:
    """Weekly rollup from last saved stats. When processing=True, snapshot until the run commits."""
    life_manual, life_tool_min, _life_stored = lifetime_model_minutes(data)
    life_min = max(0.0, life_manual - life_tool_min)
    manual_week, tool_week_min, _saved_stored = week_model_minutes(cur)
    mins_this = max(0.0, manual_week - tool_week_min)
    docs = int(cur.get("docs", 0) or 0)
    fields_week = int(cur.get("fields_filled", 0) or 0)
    runs = int(cur.get("runs", 0) or 0)

    saved_label = format_duration_hm(mins_this)
    hero_num = html.escape(saved_label)
    manual_disp = html.escape(format_duration_hm(manual_week))
    app_disp = html.escape(format_app_runtime_display(tool_week_min))

    hero_a11y = html.escape(f"You got {saved_label} back this week")
    contrast_html = f"""
<div class="tb-panel tb-panel--week">
  <span class="tb-hero-run-pill">This week</span>
  <p class="tb-hero">
    <span class="impact-sr-only">{hero_a11y}</span>
    <span aria-hidden="true">⏱ </span><span class="tb-hero-num">{hero_num}</span><span class="tb-hero-tail" aria-hidden="true"> time back</span>
  </p>
  <div class="tb-compare-row">
    <div class="tb-col">
      <div class="tb-col-label">🧍 Manual</div>
      <div class="tb-col-val">{manual_disp}</div>
    </div>
    <div class="tb-col-div" aria-hidden="true"></div>
    <div class="tb-col">
      <div class="tb-col-label">⚙️ App</div>
      <div class="tb-col-val tb-col-val--app">{app_disp}</div>
    </div>
  </div>
</div>
"""

    comparisons_block = _impact_carousel_html(
        mins_this,
        f"week::{wk}",
        exclude_card_texts=frozenset(carousel_quote_bucket) if carousel_quote_bucket is not None else None,
        register_card_texts=None,
    )

    lw_s = html.escape(format_duration_hm(life_min))
    whisper_html = (
        f'<p class="fun-fact-whisper fun-fact-whisper--alltime" title="Time back, all completed runs">'
        f'<span class="fun-alltime-num">{lw_s}</span><span class="fun-alltime-k">all-time</span></p>'
    )

    inv_word = "invoice" if docs == 1 else "invoices"
    field_word = "field" if fields_week == 1 else "fields"
    run_word = "run" if runs == 1 else "runs"
    chips_html = f"""
<div class="stat-chip-row" aria-label="This week progress">
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">📄</span> {html.escape(str(docs))} {inv_word} processed</span>
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">📊</span> {html.escape(str(fields_week))} {field_word} extracted</span>
  <span class="stat-chip"><span class="stat-chip-ico" aria-hidden="true">⚡</span> {html.escape(str(runs))} {run_word} completed</span>
</div>
"""

    banner = ""
    if processing:
        banner = (
            '<div class="impact-panel-processing-banner" role="status" aria-live="polite">'
            '<span aria-hidden="true">⏳ </span><strong>Updating…</strong>'
            '<span class="impact-sr-only">'
            "Totals below are your last saved week; they refresh when this run completes. "
            "Nothing is cleared between runs."
            "</span>"
            "</div>"
        )

    shell_classes = "impact-panel-shell fun-fact-reveal"
    if processing:
        shell_classes += " impact-panel-shell--updating"

    return f"""
<div class="{shell_classes}">
{banner}{contrast_html}
<div class="impact-panel-fun">
  {comparisons_block}
  {whisper_html}
</div>
{chips_html}
</div>
"""


def _compose_impact_processing_first_run_html() -> str:
    """First completed run of the ISO week is still in progress — no prior week stats to show."""
    return """
<div class="impact-panel-shell impact-panel-shell--processing fun-fact-reveal" aria-busy="true">
  <p class="impact-panel-processing-message">
    <span aria-hidden="true">⏳ </span>Summary lands here when this run finishes
  </p>
  <span class="impact-sr-only">First batch this week. Totals are not cleared at run start; they update when processing completes.</span>
</div>
"""


def render_productivity_impact_panel() -> None:
    wk = _iso_week_key(datetime.now())
    data = load_productivity_stats()
    weeks = data.get("weeks") or {}
    cur = weeks.get(wk) or {}
    runs = int(cur.get("runs", 0) or 0)
    queued = bool(st.session_state.get("invoice_run_queued"))
    # While a run is queued and this ISO week has no completed runs yet, show the single
    # “summary when this run finishes” panel. Otherwise show tabs (zeros after clear / new week).
    has_panel_story = runs > 0

    if queued:
        if has_panel_story:
            tab_run, tab_week = st.tabs(["This run", "This week"])
            quote_bucket: set[str] = set()
            last_run = st.session_state.get("impact_last_run")
            with tab_run:
                st.markdown(
                    _compose_impact_run_tab_html(
                        last_run=last_run,
                        processing=True,
                        carousel_quote_bucket=quote_bucket,
                    ),
                    unsafe_allow_html=True,
                )
            with tab_week:
                st.markdown(
                    _compose_impact_week_tab_html(
                        cur=cur,
                        wk=wk,
                        data=data,
                        processing=True,
                        carousel_quote_bucket=quote_bucket,
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(_compose_impact_processing_first_run_html(), unsafe_allow_html=True)
        return

    # No saved week data yet (or cleared): still show the tabbed panel at zeros / nudge copy
    # instead of an empty column, so "Clear stats" feels like a reset, not a disappearance.
    tab_run, tab_week = st.tabs(["This run", "This week"])
    quote_bucket: set[str] = set()
    last_run = st.session_state.get("impact_last_run")
    with tab_run:
        st.markdown(
            _compose_impact_run_tab_html(
                last_run=last_run,
                processing=False,
                carousel_quote_bucket=quote_bucket,
            ),
            unsafe_allow_html=True,
        )
    with tab_week:
        st.markdown(
            _compose_impact_week_tab_html(
                cur=cur,
                wk=wk,
                data=data,
                processing=False,
                carousel_quote_bucket=quote_bucket,
            ),
            unsafe_allow_html=True,
        )


def _open_explorer_folder(path: Path) -> None:
    subprocess.Popen(["explorer", str(path)])


def _render_quick_folder_buttons(key_prefix: str) -> None:
    """Open Input / Archive / Output on disk (Windows Explorer)."""
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "📥 Input",
            use_container_width=True,
            key=f"{key_prefix}_folder_input",
        ):
            try:
                _open_explorer_folder(input_dir)
                st.toast("Opened Input folder")
            except Exception as e:
                st.error(f"Couldn't open folder: {e}")
    with c2:
        if st.button(
            "🗂 Archive",
            use_container_width=True,
            key=f"{key_prefix}_folder_archive",
        ):
            try:
                _open_explorer_folder(archive_dir)
                st.toast("Opened Archive folder")
            except Exception as e:
                st.error(f"Couldn't open folder: {e}")
    with c3:
        if st.button(
            "📤 Output",
            use_container_width=True,
            key=f"{key_prefix}_folder_output",
        ):
            try:
                _open_explorer_folder(output_dir)
                st.toast("Opened Output folder")
            except Exception as e:
                st.error(f"Couldn't open folder: {e}")


def _render_time_back_methodology_sidebar() -> None:
    """Methodology is secondary; keep the main column for outcomes and delight."""
    with st.expander("ⓘ Time back — how we calculate it", expanded=False):
        st.markdown(
            f"""
**Per PDF (manual-time guess)**  
We add:

- **Read / skim** the layout: ~{MANUAL_READ_SKIM_MINUTES_PER_INVOICE:g} min  
- **Row wrap** in Excel (move on, quick check): ~{MANUAL_ROW_WRAP_MINUTES_PER_INVOICE:g} min  
- **Each filled field** (find on the invoice + type + glance): ~{MANUAL_MINUTES_PER_FIELD_TYPED:g} min  
- **Floor** so even messy PDFs still count for a little time: ~{MANUAL_MINUTES_FLOOR_PER_INVOICE:g} min minimum per invoice  

**Time back** = that estimated manual total **minus** how long this app actually ran for the batch.  
Week and lifetime totals sum those gaps. Nothing leaves your PC.
"""
        )


st.title("PDFs → Excel ✨")
st.caption("Drop in your invoices, click run, and download a clean Excel file. Everything stays on your PC.")
st.caption("Folder shortcuts — open where PDFs and Excel are stored on this PC:")
_render_quick_folder_buttons("main")

with st.sidebar:
    _render_time_back_methodology_sidebar()
    with st.expander("Tech details", expanded=False):
        st.caption("Low-priority logs")
        logs = st.session_state.get("last_log_lines", [])
        if logs:
            st.code("\n".join(logs), language="text")
        else:
            st.caption("No logs yet.")

    with st.expander("Local time-back data", expanded=False):
        st.caption(
            "Weekly totals and the “This run” tab use a small JSON file on this PC only. "
            "Deleting it does not remove your PDFs or Excel files."
        )
        st.caption(f"Path: `{PRODUCTIVITY_STATS_PATH}`")
        purge_ok = st.checkbox(
            "I understand saved time-back stats will be permanently removed.",
            key="impact_stats_purge_confirm",
        )
        if st.button(
            "Clear stats",
            disabled=not purge_ok,
            use_container_width=True,
        ):
            try:
                if PRODUCTIVITY_STATS_PATH.is_file():
                    PRODUCTIVITY_STATS_PATH.unlink()
                st.session_state["impact_last_run"] = None
                st.toast("Local time-back stats cleared.")
            except OSError as e:
                st.error(f"Could not remove stats file: {e}")
            else:
                st.rerun()

if "last_rows" not in st.session_state:
    st.session_state["last_rows"] = []
if "last_output_file" not in st.session_state:
    st.session_state["last_output_file"] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "last_log_lines" not in st.session_state:
    st.session_state["last_log_lines"] = []
if "invoice_run_queued" not in st.session_state:
    st.session_state["invoice_run_queued"] = False
if "impact_last_run" not in st.session_state:
    st.session_state["impact_last_run"] = None

col_work, col_impact = st.columns([1.15, 1], gap="large")

with col_work:
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Drag and drop one or more invoice PDFs.",
        key=f"uploader_{st.session_state['uploader_key']}",
    )
    if uploaded_files:
        _replace_input_dir_with_uploaded_pdfs(uploaded_files)
        st.caption(f"{len(uploaded_files)} file(s) uploaded and ready.")

    st.markdown(
        '<div class="section-process"><div class="section-title">Process</div></div>',
        unsafe_allow_html=True,
    )
    process_clicked = st.button(
        "Run",
        type="primary",
        use_container_width=True,
        disabled=not bool(uploaded_files),
        help="Processes uploaded PDFs using pdfplumber when possible, otherwise Poppler → Tesseract OCR, "
        "then regex/heuristic field extraction.",
    )

    if process_clicked and uploaded_files:
        st.session_state["invoice_run_queued"] = True

with col_impact:
    render_productivity_impact_panel()

with col_work:
    if st.session_state.get("invoice_run_queued"):
        run_started = time.perf_counter()
        st.toast("Processing started")
        processing_title = st.empty()
        processing_title.markdown(
            '<div class="processing-line">Working on your invoices <span class="walker">🚶</span></div>',
            unsafe_allow_html=True,
        )
        try:
            progress_bar = st.progress(0, text="Starting…")
        except TypeError:
            progress_bar = st.progress(0)
        log_lines: list[str] = []

        class StreamlitLogHandler(logging.Handler):
            def emit(self, record):
                msg = self.format(record)
                log_lines.append(msg)
                if len(log_lines) > 200:
                    del log_lines[:50]

        def on_progress(current, total, message):
            ratio = 0 if total <= 0 else min(max(current / total, 0), 1)
            pct = int(round(ratio * 100))
            label = f"{pct}% — {message}" if total > 0 else message
            try:
                progress_bar.progress(ratio, text=label)
            except TypeError:
                progress_bar.progress(ratio)

        logger = logging.getLogger()
        previous_level = logger.level
        logger.setLevel(logging.INFO)
        ui_handler = StreamlitLogHandler()
        ui_handler.setLevel(logging.INFO)
        ui_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(ui_handler)

        result = {"rows": [], "processed_files": 0, "output_file": None}
        try:
            result = run_invoice_processing(
                open_excel_after=False,
                progress_callback=on_progress,
            )
        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            logger.removeHandler(ui_handler)
            logger.setLevel(previous_level)

        try:
            run_seconds = max(0.0, time.perf_counter() - run_started)
            rows = result.get("rows", [])
            if rows:
                st.session_state["impact_last_run"] = compute_batch_productivity_metrics(rows, run_seconds)
                record_productivity_from_run(rows, run_seconds)
            excel_path = result.get("output_file")
            st.session_state["last_rows"] = rows
            st.session_state["last_output_file"] = excel_path
            if rows and excel_path:
                processing_title.markdown(
                    '<div class="processing-line">Done. Your Excel file is ready! 🎉</div>',
                    unsafe_allow_html=True,
                )
                try:
                    os.startfile(str(output_dir))
                    st.toast("Processing finished - opened Output folder")
                except Exception:
                    pass
            else:
                st.warning("No output was generated. Please check your PDF files and try again.")
            st.session_state["last_log_lines"] = log_lines
        finally:
            st.session_state["invoice_run_queued"] = False
        st.rerun()

    last_rows = st.session_state.get("last_rows", [])
    last_output_file = st.session_state.get("last_output_file")
    if last_rows and last_output_file:
        try:
            with open(last_output_file, "rb") as f:
                result_col_download, result_col_new_batch = st.columns(2)
                with result_col_download:
                    st.download_button(
                        "Download Excel",
                        data=f.read(),
                        file_name=Path(last_output_file).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                with result_col_new_batch:
                    if st.button("Start New Batch", use_container_width=True):
                        removed_pdf_count = 0
                        for file_path in output_dir.glob("*.pdf"):
                            try:
                                file_path.unlink()
                                removed_pdf_count += 1
                            except Exception as e:
                                st.error(f"Couldn't remove file {file_path.name}: {e}")
                        st.session_state["last_rows"] = []
                        st.session_state["last_output_file"] = None
                        st.session_state["uploader_key"] += 1
                        st.caption(f"Ready for a new batch. Cleared {removed_pdf_count} PDF file(s) from output.")
                        try:
                            os.startfile(str(input_dir))
                            st.toast("New batch ready - opened Input folder")
                        except Exception:
                            pass
                        st.rerun()
        except Exception as e:
            st.warning(f"Unable to prepare the download: {e}")

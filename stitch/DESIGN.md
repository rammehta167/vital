---
name: Clinical Pulse Telemetry
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3e4a3d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#6e7b6c'
  outline-variant: '#bdcaba'
  surface-tint: '#006e2d'
  primary: '#006b2c'
  on-primary: '#ffffff'
  primary-container: '#00873a'
  on-primary-container: '#f7fff2'
  inverse-primary: '#62df7d'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#3f6700'
  on-tertiary: '#ffffff'
  tertiary-container: '#518200'
  on-tertiary-container: '#f9ffea'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#7ffc97'
  primary-fixed-dim: '#62df7d'
  on-primary-fixed: '#002109'
  on-primary-fixed-variant: '#005320'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#acf847'
  tertiary-fixed-dim: '#91db2a'
  on-tertiary-fixed: '#102000'
  on-tertiary-fixed-variant: '#304f00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  vital-metric-hero:
    fontFamily: JetBrains Mono
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 40px
  vital-metric-md:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 28px
  vital-metric-sm:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system blends ultra-clean modern SaaS precision with mission-critical healthcare telemetry. Inspired by contemporary high-finish fintech and automotive interfaces, it replaces clinical dreariness with razor-sharp layouts, airy off-white surfaces, crisp architectural lines, and dynamic vitality accents.

### Personality & Demographics
- **Target Audience:** Telemetry nurses, ICU intensivists, clinical coordinators, and medical ops engineers monitoring vital metrics in high-stress, high-throughput environments.
- **Brand Attributes:** Hyper-precise, calming, authoritative, and frictionless.
- **Emotional Response:** Inspires absolute confidence through instantaneous legibility, eliminating sensory overload while preserving high-contrast urgency cues.

### Aesthetic Direction
- **Style Blend:** Modernist Tech-Forward Minimalism with Functional Skeuomorphic Undercurrents.
- **Key Characteristics:** 
  - Dual-mode card interplay: light, airy canvas (#F8F9FA) paired with high-impact deep slate (#0F172A) telemetry pods.
  - Micro-fine hairline borders (1px) replacing murky drop shadows.
  - Bio-luminescent status accents (mint, emerald, lime) providing glanceable physiological feedback.

## Colors

The color palette is engineered for rapid perceptual triage and optical ease during 12-hour monitoring shifts. It employs a light, breathable foundational canvas punctuated by deep slate contrast containers and vivid, high-saturation signal accents.

### Hierarchy & Role Allocation
- **Canvas & Surface:**
  - `bg-canvas`: `#F8F9FA` — Ultra-clean, cool off-white that minimizes ambient screen glare.
  - `bg-surface-elevated`: `#FFFFFF` — Pure white foreground card layer.
  - `bg-surface-contrast`: `#0F172A` — Deep slate telemetry viewport, providing maximum pop for live waveforms and dynamic readings.
- **Primary & Bio-Vitality:**
  - `primary-default`: `#16A34A` (Emerald Core) — Primary confirmation, regular heart rhythm indicator, and focused action states.
  - `primary-subtle`: `#DCFCE7` — Fresh mint background fill for resting metrics and verified status badges.
  - `tertiary-accent`: `#84CC16` (Electric Lime) — Secondary performance indicators, rate-of-change trendlines, and continuous telemetry waves.
- **Structural Lines & Borders:**
  - `border-subtle`: `#E2E8F0` — 1px hairline division for clean data grids.
  - `border-strong`: `#CBD5E1` — Active field and focused module containers.
- **Clinical Status Matrix:**
  - `status-normal`: `#22C55E` / `#DCFCE7` (Normal sinus rhythm / stable vitals).
  - `status-warning`: `#F59E0B` / `#FEF3C7` (Pre-hypertensive, borderline SpO2).
  - `status-critical`: `#EF4444` / `#FEE2E2` (Ventricular arrhythmias, desaturation events).
  - `status-inactive`: `#94A3B8` / `#F1F5F9` (Lead disconnected / standby sensor).

## Typography

The typographic hierarchy implements a high-clarity dual-engine strategy: **Plus Jakarta Sans** delivers a clean, open, approachable geometric aesthetic for narrative metadata and structure, while **JetBrains Mono** enforces zero-drift tabular scanning for critical real-time physiological metrics (BPM, SpO2, MAP, NIBP).

### Role Guidelines
- **Structural Text:** Plus Jakarta Sans is applied to layout headers, clinical notes, patient identities, and global navigation. Tight letter spacing (-0.015em) on headline sizes keeps text dense, modern, and architectural.
- **Telemetry Readouts:** All streaming telemetry units, sensor metrics, and timeline stamps exclusively utilize JetBrains Mono with explicit tabular numerals (`tnum`). This eliminates horizontal jitter when numerical values fluctuate continuously.
- **Labels & Micro-data:** Micro-labels utilize `label-caps` in uppercase JetBrains Mono with +0.05em tracking for rapid scanning in low-light ICU environments.

## Layout & Spacing

The layout model utilizes a fluid 12-column architectural grid engineered for dense, multi-pane clinical monitoring workstations while scaling down gracefully to portable tablets.

### Responsive Breakpoints
- **Desktop Station (1440px+):** 12-column grid, `margin-desktop: 2.5rem`, `gutter-desktop: 1.5rem`. Accommodates continuous waveform streams, patient parameter columns, and live alert sidebars concurrently.
- **Tablet Bedside (768px – 1439px):** 8-column layout, `gutter: 1.25rem`, `margin: 1.5rem`. Waveforms fold into unified tabbed charts; patient vitals condense into modular cards.
- **Mobile Telemetry Handheld (<768px):** 4-column layout, `margin: 1rem`, `gutter: 0.75rem`. Critical values stack into full-width priority cards with drawer-based event logs.

### Rhythm & Alignment
Spacing follows a strict 4px base rhythm. Outer margins create a clean framing buffer around telemetry monitors, while internal component paddings remain compact (`space-sm` to `space-md`) to maximize information density without causing visual crowding.

## Elevation & Depth

To avoid murky, heavy shadows that obscure delicate waveform graphics, this design system establishes visual hierarchy through **Tonal Layering** and **Hairline Outlines**, accented by subtle chromatic glows for critical alerts.

### Elevation Tiers
- **Tier 0 (Base Canvas):** `#F8F9FA` — Flat foundational background.
- **Tier 1 (Metric Surfaces):** Pure white `#FFFFFF` wrapped with a 1px solid border (`#E2E8F0`). Flat elevation with zero drop shadow under normal status.
- **Tier 2 (Telemetry & Oscilloscope Pods):** Deep Slate `#0F172A` floating against the off-white canvas, framed with a 1px border (`#1E293B`).
- **Tier 3 (Floating Controls & Popovers):** Solid `#FFFFFF` or `#0F172A` with an ambient shadow: `0 8px 24px -4px rgba(15, 23, 42, 0.08)` and crisp border boundary.
- **Critical Alert Glow:** High-priority cards replace standard outlines with an inner and outer micro-tinted stroke: `box-shadow: 0 0 0 1px #EF4444, 0 4px 16px -2px rgba(239, 68, 68, 0.25)`.

## Shapes

The shape system employs crisp, controlled rounded corners (Level 2) that reinforce modern SaaS sophistication while maintaining architectural discipline.

### Geometry Rules
- **Base Surfaces & Cards:** Standard `rounded-md` (0.5rem / 8px) for modular metric boxes, retaining structural geometry.
- **Primary Viewport Modules:** `rounded-lg` (1rem / 16px) for master telemetry waveform containers and overarching modal panels.
- **Pill Badges & Tags:** Full rounded capsule (`rounded-full` / 9999px) for telemetry status, patient cohort markers, and battery/network indicators.
- **Action Elements:** Buttons and interactive form elements share the default `rounded-md` (8px) radius to maintain crisp tactile ergonomics.

## Components

### Buttons
- **Primary:** High-contrast solid dark slate (`#0F172A`) with crisp white text, or clinical emerald (`#16A34A`) for critical confirm actions. Padding: 10px 18px, `rounded-md`, 14px semi-bold.
- **Secondary / Ghost:** Transparent background with 1px hairline border (`#E2E8F0`), hover state fills to `#F1F5F9`.
- **Destructive / Emergency:** Solid `#EF4444` with white text, or subtle light red `#FEE2E2` with `#DC2626` text.

### Telemetry Badges & Chips
- **Status Pills:** Capsule-shaped (`rounded-full`) with 4px 10px padding. Composed of a 6px pulsating status dot paired with `JetBrains Mono` 11px uppercase label text.
  - *Stable:* `#DCFCE7` background, `#16A34A` text and dot.
  - *Warning:* `#FEF3C7` background, `#D97706` text and dot.
  - *Critical:* `#FEE2E2` background, `#DC2626` text and dot with an active 1.5s CSS pulse ring.

### Metric Cards & Data Containers
- **Standard Vitals Pod:** White background, 1px `#E2E8F0` border, `rounded-md`, padding: `space-md` (16px). Houses the metric label in `label-caps` slate, numerical readout in `vital-metric-hero`, and unit label in muted gray.
- **Dark Waveform Card:** Deep Slate `#0F172A` background, border 1px `#1E293B`, `rounded-lg`. Displays real-time SVG ECG/SpO2 waves drawn in vibrant lime (`#84CC16`) or electric cyan with faint 24px micro-grid lines (`rgba(255, 255, 255, 0.05)`).

### Input Fields & Controls
- **Inputs:** Minimalist white containers with `#E2E8F0` borders and inset padding. Focus ring: 2px solid `#16A34A` with zero diffuse blur. Placeholder text styled in neutral `#94A3B8`.
- **Toggle Switches & Checkboxes:** 16px squares with 4px corner radius; toggle tracks use clean off-white with emerald active fill and smooth 150ms spring transitions.

### Data Tables & Grid Lists
- **Structure:** Zero outer card padding; rows separated by 1px `#E2E8F0` dividers.
- **Header:** Sticky top header with light off-white background (`#F8F9FA`), `label-caps` in `#64748B`.
- **Row Interaction:** Hover state activates a subtle `#F1F5F9` tint with cursor pointer. Monospaced numeric columns right-aligned for instant vertical comparison.
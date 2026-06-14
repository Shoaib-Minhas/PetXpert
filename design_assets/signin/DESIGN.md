---
name: Clinical Heart
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf8'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e2e1ed'
  on-surface: '#191b23'
  on-surface-variant: '#434654'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c5d7'
  surface-tint: '#1353d8'
  primary: '#003fb1'
  on-primary: '#ffffff'
  primary-container: '#1a56db'
  on-primary-container: '#d4dcff'
  inverse-primary: '#b5c4ff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#852b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#ad3b00'
  on-tertiary-container: '#ffd4c5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b5c4ff'
  on-primary-fixed: '#00174d'
  on-primary-fixed-variant: '#003dab'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#ffdbcf'
  tertiary-fixed-dim: '#ffb59a'
  on-tertiary-fixed: '#380d00'
  on-tertiary-fixed-variant: '#802a00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e2e1ed'
  warm-accent: '#F59E0B'
  emergency-red: '#E11D48'
  moderate-orange: '#EA580C'
  low-risk-green: '#16A34A'
  neutral-surface: '#F8FAFC'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

The design system is anchored in the concept of **"Clinical Heart"**—a philosophy that balances the sterile precision of medical technology with the empathetic warmth of pet ownership. The target audience includes both anxious pet owners seeking immediate answers and veterinarians requiring a robust, data-dense workspace.

The design style is **Corporate / Modern** with a **Tactile** edge. It utilizes generous whitespace and a systematic grid to ensure medical data remains the focus, while employing soft-touch UI elements to reduce user anxiety. The interface feels like a high-end medical instrument that is simultaneously approachable and welcoming.

**Key Principles:**
- **Clarity over Decoration:** Every visual element must serve a functional purpose in the diagnostic journey.
- **Calmness through Consistency:** Predictable navigation and status indicators to soothe users during pet health emergencies.
- **Hybrid Density:** High-information density for veterinary dashboards, contrasted with focused, step-by-step flows for consumer-facing AI diagnostics.

## Colors

The palette is led by **Veterinary Blue**, a deep, reliable primary color that signals authority and medical standards. This is complemented by **Care Teal**, used for interactive elements and supportive actions to inject a sense of healing and growth.

**Semantic Severity Scale:**
This system uses a strict 4-tier color logic for pet health status:
- **Emergency (Red):** Immediate action required. Used for critical AI findings and urgent vet alerts.
- **High Risk (Orange):** Serious findings requiring a consultation within 24 hours.
- **Moderate (Yellow/Gold):** Non-urgent but requires monitoring or lifestyle adjustments.
- **Low Risk (Green):** Healthy results or routine home care recommendations.

**Neutral Palette:**
We utilize a cool-gray scale (Slate/Zinc) to maintain a clinical feel. Backgrounds should use a very light tint of blue-gray to reduce eye strain during long-form medical record reviews.

## Typography

Typography is built for **legibility under stress**. We use a dual-font strategy:
1. **Hanken Grotesk** for headlines: Its sharp, contemporary geometry provides a professional, "tech-forward" feel for the AI aspects of the brand.
2. **Inter** for body and data: Chosen for its exceptional legibility in medical charts, tabular data, and diagnostic reports.

**Usage Rules:**
- **Diagnostic Results:** Use `body-lg` for AI-generated medical summaries to ensure clear reading on mobile.
- **Technical Logs:** Use `code-sm` for audit trails and API-driven medical history timestamps to distinguish system-generated data from clinician notes.
- **Mobile scaling:** Headline sizes must drop by 20-25% on mobile to maintain vertical rhythm without overwhelming the pet owner's viewport.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for desktop and a **single-column stack** for mobile. We follow a strict 4px/8px rhythm to maintain technical precision.

**Layout Models:**
- **The Diagnostic View:** A focused, 800px max-width central container for AI analysis and chat, ensuring high focus.
- **The Vet Dashboard:** A full-width layout with a collapsible left sidebar (240px) for navigation and a right-side "Utility Pane" for quick-viewing medical documents.

**Responsive Adjustments:**
- **Mobile:** Horizontal margins are locked at 16px. Touch targets must be at least 44x44px.
- **Desktop:** Card-based layouts should use a 24px gutter to provide "visual air," preventing the medical data from feeling cluttered or overwhelming.

## Elevation & Depth

This design system avoids heavy shadows in favor of **Tonal Layers** and **Soft Ambient Depth**. 

- **Surface Levels:** The base background is `neutral-surface`. Content sits on pure white cards. This creates a natural "stacked" hierarchy without needing aggressive shadows.
- **Elevated States:** Only use soft, large-radius shadows (Blur: 16px, Y: 4px, Color: Primary with 8% opacity) for floating elements like diagnostic modals or real-time notifications.
- **Interaction Depth:** Buttons and interactive cards should use a subtle 1px border (`Slate-200`) in their resting state, which deepens to a soft shadow on hover to provide tactile feedback.
- **Glassmorphism:** Use sparingly for fixed navigation bars (Backdrop blur: 12px) to maintain context of the scroll position without obscuring medical data.

## Shapes

The shape language is **Rounded (12px - 16px)**. This specific radius is used to soften the "clinical" nature of the data, making the platform feel like a friendly companion rather than a cold medical database.

- **Standard Elements (Cards, Modals):** Use `rounded-lg` (16px) for main containers.
- **Form Inputs & Buttons:** Use `rounded-md` (8px) to maintain a slightly more structured, functional appearance for interactive controls.
- **Pet Avatars:** Always use circular masks to provide a warm, organic contrast to the rectangular grid of medical data.
- **Severity Badges:** Use "Pill-shaped" (full round) tags to distinguish them from clickable buttons.

## Components

**Buttons:**
- **Primary:** Filled `primary_color` with white text. High-contrast for the main CTA (e.g., "Start Diagnosis").
- **Secondary:** Outlined with `primary_color`. Used for "Add Photo" or "Download PDF".
- **Severity Action:** Red-filled buttons are reserved strictly for "Call Emergency Vet".

**Cards:**
- **Medical History Card:** White background, 1px border, 16px padding. Includes a top-right semantic badge for the visit's severity.
- **Pet Profile Card:** Features a large circular image, pet name in `headline-md`, and a quick-status indicator (e.g., "Up to date on vaccines").

**Input Fields:**
- **Medical Data Entry:** Labels must be in `label-md` directly above the field. Use 12px internal padding and a subtle focus ring in `secondary_color`.

**AI Confidence Meter:**
- A custom component representing "AI Confidence Score." Use a horizontal progress bar that shifts color based on the severity scale, accompanied by a tooltip explaining the "Fusion Layer" (how the AI combined image and text data).

**Status Badges:**
- Use the semantic scale for badges. Text should be all-caps in `label-sm` with high-contrast background tints (e.g., Light Red background with Dark Red text for "High Risk").
# SF Pro Typography System - UI/UX Design Guide

## Font Family Strategy

### SF Pro Display
**Use for:** Headlines, hero text, large display content (≥20px)
- Optimized for sizes 20px and above
- Better for visual impact and brand presence
- Clean, modern aesthetic for marketing content

### SF Pro Text  
**Use for:** Body copy, UI elements, readable content (<20px)
- Optimized for sizes below 20px  
- Better readability at small sizes
- Interface elements, forms, buttons, navigation

---

## Font Weight Hierarchy

### 🎯 Applied Strategy

#### **100 - Ultralight**
- Large hero titles when extreme elegance is needed
- Rarely used, only for very large (72px+) display text

#### **200 - Thin**
- Hero headlines for lightness and sophistication
- Large section headers (48px+)
- **Examples:** Hero main title, landing page headlines

#### **300 - Light**
- Secondary hero text
- Section headings
- Elegant subheadings (32-48px)
- **Examples:** `.card-5` (hero display text), large titles

#### **400 - Regular** ✅ DEFAULT
- Body text (primary content)
- Paragraphs, descriptions
- Standard UI elements
- Form inputs, labels
- Navigation items
- **Examples:** `.text-5`, `.footer-4`, most text content

#### **500 - Medium**
- Emphasized body text
- Subheadings (16-24px)
- Important UI elements
- Primary button text
- Card titles
- **Examples:** `.nav-6 span` (primary CTA buttons), `.title-5`

#### **600 - Semibold**
- Strong emphasis
- Section headers (20-32px)
- Important headings
- Secondary buttons
- **Examples:** `.header-4` (form headings), strong emphasis text

#### **700 - Bold**
- Maximum emphasis
- Call-to-action buttons
- Critical information
- Strong headings
- **Examples:** `.animation-5 span` (cursor indicators), `.feature-5`

#### **800 - Heavy**
- Rarely used
- Ultra-strong brand statements
- Maximum impact headlines

#### **900 - Black**
- Extremely rare
- Brand-specific ultra-bold needs only

---

## Current Implementation

### Headers & Display Text
```css
/* Large hero display - Light for elegance */
.card-5 { 
  font-family: "SF Pro Display"; 
  font-weight: 300;
  font-size: min(7.8rem, 8vw);
}

/* Hero section titles - Light */
.background-6 p { 
  font-family: "SF Pro Text";
  font-weight: 300;
  font-size: 5rem;
}

/* Section headings - Regular */
.image-7 { 
  font-family: "SF Pro Text";
  font-weight: 400;
  font-size: 3.625rem;
}
```

### Body & Content Text
```css
/* Body paragraphs - Regular */
h5, h6, p { 
  font-weight: 400;
}

/* Emphasized text - Semibold */
p > strong { 
  font-weight: 600;
}

/* Secondary text - Regular */
.text-secondary {
  font-weight: 400;
}
```

### UI Elements
```css
/* Regular buttons - Regular */
.list-5, .header-0, .hero-7 {
  font-weight: 400;
}

/* Primary CTA buttons - Medium */
.nav-6 span, .item-5 {
  font-weight: 500;
}

/* Form headings - Semibold */
.header-4 {
  font-weight: 600;
}

/* Small UI text - Medium */
.title-5, .image-5 {
  font-weight: 500;
}
```

### Navigation
```css
/* Nav items - Regular */
.subtitle-3, .button-4 {
  font-weight: 400;
}

/* Mobile menu links - Regular */
.subtitle-6 > a {
  font-weight: 400;
}
```

---

## Design Principles

### Readability
- **Body text:** Always 400 (Regular)
- **Paragraphs:** 400-500 max
- **Small text (<14px):** Never lighter than 400

### Hierarchy
1. **Hero/Display:** 200-300 (Thin/Light)
2. **Headers:** 400-600 (Regular to Semibold)
3. **Body:** 400 (Regular)
4. **Emphasis:** 500-600 (Medium/Semibold)
5. **CTA/Important:** 600-700 (Semibold/Bold)

### Contrast
- Use weight differences for visual hierarchy
- Minimum 200 weight difference for clear distinction
- Don't mix too many weights on one page (3-4 max)

---

## Size + Weight Guidelines

| Size Range | Recommended Weights | Use Case |
|------------|-------------------|----------|
| 72px+ | 100-300 | Hero displays |
| 48-72px | 200-400 | Large headers |
| 32-48px | 300-500 | Section headers |
| 20-32px | 400-600 | Subheadings |
| 16-20px | 400-500 | Body, UI elements |
| 12-16px | 400-500 | Small text, labels |
| <12px | 500-600 | Tiny text (needs weight for legibility) |

---

## Accessibility Notes

- Never use weight < 300 for text smaller than 24px
- Maintain WCAG contrast ratios with all weights
- Heavier weights improve readability for small text
- Lighter weights work only on large, high-contrast displays

---

## Implementation Status

✅ **Completed:**
- All @font-face declarations (SF Pro Display + Text)
- CSS variables updated to SF Pro
- Font family assignments across all elements
- Weight optimization for primary elements

🎯 **Optimized Elements:**
- Hero text: Light (300) for elegance
- Body text: Regular (400) for readability
- Buttons: Medium (500) for CTAs
- Headers: Regular to Semibold (400-600)
- Emphasis: Semibold (600)

---

## Browser Support

SF Pro fonts loaded via @font-face with:
- `.otf` format for maximum compatibility
- `font-display: swap` for performance
- Full weight range (100-900)
- Italic variants for all weights

Perfect rendering on:
- Safari (native Apple font)
- Chrome/Edge (via @font-face)
- Firefox (via @font-face)
- Mobile browsers (iOS/Android)


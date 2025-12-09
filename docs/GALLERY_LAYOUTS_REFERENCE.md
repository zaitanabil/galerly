# Gallery Layouts Quick Reference

## Available Layouts

### Grid Layouts (2)

#### grid_classic
- **Slots:** 12 (4x3 grid)
- **Aspect Ratio:** All 1:1 (square)
- **Use Case:** Classic portfolio, consistent presentation
- **Mobile-Friendly:** Yes

#### grid_portfolio
- **Slots:** 9 (3x3 grid)
- **Aspect Ratio:** All 1:1 (square)
- **Use Case:** Professional portfolio showcase
- **Mobile-Friendly:** Yes

---

### Masonry Layouts (2)

#### masonry_mixed
- **Slots:** 10
- **Aspect Ratios:** Mixed (2:3 portrait, 3:2 landscape, 1:1 square)
- **Features:** Large hero portrait, diverse arrangements
- **Use Case:** Editorial, dynamic galleries
- **Mobile-Friendly:** Yes

#### masonry_wedding
- **Slots:** 8
- **Aspect Ratios:** Mixed (3:2 hero, 3:2 landscape, 1:1 square, 2:3 portrait)
- **Features:** Large hero image spanning 2 columns
- **Use Case:** Wedding photography, special events
- **Mobile-Friendly:** Yes

---

### Panoramic Layouts (2)

#### panoramic_hero
- **Slots:** 7
- **Aspect Ratios:** 21:9 hero, 3:2 supporting, 1:1 accents
- **Features:** Ultra-wide hero image
- **Use Case:** Landscape photography, architectural
- **Mobile-Friendly:** Moderate

#### panoramic_landscape
- **Slots:** 6
- **Aspect Ratios:** 16:9 panoramas, 3:2 supporting
- **Features:** Three full-width panoramic rows
- **Use Case:** Landscape series, travel photography
- **Mobile-Friendly:** Good

---

### Collage Layouts (2)

#### collage_creative
- **Slots:** 9
- **Aspect Ratios:** Mixed with absolute positioning
- **Features:** Overlapping photos, z-index layering, creative arrangement
- **Use Case:** Artistic presentations, mood boards
- **Mobile-Friendly:** Limited (best on desktop)
- **Positioning:** Absolute (x, y coordinates)

#### collage_magazine
- **Slots:** 7
- **Aspect Ratios:** Mixed editorial style
- **Features:** Magazine spread layout, layered composition
- **Use Case:** Editorial, fashion, storytelling
- **Mobile-Friendly:** Limited (best on desktop)
- **Positioning:** Absolute (x, y coordinates)

---

### Story Layouts (3)

#### story_vertical
- **Slots:** 6
- **Aspect Ratios:** All 9:16 (vertical)
- **Features:** Vertical scrolling, full-screen mobile experience
- **Use Case:** Social media stories, vertical video
- **Mobile-Friendly:** Excellent
- **Scroll:** Vertical

#### story_feed
- **Slots:** 8
- **Aspect Ratios:** All 1:1 (square)
- **Features:** Social media feed style, caption space
- **Use Case:** Instagram-style presentation
- **Mobile-Friendly:** Excellent
- **Scroll:** Vertical

#### story_carousel
- **Slots:** 10
- **Aspect Ratios:** All 4:5 (mobile portrait)
- **Features:** Horizontal scrolling carousel
- **Use Case:** Mobile-optimized browsing, quick viewing
- **Mobile-Friendly:** Excellent
- **Scroll:** Horizontal

---

## Layout Selection Guide

### By Photo Count

| Photos | Recommended Layouts |
|--------|-------------------|
| 6      | story_vertical, panoramic_landscape |
| 7      | panoramic_hero, collage_magazine |
| 8      | masonry_wedding, story_feed |
| 9      | grid_portfolio, collage_creative |
| 10     | masonry_mixed, story_carousel |
| 12     | grid_classic |

### By Photography Type

| Type | Recommended Layouts |
|------|-------------------|
| Wedding | masonry_wedding, grid_portfolio, panoramic_hero |
| Portrait | grid_classic, masonry_mixed, story_vertical |
| Landscape | panoramic_hero, panoramic_landscape |
| Architecture | panoramic_landscape, grid_classic |
| Fashion | collage_magazine, masonry_mixed |
| Events | grid_classic, story_feed |
| Social Media | story_vertical, story_feed, story_carousel |
| Editorial | collage_magazine, masonry_mixed |
| Product | grid_portfolio, grid_classic |
| Travel | panoramic_landscape, masonry_mixed |

### By Device Optimization

| Device Priority | Layouts |
|----------------|---------|
| Mobile-First | story_vertical, story_feed, story_carousel, grid_classic, grid_portfolio |
| Desktop-Optimized | collage_creative, collage_magazine, panoramic_hero |
| Responsive | masonry_mixed, masonry_wedding, panoramic_landscape |

---

## Technical Specifications

### Aspect Ratios Used

| Ratio | Description | Used In |
|-------|-------------|---------|
| 1:1 | Square | All grid layouts, story_feed |
| 2:3 | Portrait | masonry_mixed, masonry_wedding, collage layouts |
| 3:2 | Landscape | masonry_wedding, panoramic_hero, collage layouts |
| 4:5 | Mobile Portrait | story_carousel |
| 9:16 | Vertical Story | story_vertical |
| 16:9 | Widescreen | panoramic_landscape |
| 21:9 | Cinematic | panoramic_hero |

### Positioning Types

| Type | Layouts | Rendering |
|------|---------|-----------|
| Grid | grid_*, masonry_*, panoramic_landscape | Row/column based |
| Absolute | collage_* | X/Y coordinates with z-index |
| Scroll | story_* | Vertical or horizontal scrolling |

---

## Usage Examples

### Create Gallery with Layout

```typescript
// Select masonry wedding layout
const gallery = await createGallery({
  name: "Sarah & Mike's Wedding",
  clientName: "Sarah Johnson",
  layout_id: "masonry_wedding",
  clientEmails: ["sarah@example.com"]
});

// Upload exactly 8 photos for this layout
```

### Change Layout

```typescript
// Switch from grid to panoramic
await updateGallery(galleryId, {
  layout_id: "panoramic_hero"
});

// Must have exactly 7 photos for panoramic_hero
```

### Fetch Layout for Rendering

```typescript
const layout = await fetch(`/v1/gallery-layouts/masonry_mixed`);
const layoutData = await layout.json();

// Render with GalleryLayoutRenderer
<GalleryLayoutRenderer 
  layout={layoutData}
  photos={photos}
/>
```

---

## Best Practices

1. **Photo Count Matching**
   - Always upload exactly the number of photos specified by the layout
   - Use `validate_layout_photos()` to check compatibility

2. **Aspect Ratio Preparation**
   - Review layout slot aspect ratios before shooting/selection
   - Crop photos to match slot requirements for best results

3. **Layout Selection Timing**
   - Choose layout before uploading photos
   - Consider final photo count when selecting layout

4. **Mobile Consideration**
   - Use story layouts for mobile-heavy audiences
   - Avoid collage layouts for primarily mobile viewers

5. **Performance**
   - Layouts with fewer slots load faster
   - Horizontal scroll layouts may impact mobile performance

---

## Default Behavior

- **Default Layout:** `grid_classic` (12 slots)
- **No Layout Specified:** Defaults to grid_classic
- **Invalid Layout ID:** Returns error on update
- **Photo Mismatch:** Validation prevents assignment

---

## API Quick Reference

```bash
# List all layouts
GET /v1/gallery-layouts

# Filter by category
GET /v1/gallery-layouts?category=masonry

# Get specific layout
GET /v1/gallery-layouts/masonry_wedding

# Create gallery with layout
POST /v1/galleries
{
  "name": "My Gallery",
  "layout_id": "masonry_wedding"
}

# Update gallery layout
PUT /v1/galleries/{id}
{
  "layout_id": "panoramic_hero"
}
```

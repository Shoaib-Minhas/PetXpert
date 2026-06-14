# Template Structure Documentation

## Overview
This document defines the template folder structure and naming conventions for the PetXpert project. Following these conventions ensures consistency, scalability, and maintainability.

## Folder Structure

```
templates/
├── layouts/          # Base templates and shared layouts
├── auth/             # Authentication-related templates
├── home/             # Landing page and public-facing pages
├── pets/             # Pet owner features
├── veterinarians/    # Veterinarian-related features
└── [future_modules]/ # Additional modules as needed
```

## Current Templates

### layouts/
- `base.html` - Main layout template with navigation, sidebar, and common structure

### auth/
- `signin.html` - User sign-in page
- `signup.html` - User sign-up page

### home/
- `index.html` - Landing page

### pets/
- `my_pets.html` - Pet management dashboard

### veterinarians/
- `list.html` - Veterinarian listing page
- `profile_complete.html` - Veterinarian profile completion form

## Naming Conventions

### Folder Names
- **Use lowercase, plural names** matching Django app names
- Examples: `pets/`, `veterinarians/`, `appointments/`, `accounts/`
- Avoid abbreviations unless widely understood

### File Names
- **Use lowercase with underscores** for multi-word names
- **Use descriptive names** that indicate the template's purpose
- **Use action-based names** for forms: `form_create.html`, `form_edit.html`
- **Use list/detail pattern** for CRUD operations:
  - `list.html` - List view of items
  - `detail.html` - Single item detail view
  - `create.html` - Create new item form
  - `edit.html` - Edit existing item form
  - `delete.html` - Delete confirmation

### Template References
- Always use the full path from the templates directory
- Example: `{% extends "layouts/base.html" %}`
- Example: `return render(request, 'pets/my_pets.html')`

## Module-Based Organization

Templates should be organized by Django app/module:

```
templates/
├── layouts/              # Shared layouts
├── accounts/             # User accounts, profiles
├── appointments/         # Appointment booking, management
├── pets/                 # Pet profiles, health records
├── veterinarians/        # Veterinarian profiles, services
├── consultations/        # Consultation features
├── reviews/              # Review system
└── payments/             # Payment processing
```

## Reusable Components

When creating reusable components, use the `partials/` folder:

```
templates/
├── layouts/
├── partials/
│   ├── navbar.html
│   ├── sidebar.html
│   ├── footer.html
│   ├── pet_card.html
│   └── vet_card.html
└── [modules]/
```

Include partials using:
```django
{% include "partials/navbar.html" %}
```

## Template Inheritance

1. **Base Template** (`layouts/base.html`) - Contains common structure
2. **Module Layouts** (optional) - Module-specific layouts extending base
3. **Page Templates** - Specific pages extending module layouts or base

Example:
```django
{# layouts/base.html #}
<!DOCTYPE html>
<html>
<head>{% block head %}{% endblock %}</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>

{# pets/my_pets.html #}
{% extends "layouts/base.html" %}
{% block content %}
    {# Pet-specific content #}
{% endblock %}
```

## Best Practices

1. **Keep templates DRY** - Use `{% include %}` for repeated components
2. **Use template inheritance** - Extend base templates rather than duplicating code
3. **Descriptive block names** - Use clear names like `{% block page_content %}`
4. **Comment complex logic** - Add comments for template logic that isn't obvious
5. **Separate concerns** - Keep business logic in views, not templates
6. **Use template tags/filters** - Create custom tags for complex logic

## Future Module Template Structure

When adding new modules, follow this pattern:

```
templates/
└── [module_name]/
    ├── list.html              # List view
    ├── detail.html            # Detail view
    ├── create.html            # Create form
    ├── edit.html              # Edit form
    ├── delete.html            # Delete confirmation
    └── [feature].html         # Additional feature-specific templates
```

## Migration Guide

When reorganizing templates:
1. Create the new folder structure
2. Move templates to appropriate folders
3. Update template references in:
   - `config/urls.py` (or app-specific `urls.py`)
   - View functions' `render()` calls
   - Template `{% extends %}` statements
   - Template `{% include %}` statements
4. Test all pages to ensure no broken references

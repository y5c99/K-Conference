"""Validators for uploaded files."""

import os
from django.core.exceptions import ValidationError


# Limit to 25 MB
MAX_UPLOAD_SIZE_MB = 25
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Allowed manuscript file types
ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx']


def validate_manuscript_file(uploaded_file):
    """Reject files that are too big or the wrong type."""
    # Size check
    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f'File is too large. Maximum size is {MAX_UPLOAD_SIZE_MB} MB.'
        )

    # Extension check
    name = uploaded_file.name.lower()
    ext = os.path.splitext(name)[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'Only PDF, DOC, or DOCX files are allowed. Got: {ext}'
        )
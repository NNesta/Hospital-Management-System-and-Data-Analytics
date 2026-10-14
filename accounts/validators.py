"""Validators for Rwandan identifiers, shared by every app."""

import re

from django.core.exceptions import ValidationError

# MTN (078, 079) and Airtel (072, 073) mobile numbers, with or without +250.
RWANDA_PHONE_RE = re.compile(r"^(?:\+?250|0)7[2389]\d{7}$")

# National ID: 16 digits, e.g. 1 1990 8 0012345 0 12 (citizen, birth year,
# 8 = male / 7 = female, sequence, issue count, check digits).
RWANDA_NID_RE = re.compile(r"^[1-3](19|20)\d{2}[78]\d{10}$")


def validate_rwanda_phone(value):
    digits = re.sub(r"[\s\-()]", "", value or "")
    if digits and not RWANDA_PHONE_RE.match(digits):
        raise ValidationError(
            "Enter a Rwandan mobile number, e.g. +250 788 123 456 or 0788 123 456.",
            code="invalid_phone",
        )


def validate_rwanda_national_id(value):
    digits = re.sub(r"\s", "", value or "")
    if digits and not RWANDA_NID_RE.match(digits):
        raise ValidationError(
            "Enter the 16-digit Rwandan national ID, e.g. 1199080012345012.",
            code="invalid_national_id",
        )

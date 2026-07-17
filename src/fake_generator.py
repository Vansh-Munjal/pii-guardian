from faker import Faker

fake = Faker("en_IN")   # Indian locale for realistic Indian names/addresses

# Cache ensures the same original PII always gets the same fake replacement
# throughout the entire document — critical for consistency.
_cache: dict[str, str] = {}


def _generate(pii_type: str) -> str:
    generators = {
        "PERSON":      lambda: fake.name(),
        "EMAIL":       lambda: fake.email(),
        "PHONE":       lambda: fake.phone_number(),
        "ORG":         lambda: fake.company(),
        "ADDRESS":     lambda: fake.address().replace("\n", ", "),
        "SSN":         lambda: f"{fake.random_int(100,999)}-{fake.random_int(10,99)}-{fake.random_int(1000,9999)}",
        "CREDIT_CARD": lambda: fake.credit_card_number(card_type=None),
        "DATE_OF_BIRTH": lambda: fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%d/%m/%Y"),
        "IP_ADDRESS":  lambda: fake.ipv4(),
    }
    generator = generators.get(pii_type)
    if generator is None:
        return "[REDACTED]"
    return generator()


def get_fake(original_text: str, pii_type: str) -> str:
    """
    Returns a fake value for the given original PII text.
    Repeated calls with the same original_text always return the same fake value,
    regardless of pii_type — ensuring document-wide consistency.
    """
    if original_text not in _cache:
        _cache[original_text] = _generate(pii_type)
    return _cache[original_text]


def reset_cache() -> None:
    """Clears the mapping. Call this between documents if processing in batch."""
    _cache.clear()

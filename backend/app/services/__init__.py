# Lazy imports to avoid circular dependency
# Import directly from modules when needed:
# from app.services.sar_generator import SARGeneratorService
# from app.services.audit_trail import AuditTrailService
# from app.services.fact_checker import FactCheckerService

__all__ = ["SARGeneratorService", "AuditTrailService", "FactCheckerService"]


def __getattr__(name):
    """Lazy import to avoid circular imports."""
    if name == "SARGeneratorService":
        from app.services.sar_generator import SARGeneratorService
        return SARGeneratorService
    elif name == "AuditTrailService":
        from app.services.audit_trail import AuditTrailService
        return AuditTrailService
    elif name == "FactCheckerService":
        from app.services.fact_checker import FactCheckerService
        return FactCheckerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

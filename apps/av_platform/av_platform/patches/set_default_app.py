from av_platform.shell import set_default_app


def execute():
    """Sites installed before ADR-004 also open AV Platform by default."""
    set_default_app()

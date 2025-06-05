# engine_logger.py
import log.logger

class EngineLogger:
    """Mixin class que fornece métodos de logging com indentação."""
    
    def log_info(self, message, indent=0):
        """Log info message with proper indentation."""
        prefix = "  " * indent
        self.logger.info(f"{prefix}{message}")

    def log_debug(self, message, indent=0):
        """Log debug message with proper indentation."""
        prefix = "  " * indent
        self.logger.debug(f"{prefix}{message}")

    def log_error(self, message, indent=0):
        """Log error message with proper indentation."""
        prefix = "  " * indent
        self.logger.error(f"{prefix}{message}")

    def log_warning(self, message, indent=0):
        """Log warning message with proper indentation."""
        prefix = "  " * indent
        self.logger.warning(f"{prefix}{message}")